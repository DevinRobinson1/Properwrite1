// Real Estate Investment Analyzer - JavaScript Functions (No Google Places)

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
    
    // Remove error message
    const errorMessage = field.parentNode.querySelector('.field-error');
    if (errorMessage) {
        errorMessage.remove();
    }
}

// Show field error
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

// Email validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// ZIP code validation
function isValidZip(zip) {
    const zipRegex = /^\d{5}(-\d{4})?$/;
    return zipRegex.test(zip);
}

// Setup editing mode
function setupEditingMode() {
    const editableElements = document.querySelectorAll('.editable');
    
    editableElements.forEach(element => {
        element.addEventListener('click', function() {
            if (!isEditing) {
                enableEditing();
            }
        });
    });
}

// Enable editing
function enableEditing() {
    if (isEditing) return;
    
    isEditing = true;
    const editableElements = document.querySelectorAll('.editable');
    
    // Store original content
    editableElements.forEach(element => {
        originalContent[element.id || element.className] = element.innerHTML;
        makeEditable(element);
    });
    
    showNotification('Editing mode enabled. Click on any highlighted content to edit.', 'info');
}

// Make element editable
function makeEditable(element) {
    element.contentEditable = true;
    element.classList.add('editing');
    
    element.addEventListener('blur', function() {
        this.contentEditable = false;
        this.classList.remove('editing');
        isEditing = false;
        showNotification('Changes saved successfully!', 'success');
    });
    
    element.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.blur();
        }
    });
}

// Generate share link
function generateShareLink() {
    const propertyData = {
        // Collect current property data
        timestamp: new Date().toISOString()
    };
    
    // In a real implementation, this would make an API call
    const shareUrl = `${window.location.origin}/share/${btoa(JSON.stringify(propertyData))}`;
    
    document.getElementById('share-url').value = shareUrl;
    document.getElementById('shareModal').classList.remove('hidden');
    
    showNotification('Share link generated successfully!', 'success');
}

// Copy share link
function copyShareLink() {
    const shareUrl = document.getElementById('share-url');
    shareUrl.select();
    shareUrl.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        showNotification('Share link copied to clipboard!', 'success');
    } catch (err) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(shareUrl.value).then(() => {
                showNotification('Share link copied to clipboard!', 'success');
            }).catch(() => {
                showNotification('Unable to copy link. Please copy manually.', 'error');
            });
        }
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
    
    if (!tooltipText) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip fixed bg-gray-800 text-white px-2 py-1 rounded text-sm z-50';
    tooltip.textContent = tooltipText;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
}

// Hide tooltip
function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
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