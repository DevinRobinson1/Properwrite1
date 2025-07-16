// JV Submit Wizard JavaScript
class JVWizard {
  constructor() {
    this.currentStep = 1;
    this.maxSteps = 4;
    this.formData = {};
    this.autocomplete = null;
    this.init();
  }

  init() {
    this.bindEvents();
    this.initGooglePlaces();
    this.loadFromStorage();
    this.updateUI();
  }

  bindEvents() {
    // Next/Previous buttons
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('next')) {
        this.nextStep();
      } else if (e.target.classList.contains('prev')) {
        this.prevStep();
      }
    });

    // Form submission
    document.getElementById('jv-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitForm();
    });

    // Form input changes - save to localStorage
    document.getElementById('jv-form').addEventListener('input', (e) => {
      this.saveToStorage();
    });

    // Step clicks
    document.querySelectorAll('.step').forEach(step => {
      step.addEventListener('click', (e) => {
        const stepNum = parseInt(e.target.dataset.step);
        if (stepNum <= this.currentStep) {
          this.goToStep(stepNum);
        }
      });
    });
  }

  initGooglePlaces() {
    if (typeof google !== 'undefined' && google.maps) {
      const input = document.getElementById('autocomplete');
      if (input) {
        this.autocomplete = new google.maps.places.Autocomplete(input, {
          types: ['address'],
          componentRestrictions: { country: 'us' }
        });

        this.autocomplete.addListener('place_changed', () => {
          const place = this.autocomplete.getPlace();
          if (place.formatted_address) {
            input.value = place.formatted_address;
            this.saveToStorage();
          }
        });
      }
    }
  }

  nextStep() {
    if (this.validateCurrentStep()) {
      this.saveToStorage();
      if (this.currentStep < this.maxSteps) {
        this.currentStep++;
        if (this.currentStep === 4) {
          this.generateReview();
        }
        this.updateUI();
      }
    }
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.updateUI();
    }
  }

  goToStep(stepNum) {
    this.currentStep = stepNum;
    this.updateUI();
  }

  validateCurrentStep() {
    const currentFieldset = document.querySelector(`fieldset[data-step="${this.currentStep}"]`);
    const requiredFields = currentFieldset.querySelectorAll('input[required], select[required]');
    
    let isValid = true;
    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        field.classList.add('border-red-300');
        isValid = false;
      } else {
        field.classList.remove('border-red-300');
      }
    });

    // Email validation
    const emailField = currentFieldset.querySelector('input[type="email"]');
    if (emailField && emailField.value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(emailField.value)) {
        emailField.classList.add('border-red-300');
        isValid = false;
      }
    }

    // Phone validation
    const phoneField = currentFieldset.querySelector('input[type="tel"]');
    if (phoneField && phoneField.value) {
      const phoneRegex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
      if (!phoneRegex.test(phoneField.value)) {
        phoneField.classList.add('border-red-300');
        isValid = false;
      }
    }

    if (!isValid) {
      this.showMessage('Please fill in all required fields correctly.', 'error');
    }

    return isValid;
  }

  updateUI() {
    // Update step indicators
    document.querySelectorAll('.step').forEach(step => {
      const stepNum = parseInt(step.dataset.step);
      if (stepNum === this.currentStep) {
        step.classList.add('active');
      } else {
        step.classList.remove('active');
      }
    });

    // Show/hide fieldsets
    document.querySelectorAll('fieldset').forEach(fieldset => {
      const stepNum = parseInt(fieldset.dataset.step);
      if (stepNum === this.currentStep) {
        fieldset.hidden = false;
      } else {
        fieldset.hidden = true;
      }
    });
  }

  generateReview() {
    const formData = this.getFormData();
    const reviewContainer = document.getElementById('review-container');
    
    let reviewHTML = '<div class="space-y-2">';
    
    if (formData.email) {
      reviewHTML += `<div class="review-item"><span class="review-label">Email:</span><span class="review-value">${formData.email}</span></div>`;
    }
    
    if (formData.phone) {
      reviewHTML += `<div class="review-item"><span class="review-label">Phone:</span><span class="review-value">${formData.phone}</span></div>`;
    }
    
    if (formData.address) {
      reviewHTML += `<div class="review-item"><span class="review-label">Address:</span><span class="review-value">${formData.address}</span></div>`;
    }
    
    if (formData.deal_type) {
      reviewHTML += `<div class="review-item"><span class="review-label">Deal Type:</span><span class="review-value">${formData.deal_type}</span></div>`;
    }
    
    if (formData.asking_price) {
      reviewHTML += `<div class="review-item"><span class="review-label">Asking Price:</span><span class="review-value">$${parseInt(formData.asking_price).toLocaleString()}</span></div>`;
    }
    
    if (formData.arv) {
      reviewHTML += `<div class="review-item"><span class="review-label">ARV:</span><span class="review-value">$${parseInt(formData.arv).toLocaleString()}</span></div>`;
    }
    
    if (formData.rehab_cost) {
      reviewHTML += `<div class="review-item"><span class="review-label">Rehab Cost:</span><span class="review-value">$${parseInt(formData.rehab_cost).toLocaleString()}</span></div>`;
    }
    
    if (formData.photo_link) {
      reviewHTML += `<div class="review-item"><span class="review-label">Photo Link:</span><span class="review-value"><a href="${formData.photo_link}" target="_blank" class="text-blue-600 hover:underline">View Photos</a></span></div>`;
    }
    
    reviewHTML += '</div>';
    
    // Add AI analysis if available
    if (formData.arv && formData.asking_price) {
      this.generateAIAnalysis(formData);
    }
    
    reviewContainer.innerHTML = reviewHTML;
  }

  async generateAIAnalysis(formData) {
    try {
      const response = await fetch('/api/ai_deal_analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address: formData.address,
          asking_price: formData.asking_price,
          arv: formData.arv,
          rehab_cost: formData.rehab_cost || 0,
          deal_type: formData.deal_type
        })
      });

      if (response.ok) {
        const analysis = await response.json();
        const aiSection = document.createElement('div');
        aiSection.className = 'ai-analysis';
        aiSection.innerHTML = `
          <h3>AI Deal Analysis</h3>
          <p>${analysis.analysis}</p>
        `;
        document.getElementById('review-container').appendChild(aiSection);
      }
    } catch (error) {
      console.log('AI analysis unavailable:', error);
    }
  }

  getFormData() {
    const formData = {};
    const form = document.getElementById('jv-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
      if (input.name && input.value) {
        formData[input.name] = input.value;
      }
    });
    
    return formData;
  }

  saveToStorage() {
    const formData = this.getFormData();
    localStorage.setItem('jv_form_data', JSON.stringify(formData));
    localStorage.setItem('jv_current_step', this.currentStep.toString());
  }

  loadFromStorage() {
    const savedData = localStorage.getItem('jv_form_data');
    const savedStep = localStorage.getItem('jv_current_step');
    
    if (savedData) {
      try {
        const formData = JSON.parse(savedData);
        Object.keys(formData).forEach(key => {
          const input = document.querySelector(`[name="${key}"]`);
          if (input) {
            input.value = formData[key];
          }
        });
      } catch (e) {
        console.log('Error loading saved data:', e);
      }
    }
    
    if (savedStep) {
      this.currentStep = parseInt(savedStep);
    }
  }

  clearStorage() {
    localStorage.removeItem('jv_form_data');
    localStorage.removeItem('jv_current_step');
  }

  async submitForm() {
    if (!this.validateCurrentStep()) {
      return;
    }

    const formData = this.getFormData();
    const submitButton = document.querySelector('button[type="submit"]');
    
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';
    
    try {
      const response = await fetch('/api/jv-deals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (response.ok) {
        this.showMessage('Deal submitted successfully! We\'ll review it and get back to you soon.', 'success');
        this.clearStorage();
        
        // Redirect after 2 seconds
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        this.showMessage(result.error || 'Failed to submit deal. Please try again.', 'error');
      }
    } catch (error) {
      console.error('Submission error:', error);
      this.showMessage('Network error. Please check your connection and try again.', 'error');
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = 'Submit JV Deal';
    }
  }

  showMessage(text, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());

    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    const wizard = document.getElementById('jv-wizard');
    wizard.insertBefore(message, wizard.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      message.remove();
    }, 5000);
  }
}

// Initialize wizard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new JVWizard();
});