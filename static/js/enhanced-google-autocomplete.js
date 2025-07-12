/**
 * Enhanced Google Places Autocomplete with Address Validation
 * Replaces manual address entry with single autocomplete field
 */

class EnhancedGoogleAutocomplete {
    constructor(inputId, options = {}) {
        this.inputId = inputId;
        this.options = {
            types: ['address'],
            componentRestrictions: { country: 'us' },
            fields: ['place_id', 'formatted_address', 'address_components', 'geometry'],
            ...options
        };
        
        this.autocomplete = null;
        this.selectedPlace = null;
        this.init();
    }

    init() {
        const input = document.getElementById(this.inputId);
        if (!input) {
            console.error(`Input element with id '${this.inputId}' not found`);
            return;
        }

        // Initialize autocomplete
        this.autocomplete = new google.maps.places.Autocomplete(input, this.options);
        
        // Listen for place selection
        this.autocomplete.addListener('place_changed', () => {
            this.handlePlaceSelection();
        });
    }

    handlePlaceSelection() {
        const place = this.autocomplete.getPlace();
        
        if (!place.place_id) {
            this.showError('Please select a valid address from the suggestions');
            return;
        }

        this.selectedPlace = place;
        
        // Validate address with Google's Address Validation API
        this.validateAddress(place)
            .then(validation => {
                if (validation.isValid) {
                    this.populateAddressFields(place, validation.canonicalData);
                    this.showSuccess('Address validated successfully');
                } else {
                    this.showError(validation.error || 'Address could not be validated. Please try a different address.');
                }
            })
            .catch(error => {
                console.error('Address validation error:', error);
                // Fallback to basic validation
                this.populateAddressFields(place);
            });
    }

    async validateAddress(place) {
        try {
            // Use official Google Places "Place Details (New)" API
            const response = await fetch('/api/places/details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    place_id: place.place_id
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Store canonical data for later use
                this.canonicalData = result.data;
                return { 
                    isValid: true, 
                    canonicalData: result.data 
                };
            } else {
                return { 
                    isValid: false, 
                    error: result.message || 'Address validation failed' 
                };
            }
        } catch (error) {
            console.error('Address validation API error:', error);
            return { isValid: false, error: 'Validation service unavailable' };
        }
    }

    populateAddressFields(place, canonicalData = null) {
        let addressData;
        
        if (canonicalData) {
            // Use canonical data from Google Places API
            const formatted = canonicalData.formattedAddress;
            const addressParts = this.parseFormattedAddress(formatted);
            
            addressData = {
                place_id: canonicalData.placeId,
                formatted_address: canonicalData.formattedAddress,
                street: addressParts.street,
                city: addressParts.city,
                state: addressParts.state,
                zip: addressParts.zip,
                lat: canonicalData.lat,
                lng: canonicalData.lng
            };
        } else {
            // Fallback to original place data
            const addressComponents = this.parseAddressComponents(place.address_components);
            addressData = {
                place_id: place.place_id,
                formatted_address: place.formatted_address,
                street: addressComponents.street,
                city: addressComponents.city,
                state: addressComponents.state,
                zip: addressComponents.zip,
                lat: place.geometry?.location?.lat(),
                lng: place.geometry?.location?.lng()
            };
        }
        
        // Populate hidden fields for backend processing
        this.setFieldValue('street-address', addressData.street);
        this.setFieldValue('city', addressData.city);
        this.setFieldValue('state', addressData.state);
        this.setFieldValue('zip-code', addressData.zip);
        this.setFieldValue('place-id', addressData.place_id);
        this.setFieldValue('formatted-address', addressData.formatted_address);
        
        // Also populate visible fields if they exist
        this.setFieldValue('address', addressData.street);
        this.setFieldValue('address-input', addressData.street);
        
        // Store for later use
        window.selectedAddressData = addressData;
        window.lastGoogleAutocompleteData = {
            placeId: addressData.place_id,
            formattedAddress: addressData.formatted_address,
            addressComponents: {
                street: addressData.street,
                city: addressData.city,
                state: addressData.state,
                zip: addressData.zip
            }
        };
    }

    parseAddressComponents(components) {
        const addressData = {
            street: '',
            city: '',
            state: '',
            zip: ''
        };

        components.forEach(component => {
            const types = component.types;
            
            if (types.includes('street_number')) {
                addressData.street = component.long_name + ' ';
            }
            if (types.includes('route')) {
                addressData.street += component.long_name;
            }
            if (types.includes('locality')) {
                addressData.city = component.long_name;
            }
            if (types.includes('administrative_area_level_1')) {
                addressData.state = component.short_name;
            }
            if (types.includes('postal_code')) {
                addressData.zip = component.long_name;
            }
        });

        return addressData;
    }

    parseFormattedAddress(formattedAddress) {
        /**
         * Parse Google's formatted address string like:
         * "14303 Evening Flight Lane, Charlotte, NC 28278, USA"
         */
        const parts = formattedAddress.split(', ');
        
        if (parts.length < 3) {
            // Fallback parsing for unusual formats
            return {
                street: formattedAddress,
                city: '',
                state: '',
                zip: ''
            };
        }
        
        // Extract components from formatted string
        const street = parts[0] || '';
        const city = parts[1] || '';
        const stateZip = parts[2] || '';
        
        // Parse state and ZIP from "NC 28278" format
        const stateZipMatch = stateZip.match(/^([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$/);
        const state = stateZipMatch ? stateZipMatch[1] : '';
        const zip = stateZipMatch ? stateZipMatch[2] : '';
        
        return {
            street,
            city,
            state,
            zip
        };
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value || '';
        }
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showToast(message, type = 'info') {
        // Remove existing toast
        const existingToast = document.getElementById('address-toast');
        if (existingToast) {
            existingToast.remove();
        }

        // Create new toast
        const toast = document.createElement('div');
        toast.id = 'address-toast';
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm ${
            type === 'error' ? 'bg-red-500 text-white' : 
            type === 'success' ? 'bg-green-500 text-white' : 
            'bg-blue-500 text-white'
        }`;
        // Create content safely using DOM methods to prevent XSS
        const contentDiv = document.createElement('div');
        contentDiv.className = 'flex items-center';
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'flex-1';
        messageSpan.textContent = message; // Use textContent instead of innerHTML
        
        const closeButton = document.createElement('button');
        closeButton.className = 'ml-2 text-white hover:text-gray-200';
        closeButton.textContent = '×';
        closeButton.onclick = function() {
            this.parentElement.parentElement.remove();
        };
        
        contentDiv.appendChild(messageSpan);
        contentDiv.appendChild(closeButton);
        toast.appendChild(contentDiv);

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize for main property analysis form
    if (document.getElementById('address-input')) {
        window.addressAutocomplete = new EnhancedGoogleAutocomplete('address-input');
    }
    
    // Initialize for JV form if present
    if (document.getElementById('jv-address-input')) {
        window.jvAddressAutocomplete = new EnhancedGoogleAutocomplete('jv-address-input');
    }
});