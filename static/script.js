// Real Estate Investment Analyzer - JavaScript Functions

// Global variables
let isEditing = false;
let originalContent = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Add form validation
    setupFormValidation();
    
    // Setup editing functionality if on presentation page
    if (document.querySelector('.editable')) {
        setupEditingMode();
    }
    
    // Add smooth scrolling for anchor links
    setupSmoothScrolling();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Google Places disabled - manual address entry enabled
});

// Form validation setup
function setupFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;
    
    const inputs = form.querySelectorAll('input[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldError);
    });
    
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField({ target: input })) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            showError('Please fill in all required fields correctly.');
        } else {
            showLoading();
        }
    });
}

// Validate individual form field
function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error styling
    field.classList.remove('border-red-500', 'bg-red-50');
    
    // Check if required field is empty
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required.';
    }
    
    // Specific validation rules
    switch(field.type) {
        case 'email':
            if (value && !isValidEmail(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address.';
            }
            break;
        case 'number':
            if (value && (isNaN(value) || parseFloat(value) < 0)) {
                isValid = false;
                errorMessage = 'Please enter a valid positive number.';
            }
            break;
        case 'text':
            if (field.name === 'zip' && value && !isValidZip(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid ZIP code.';
            }
            break;
    }
    
    if (!isValid) {
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

// Clear field error styling
function clearFieldError(event) {
    const field = event.target;
    field.classList.remove('border-red-500', 'bg-red-50');
    
    // Remove error message if exists
    const errorDiv = field.parentNode.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Show field-specific error
function showFieldError(field, message) {
    field.classList.add('border-red-500', 'bg-red-50');
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-red-600 text-sm mt-1';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

// Utility functions for validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidZip(zip) {
    const zipRegex = /^\d{5}(-\d{4})?$/;
    return zipRegex.test(zip);
}

// Setup editing mode for presentation page
function setupEditingMode() {
    const editableElements = document.querySelectorAll('.editable');
    
    editableElements.forEach(element => {
        originalContent[element.dataset.field] = element.innerHTML;
        
        element.addEventListener('click', function() {
            if (isEditing) {
                makeEditable(this);
            }
        });
    });
}

// Enable editing mode
function enableEditing() {
    isEditing = !isEditing;
    const editBtn = document.querySelector('button[onclick="enableEditing()"]');
    const editableElements = document.querySelectorAll('.editable');
    
    if (isEditing) {
        editBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Save Changes';
        editBtn.className = editBtn.className.replace('bg-blue-600', 'bg-green-600');
        
        editableElements.forEach(element => {
            element.classList.add('editing');
            element.title = 'Click to edit this content';
        });
        
        showNotification('Editing mode enabled. Click on any highlighted content to edit.', 'info');
    } else {
        editBtn.innerHTML = '<i class="fas fa-edit mr-2"></i>Edit Content';
        editBtn.className = editBtn.className.replace('bg-green-600', 'bg-blue-600');
        
        editableElements.forEach(element => {
            element.classList.remove('editing');
            element.removeAttribute('title');
            element.contentEditable = false;
        });
        
        showNotification('Changes saved successfully!', 'success');
    }
}

// Make element editable
function makeEditable(element) {
    element.contentEditable = true;
    element.focus();
    
    // Select all text
    const range = document.createRange();
    range.selectNodeContents(element);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    
    element.addEventListener('blur', function() {
        this.contentEditable = false;
    });
    
    element.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.blur();
        }
        if (e.key === 'Escape') {
            this.innerHTML = originalContent[this.dataset.field];
            this.blur();
        }
    });
}

// Generate share link
function generateShareLink() {
    const shareModal = document.getElementById('shareModal');
    const shareUrl = document.getElementById('shareUrl');
    
    // Generate a unique share URL (in a real app, this would be generated server-side)
    const currentUrl = window.location.href;
    const shareId = Math.random().toString(36).substring(2, 15);
    const generatedUrl = `${currentUrl}?share=${shareId}`;
    
    shareUrl.value = generatedUrl;
    shareModal.classList.remove('hidden');
    shareModal.querySelector('.bg-white').classList.add('modal-enter');
    
    showNotification('Share link generated successfully!', 'success');
}

// Copy share link to clipboard
function copyShareLink() {
    const shareUrl = document.getElementById('shareUrl');
    shareUrl.select();
    shareUrl.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        showNotification('Share link copied to clipboard!', 'success');
    } catch (err) {
        // Fallback for modern browsers
        navigator.clipboard.writeText(shareUrl.value).then(() => {
            showNotification('Share link copied to clipboard!', 'success');
        }).catch(() => {
            showNotification('Unable to copy link. Please copy manually.', 'error');
        });
    }
}

