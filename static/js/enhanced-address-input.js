/**
 * Enhanced Address Input with 5-Layer Defense
 * Provides Google Places Autocomplete with fuzzy matching fallbacks
 */

class EnhancedAddressInput {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            onAddressSelected: options.onAddressSelected || (() => {}),
            onValidationComplete: options.onValidationComplete || (() => {}),
            showConfirmationBanner: options.showConfirmationBanner !== false,
            ...options
        };
        
        this.autocompleteService = null;
        this.placesService = null;
        this.selectedAddress = null;
        this.confirmationBanner = null;
        
        this.init();
    }
    
    init() {
        // Check if Google Maps API is loaded
        if (typeof google !== 'undefined' && google.maps && google.maps.places) {
            this.initializeGooglePlaces();
        } else {
            // Fallback to basic input with server-side validation
            this.initializeFallbackMode();
        }
        
        // Add input event listeners
        this.input.addEventListener('blur', this.handleInputBlur.bind(this));
        this.input.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
    
    initializeGooglePlaces() {
        console.log('Initializing Google Places Autocomplete');
        
        // Initialize autocomplete with address types only
        this.autocomplete = new google.maps.places.Autocomplete(this.input, {
            types: ['address'],
            componentRestrictions: { country: 'us' },
            fields: ['place_id', 'formatted_address', 'address_components', 'geometry']
        });
        
        // Listen for place selection
        this.autocomplete.addListener('place_changed', this.handlePlaceSelection.bind(this));
        
        // Initialize services for additional lookups
        this.autocompleteService = new google.maps.places.AutocompleteService();
        this.placesService = new google.maps.places.PlacesService(document.createElement('div'));
        
        // Prevent form submission on Enter key in autocomplete dropdown
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && document.querySelector('.pac-container:not([style*="display: none"])')) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }
    
    initializeFallbackMode() {
        console.log('Initializing fallback address input mode');
        this.input.setAttribute('data-address-fallback', 'true');
    }
    
    handlePlaceSelection() {
        const place = this.autocomplete.getPlace();
        
        if (!place || !place.place_id) {
            console.warn('No place selected or invalid place data');
            return;
        }
        
        // Parse address components using Google's canonical format
        const components = place.address_components;
        const getComponent = (type) => {
            const component = components.find(c => c.types.includes(type));
            return component ? component.long_name : '';
        };
        
        const getShortComponent = (type) => {
            const component = components.find(c => c.types.includes(type));
            return component ? component.short_name : '';
        };
        
        // Build canonical address parts
        const streetNumber = getComponent('street_number');
        const route = getComponent('route');
        const street = `${streetNumber} ${route}`.trim();
        const city = getComponent('locality') || getComponent('postal_town') || getComponent('sublocality');
        const state = getShortComponent('administrative_area_level_1'); // Use short name for state abbreviation
        const zip = getComponent('postal_code');
        
        this.selectedAddress = {
            placeId: place.place_id,
            formattedAddress: place.formatted_address,
            street: street,
            city: city,
            state: state,
            zip: zip,
            latitude: place.geometry?.location?.lat(),
            longitude: place.geometry?.location?.lng(),
            addressComponents: place.address_components,
            geometry: place.geometry,
            source: 'google_autocomplete'
        };
        
        console.log('Address selected via Google Autocomplete:', this.selectedAddress);
        
        // Store globally for form submission
        window.selectedAddressData = this.selectedAddress;
        
        // Also store in the format expected by form submission
        window.lastGoogleAutocompleteData = {
            placeId: this.selectedAddress.placeId,
            formattedAddress: this.selectedAddress.formattedAddress,
            addressComponents: {
                street: this.selectedAddress.street,
                city: this.selectedAddress.city,
                state: this.selectedAddress.state,
                zip: this.selectedAddress.zip
            }
        };
        
        // Auto-populate other form fields immediately
        this.autoPopulateFields();
        
        if (this.options.showConfirmationBanner) {
            this.showConfirmationBanner();
        } else {
            this.confirmAddress();
        }
    }
    
    autoPopulateFields() {
        // Auto-populate city, state, and zip fields if they exist
        const cityField = document.getElementById('city');
        const stateField = document.getElementById('state');
        const zipField = document.getElementById('zip');
        
        if (cityField && this.selectedAddress.city) {
            cityField.value = this.selectedAddress.city;
            // Trigger change event for any listeners
            cityField.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        if (stateField && this.selectedAddress.state) {
            stateField.value = this.selectedAddress.state;
            stateField.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        if (zipField && this.selectedAddress.zip) {
            zipField.value = this.selectedAddress.zip;
            zipField.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        console.log('Auto-populated fields:', {
            city: this.selectedAddress.city,
            state: this.selectedAddress.state,
            zip: this.selectedAddress.zip
        });
    }
    
    handleInputBlur() {
        // Only validate if user hasn't used Google Places autocomplete
        if (!this.selectedAddress && this.input.value.trim() && !this.input.getAttribute('data-validated')) {
            // Only validate if it looks like a complete address
            const addressValue = this.input.value.trim();
            if (addressValue.includes(',') || addressValue.split(' ').length >= 3) {
                console.log('Manual address entry detected, performing server-side validation');
                this.validateAddressServerSide();
            }
        }
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter' && this.input.value.trim()) {
            event.preventDefault();
            if (!this.selectedAddress) {
                this.validateAddressServerSide();
            } else {
                this.confirmAddress();
            }
        }
    }
    
    async validateAddressServerSide() {
        const address = this.input.value.trim();
        if (!address) return;
        
        try {
            // Show loading state
            this.setLoadingState(true);
            
            // Call server-side geocoding endpoint
            const response = await fetch('/api/validate-address', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    address: address,
                    source: 'manual_entry'
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.address) {
                this.selectedAddress = {
                    formattedAddress: result.address.formatted_address,
                    placeId: result.address.place_id,
                    source: 'server_geocoding',
                    confidence: result.address.confidence
                };
                
                // Update input with normalized address
                this.input.value = result.address.formatted_address;
                
                if (this.options.showConfirmationBanner) {
                    this.showConfirmationBanner();
                } else {
                    this.confirmAddress();
                }
            } else {
                this.showValidationError(result.error || 'Address could not be validated');
            }
        } catch (error) {
            console.error('Server-side address validation failed:', error);
            this.showValidationError('Address validation service unavailable');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    showConfirmationBanner() {
        if (this.confirmationBanner) {
            this.confirmationBanner.remove();
        }
        
        const banner = document.createElement('div');
        banner.className = 'address-confirmation-banner bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2';
        banner.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <i class="fas fa-map-marker-alt text-blue-600"></i>
                    <span class="text-sm text-gray-700">
                        We'll analyze: <strong>${this.selectedAddress.formattedAddress}</strong>. Correct?
                    </span>
                </div>
                <div class="flex space-x-2">
                    <button class="confirm-btn bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                        Yes
                    </button>
                    <button class="edit-btn bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-400">
                        Edit
                    </button>
                </div>
            </div>
        `;
        
        // Insert banner after input
        this.input.parentNode.insertBefore(banner, this.input.nextSibling);
        this.confirmationBanner = banner;
        
        // Add event listeners
        banner.querySelector('.confirm-btn').addEventListener('click', this.confirmAddress.bind(this));
        banner.querySelector('.edit-btn').addEventListener('click', this.editAddress.bind(this));
    }
    
    confirmAddress() {
        if (this.confirmationBanner) {
            this.confirmationBanner.remove();
            this.confirmationBanner = null;
        }
        
        console.log('Address confirmed:', this.selectedAddress);
        
        // Trigger callbacks
        this.options.onAddressSelected(this.selectedAddress);
        this.options.onValidationComplete({
            success: true,
            address: this.selectedAddress
        });
    }
    
    editAddress() {
        if (this.confirmationBanner) {
            this.confirmationBanner.remove();
            this.confirmationBanner = null;
        }
        
        this.selectedAddress = null;
        this.input.focus();
        this.input.select();
    }
    
    setLoadingState(loading) {
        if (loading) {
            this.input.classList.add('loading');
            this.input.style.background = '#f3f4f6 url("data:image/svg+xml;base64,PHN2ZyBhbmltYXRpb249InNwaW4iIGZpbGw9Im5vbmUiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiIHN0cm9rZT0iI2Y5ZmFmYiIgc3Ryb2tlLXdpZHRoPSI0Ii8+CjxwYXRoIGQ9Im00IDEyYTggOCAwIDAgMSA4LTggVjBDNS4zNzMgMCAwIDUuMzczIDAgMTJoNCIgZmlsbD0iIzM3NDE1MSIvPgo8L3N2Zz4K") no-repeat right 8px center';
            this.input.style.backgroundSize = '16px 16px';
        } else {
            this.input.classList.remove('loading');
            this.input.style.background = '';
        }
    }
    
    showValidationError(message) {
        // Remove any existing error
        const existingError = this.input.parentNode.querySelector('.address-validation-error');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'address-validation-error bg-red-50 border border-red-200 rounded-lg p-2 mt-1';
        errorDiv.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-exclamation-triangle text-red-500"></i>
                <span class="text-sm text-red-700">${message}</span>
            </div>
        `;
        
        this.input.parentNode.insertBefore(errorDiv, this.input.nextSibling);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    // Public methods
    getSelectedAddress() {
        return this.selectedAddress;
    }
    
    reset() {
        this.selectedAddress = null;
        this.input.value = '';
        if (this.confirmationBanner) {
            this.confirmationBanner.remove();
            this.confirmationBanner = null;
        }
    }
    
    setValue(address) {
        this.input.value = address;
        this.selectedAddress = null;
    }
}

// Auto-initialize enhanced address inputs
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with data-enhanced-address attribute
    const addressInputs = document.querySelectorAll('[data-enhanced-address]');
    
    addressInputs.forEach(input => {
        new EnhancedAddressInput(input, {
            onAddressSelected: (address) => {
                console.log('Address selected:', address);
                // Trigger form submission or analysis
                const form = input.closest('form');
                if (form && input.dataset.autoSubmit === 'true') {
                    form.dispatchEvent(new Event('submit'));
                }
            },
            onValidationComplete: (result) => {
                console.log('Address validation complete:', result);
            }
        });
    });
});

// Export for use in other modules
window.EnhancedAddressInput = EnhancedAddressInput;