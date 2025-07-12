/**
 * Google Autocomplete (New) API Integration
 * Provides real-time address suggestions with automatic city/state/zip population
 */

class GoogleAutocompleteNew {
    constructor(inputElement, options = {}) {
        console.log('GoogleAutocompleteNew constructor called');
        this.input = inputElement;
        this.options = {
            onSelect: options.onSelect || (() => {}),
            onError: options.onError || (() => {}),
            ...options
        };
        
        // Generate unique session token for billing optimization
        this.sessionToken = this.generateSessionToken();
        this.suggestionsContainer = null;
        this.currentController = null;
        this.suggestions = [];
        this.apiNotEnabled = false;
        
        this.init();
    }
    
    init() {
        // Check if input element exists
        if (!this.input) {
            console.error('GoogleAutocompleteNew: Input element not found');
            return;
        }
        
        // Create suggestions dropdown container
        this.createSuggestionsContainer();
        
        // Bind event listeners
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('blur', this.handleBlur.bind(this));
        
        // Close suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }
    
    createSuggestionsContainer() {
        if (!this.input || !this.input.parentNode) {
            console.error('GoogleAutocompleteNew: Cannot create suggestions container - input or parent not found');
            return;
        }
        
        this.suggestionsContainer = document.createElement('div');
        this.suggestionsContainer.className = 'google-autocomplete-suggestions';
        this.suggestionsContainer.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            background: white;
            border: 1px solid #d1d5db;
            border-top: none;
            border-radius: 0 0 0.375rem 0.375rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            max-height: 200px;
            overflow-y: auto;
            display: none;
        `;
        
        // Insert after input element
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.suggestionsContainer);
    }
    
    generateSessionToken() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }
    
    async handleInput(e) {
        const query = e.target.value.trim();
        console.log('handleInput called with query:', query);
        
        if (!query) {
            this.hideSuggestions();
            return;
        }
        
        // Skip API calls if not enabled
        if (this.apiNotEnabled) {
            console.log('API not enabled, skipping autocomplete');
            return;
        }
        
        // Cancel previous request
        if (this.currentController) {
            this.currentController.abort();
        }
        
        // Create new AbortController for this request
        this.currentController = new AbortController();
        
        try {
            const response = await fetch('/api/autocomplete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input: query,
                    languageCode: 'en',
                    includeQueryPredictions: false,
                    sessionToken: this.sessionToken
                }),
                signal: this.currentController.signal
            });
            
            if (!response.ok) {
                throw new Error('Autocomplete request failed');
            }
            
            const data = await response.json();
            console.log('Autocomplete API response:', data);
            
            // Handle API not enabled case
            if (data.error === 'API_NOT_ENABLED') {
                this.handleAPINotEnabled();
                return;
            }
            
            this.suggestions = data.suggestions || [];
            console.log('Parsed suggestions:', this.suggestions);
            this.renderSuggestions();
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Autocomplete error:', error);
                console.error('Error details:', error.message);
                this.options.onError(error);
            }
        }
    }
    
    renderSuggestions() {
        if (!this.suggestions.length) {
            this.hideSuggestions();
            return;
        }
        
        this.suggestionsContainer.innerHTML = '';
        
        this.suggestions.forEach((suggestion, index) => {
            const prediction = suggestion.placePrediction;
            const item = document.createElement('div');
            item.className = 'google-autocomplete-item';
            item.style.cssText = `
                padding: 0.75rem 1rem;
                cursor: pointer;
                border-bottom: 1px solid #f3f4f6;
                transition: background-color 0.15s ease;
            `;
            
            item.innerHTML = `
                <div class="text-sm font-medium text-gray-900">${prediction.text.text}</div>
            `;
            
            // Hover effects
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f9fafb';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'white';
            });
            
            // Click handler
            item.addEventListener('click', () => {
                this.selectSuggestion(prediction);
            });
            
            this.suggestionsContainer.appendChild(item);
        });
        
        this.showSuggestions();
    }
    
    async selectSuggestion(prediction) {
        console.log('Selected prediction:', prediction);
        
        // Don't update the input value here - wait for place details
        // This prevents the incomplete address from being shown
        
        // Hide suggestions
        this.hideSuggestions();
        
        try {
            // Get place details using the same session token
            const response = await fetch('/api/place-details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    placeId: prediction.placeId,
                    sessionToken: this.sessionToken
                })
            });
            
            if (!response.ok) {
                throw new Error('Place details request failed');
            }
            
            const placeData = await response.json();
            console.log('Place details response:', placeData);
            
            // Handle API not enabled case
            if (placeData.error === 'API_NOT_ENABLED') {
                this.handleAPINotEnabled();
                return;
            }
            
            // Parse address components
            const addressComponents = this.parseAddressComponents(placeData.addressComponents || []);
            console.log('Parsed address components:', addressComponents);
            
            // Call the selection callback with parsed data
            this.options.onSelect({
                placeId: prediction.placeId,
                formattedAddress: placeData.formattedAddress,
                addressComponents: addressComponents,
                fullResponse: placeData
            });
            
            // Generate new session token for next search
            this.sessionToken = this.generateSessionToken();
            
        } catch (error) {
            console.error('Place details error:', error);
            this.options.onError(error);
        }
    }
    
    parseAddressComponents(components) {
        const parsed = {
            street_number: '',
            route: '',
            locality: '',
            administrative_area_level_1: '',
            postal_code: '',
            country: ''
        };
        
        components.forEach(component => {
            // Handle both old and new API formats
            const types = component.types || [];
            types.forEach(type => {
                if (parsed.hasOwnProperty(type)) {
                    // New API format uses longText/shortText, old uses long_name/short_name
                    parsed[type] = component.longText || component.shortText || 
                                   component.long_name || component.short_name || '';
                }
            });
        });
        
        // Log the parsed components for debugging
        console.log('Parsed address components:', parsed);
        
        return {
            street: `${parsed.street_number} ${parsed.route}`.trim(),
            city: parsed.locality,
            state: parsed.administrative_area_level_1,
            zip: parsed.postal_code,
            country: parsed.country
        };
    }
    
    handleKeydown(e) {
        // Handle keyboard navigation (optional enhancement)
        if (e.key === 'Escape') {
            this.hideSuggestions();
        }
    }
    
    handleBlur(e) {
        // Delay hiding to allow for click selection
        setTimeout(() => {
            this.hideSuggestions();
        }, 150);
    }
    
    showSuggestions() {
        this.suggestionsContainer.style.display = 'block';
    }
    
    hideSuggestions() {
        this.suggestionsContainer.style.display = 'none';
    }
    
    handleAPINotEnabled() {
        // Show informative message about API setup
        showToast('Google Places API (New) needs to be enabled in Google Cloud Console. Using basic validation fallback.', 'warning');
        
        // Hide suggestions container
        this.hideSuggestions();
        
        // Set flag to prevent further API calls
        this.apiNotEnabled = true;
        
        // Notify parent component that API is not enabled
        if (this.options.onAPINotEnabled) {
            this.options.onAPINotEnabled();
        }
    }
    
    destroy() {
        if (this.currentController) {
            this.currentController.abort();
        }
        
        if (this.suggestionsContainer && this.suggestionsContainer.parentNode) {
            this.suggestionsContainer.parentNode.removeChild(this.suggestionsContainer);
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const streetAddressInput = document.getElementById('address');
    const cityInput = document.getElementById('city');
    const stateInput = document.getElementById('state');
    const zipInput = document.getElementById('zip');
    
    if (streetAddressInput) {
        console.log('Initializing Google Autocomplete (New) on address input');
        const autocompleteInstance = new GoogleAutocompleteNew(streetAddressInput, {
            onSelect: function(data) {
                console.log('Address selected:', data);
                
                // Store selected address data globally for form submission
                window.selectedAddressData = data;
                
                // Update the main address input with the full formatted address
                if (data.formattedAddress) {
                    streetAddressInput.value = data.formattedAddress;
                    console.log('Updated address field with:', data.formattedAddress);
                }
                
                // Auto-populate city, state, and zip fields
                if (cityInput && data.addressComponents.city) {
                    cityInput.value = data.addressComponents.city;
                    console.log('Set city field to:', data.addressComponents.city);
                } else {
                    console.log('City field not populated:', { cityInput, city: data.addressComponents.city });
                }
                
                if (stateInput && data.addressComponents.state) {
                    stateInput.value = data.addressComponents.state;
                    console.log('Set state field to:', data.addressComponents.state);
                } else {
                    console.log('State field not populated:', { stateInput, state: data.addressComponents.state });
                }
                
                if (zipInput && data.addressComponents.zip) {
                    zipInput.value = data.addressComponents.zip;
                    console.log('Set zip field to:', data.addressComponents.zip);
                } else {
                    console.log('Zip field not populated:', { zipInput, zip: data.addressComponents.zip });
                }
                
                // Log the complete address data
                console.log('Complete address data stored:', window.selectedAddressData);
                
                // Show success toast
                showToast('Address selected successfully!', 'success');
            },
            
            onError: function(error) {
                console.error('Google Autocomplete error:', error);
                showToast('Error getting address suggestions. Please try again.', 'error');
            },
            
            onAPINotEnabled: function() {
                console.log('Google Places API (New) not enabled - falling back to basic input');
                showToast('Google Places API setup needed. Using basic address validation.', 'warning');
            }
        });
    }
});

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white transition-opacity duration-300 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    }`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}