// Close share modal
function closeShareModal() {
    const shareModal = document.getElementById('shareModal');
    shareModal.classList.add('hidden');
}

// Show loading state
function showLoading() {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating Analysis...';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md fade-in`;
    
    // Set colors based on type
    switch(type) {
        case 'success':
            notification.className += ' bg-green-100 border border-green-400 text-green-700';
            break;
        case 'error':
            notification.className += ' bg-red-100 border border-red-400 text-red-700';
            break;
        case 'warning':
            notification.className += ' bg-yellow-100 border border-yellow-400 text-yellow-700';
            break;
        default:
            notification.className += ' bg-blue-100 border border-blue-400 text-blue-700';
    }
    
    // Create elements safely without innerHTML to prevent XSS
    const container = document.createElement('div');
    container.className = 'flex items-center';
    
    const messageSpan = document.createElement('span');
    messageSpan.className = 'flex-1';
    messageSpan.textContent = message; // Safe text content assignment
    
    const closeButton = document.createElement('button');
    closeButton.className = 'ml-2 text-lg font-bold';
    closeButton.textContent = '×';
    closeButton.onclick = function() { 
        this.parentElement.parentElement.remove(); 
    };
    
    container.appendChild(messageSpan);
    container.appendChild(closeButton);
    notification.appendChild(container);
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Show error message
function showError(message) {
    showNotification(message, 'error');
}

// Setup smooth scrolling
function setupSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// Show tooltip
function showTooltip(event) {
    const element = event.target;
    const tooltipText = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.className = 'absolute bg-gray-800 text-white text-sm rounded py-1 px-2 z-50';
    tooltip.textContent = tooltipText;
    tooltip.id = 'tooltip';
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

// Hide tooltip
function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Format currency input
function formatCurrency(input) {
    let value = input.value.replace(/[^\d]/g, '');
    if (value) {
        value = parseInt(value).toLocaleString();
        input.value = '$' + value;
    }
}

// Google Places Autocomplete functionality
let autocomplete;
let selectedPlace = null;

function initGooglePlaces() {
    const addressInput = document.getElementById('property-address');
    const cityInput = document.getElementById('city');
    const stateInput = document.getElementById('state');
    const zipInput = document.getElementById('zip');
    const loadingSpinner = document.getElementById('address-loading');
    
    if (!addressInput) return;
    
    // Check if Google Places API is available
    if (!window.google || !window.google.maps || !window.google.maps.places) {
        console.log('Google Places API not available - using manual entry mode');
        return;
    }
    
    // Initialize Google Places Autocomplete with error handling
    try {
        autocomplete = new google.maps.places.Autocomplete(addressInput, {
            types: ['address'],
            componentRestrictions: { country: 'us' },
            fields: ['address_components', 'formatted_address', 'geometry', 'name']
        });
    } catch (error) {
        console.log('Google Places API initialization failed:', error);
        return;
    }
    
    // Show loading spinner when user starts typing
    let typingTimer;
    addressInput.addEventListener('input', function() {
        clearTimeout(typingTimer);
        if (this.value.length > 2) {
            loadingSpinner.classList.remove('hidden');
            
            // Hide spinner after 3 seconds if no selection made
            typingTimer = setTimeout(() => {
                loadingSpinner.classList.add('hidden');
            }, 3000);
        } else {
            loadingSpinner.classList.add('hidden');
        }
    });
    
    // Handle place selection
    autocomplete.addListener('place_changed', function() {
        loadingSpinner.classList.add('hidden');
        const place = autocomplete.getPlace();
        
        if (!place.geometry) {
            // Allow manual entry without requiring Google Places selection
            return;
        }
        
        selectedPlace = place;
        
        // Extract address components
        const components = place.address_components;
        let streetNumber = '';
        let route = '';
        let city = '';
        let state = '';
        let postalCode = '';
        
        components.forEach(component => {
            const types = component.types;
            
            if (types.includes('street_number')) {
                streetNumber = component.long_name;
            }
            if (types.includes('route')) {
                route = component.long_name;
            }
            if (types.includes('locality')) {
                city = component.long_name;
            }
            if (types.includes('administrative_area_level_1')) {
                state = component.short_name;
            }
            if (types.includes('postal_code')) {
                postalCode = component.long_name;
            }
        });
        
        // Populate form fields
        const fullAddress = `${streetNumber} ${route}`.trim();
        addressInput.value = fullAddress;
        
        if (cityInput && city) cityInput.value = city;
        if (stateInput && state) stateInput.value = state;
        if (zipInput && postalCode) zipInput.value = postalCode;
        
        // Store coordinates for API calls
        if (place.geometry && place.geometry.location) {
            const lat = place.geometry.location.lat();
            const lng = place.geometry.location.lng();
            
            addressInput.dataset.latitude = lat;
            addressInput.dataset.longitude = lng;
            
            // Add hidden inputs to the form to pass coordinates
            let latInput = document.getElementById('latitude-input');
            let lngInput = document.getElementById('longitude-input');
            
            if (!latInput) {
                latInput = document.createElement('input');
                latInput.type = 'hidden';
                latInput.id = 'latitude-input';
                latInput.name = 'latitude';
                addressInput.form.appendChild(latInput);
            }
            
            if (!lngInput) {
                lngInput = document.createElement('input');
                lngInput.type = 'hidden';
                lngInput.id = 'longitude-input';
                lngInput.name = 'longitude';
                addressInput.form.appendChild(lngInput);
            }
            
            latInput.value = lat;
            lngInput.value = lng;
        }
        
        // Visual feedback
        addressInput.classList.add('border-green-500', 'bg-green-50');
        setTimeout(() => {
            addressInput.classList.remove('border-green-500', 'bg-green-50');
        }, 2000);
        
        showNotification('Address validated successfully!', 'success');
    });
    
    // Handle manual typing without selection
    addressInput.addEventListener('blur', function() {
        loadingSpinner.classList.add('hidden');
        
        if (this.value && !selectedPlace) {
            // Allow manual entry without Google Places - remove the notification requirement
            // showNotification('Please select an address from the dropdown for best results.', 'info');
        }
    });
}

// Initialize Google Places when API loads
function initializeGoogleMaps() {
    if (window.google && window.google.maps) {
        initGooglePlaces();
    } else {
        // Retry in case API is still loading
        setTimeout(initializeGoogleMaps, 500);
    }
}

// Enhanced address autocomplete functionality for fallback
document.addEventListener('DOMContentLoaded', function() {
    setupAddressAutocomplete();
    initializeGoogleMaps();
});

function setupAddressAutocomplete() {
    const addressInput = document.getElementById('property-address');
    const cityInput = document.getElementById('city');
    const stateInput = document.getElementById('state');
    const zipInput = document.getElementById('zip');
    
    if (!addressInput) return;
    
    // Fallback: Auto-populate other fields when address is pasted
    addressInput.addEventListener('paste', function(e) {
        setTimeout(() => {
            const value = e.target.value;
            
            // If user pastes a full address, try to parse it
            if (value.includes(',')) {
                const parts = value.split(',').map(part => part.trim());
                if (parts.length >= 3) {
                    // Try to extract city, state, zip from pasted address
                    const lastPart = parts[parts.length - 1];
                    const secondLastPart = parts[parts.length - 2];
                    
                    // Check if last part looks like "STATE ZIP"
                    const stateZipMatch = lastPart.match(/^([A-Z]{2})\s+(\d{5}(-\d{4})?)$/);
                    if (stateZipMatch) {
                        if (cityInput && !cityInput.value) cityInput.value = secondLastPart;
                        if (stateInput && !stateInput.value) stateInput.value = stateZipMatch[1];
                        if (zipInput && !zipInput.value) zipInput.value = stateZipMatch[2];
                    }
                }
            }
        }, 100);
    });
}

// Handle modal clicks outside content
document.addEventListener('click', function(event) {
    const shareModal = document.getElementById('shareModal');
    if (shareModal && event.target === shareModal) {
        closeShareModal();
    }
});

// Handle escape key for modals
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const shareModal = document.getElementById('shareModal');
        if (shareModal && !shareModal.classList.contains('hidden')) {
            closeShareModal();
        }
    }
});

// Add print styles optimization
window.addEventListener('beforeprint', function() {
    // Ensure all content is visible for printing
    const editableElements = document.querySelectorAll('.editable');
    editableElements.forEach(element => {
        element.classList.remove('editing');
        element.contentEditable = false;
    });
});

// Performance optimization: Lazy load heavy content
function lazyLoadContent() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading if supported
if ('IntersectionObserver' in window) {
    document.addEventListener('DOMContentLoaded', lazyLoadContent);
}
