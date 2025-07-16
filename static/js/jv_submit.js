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
    console.log('Binding events...');
    
    // Next/Previous buttons
    document.addEventListener('click', (e) => {
      console.log('Click detected on:', e.target);
      
      if (e.target.classList.contains('next') || e.target.closest('.next')) {
        console.log('Next button clicked');
        e.preventDefault();
        this.nextStep();
      } else if (e.target.classList.contains('prev') || e.target.closest('.prev')) {
        console.log('Previous button clicked');
        e.preventDefault();
        this.prevStep();
      }
    });

    // Form submission
    const form = document.getElementById('jv-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitForm();
      });
    }

    // Form input changes - save to localStorage
    if (form) {
      form.addEventListener('input', (e) => {
        this.saveToStorage();
      });
    }

    // Step clicks
    document.querySelectorAll('.step-indicator').forEach(indicator => {
      indicator.addEventListener('click', (e) => {
        const stepNum = parseInt(indicator.dataset.step);
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
    console.log('nextStep called, current step:', this.currentStep);
    
    if (this.validateCurrentStep()) {
      console.log('Validation passed, moving to next step');
      this.saveToStorage();
      if (this.currentStep < this.maxSteps) {
        this.currentStep++;
        console.log('New step:', this.currentStep);
        if (this.currentStep === 4) {
          this.generateReview();
        }
        this.updateUI();
      }
    } else {
      console.log('Validation failed');
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
    document.querySelectorAll('.step-indicator').forEach(indicator => {
      const stepNum = parseInt(indicator.dataset.step);
      indicator.classList.remove('active', 'completed');
      
      if (stepNum === this.currentStep) {
        indicator.classList.add('active');
      } else if (stepNum < this.currentStep) {
        indicator.classList.add('completed');
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

    // Update animated progress bar
    this.updateProgressBar();
  }

  updateProgressBar() {
    const progressBar = document.getElementById('progress-bar');
    const progressDot = document.getElementById('progress-dot');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    
    if (progressBar && progressDot && progressText && progressPercent) {
      const progress = (this.currentStep / this.maxSteps) * 100;
      
      // Animate progress bar
      progressBar.style.width = progress + '%';
      progressDot.style.left = `calc(${progress}% - 8px)`;
      
      // Update text
      progressText.textContent = `Step ${this.currentStep} of ${this.maxSteps}`;
      progressPercent.textContent = Math.round(progress) + '%';
      
      // Change dot color based on step
      const colors = ['border-blue-500', 'border-green-500', 'border-purple-500', 'border-orange-500'];
      progressDot.className = `absolute -top-1 left-0 w-5 h-5 bg-white border-4 ${colors[this.currentStep - 1]} rounded-full shadow-lg transform -translate-x-2 transition-all duration-700 ease-out`;
    }
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
        // Trigger confetti celebration
        this.triggerConfetti();
        
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

  triggerConfetti() {
    // Create multiple confetti bursts
    const colors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B'];
    
    // First burst
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: colors
    });
    
    // Second burst with delay
    setTimeout(() => {
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.7 },
        colors: colors
      });
    }, 200);
    
    // Third burst with different settings
    setTimeout(() => {
      confetti({
        particleCount: 60,
        spread: 90,
        origin: { y: 0.5 },
        colors: colors,
        shapes: ['star', 'circle']
      });
    }, 400);
    
    // Final burst from both sides
    setTimeout(() => {
      confetti({
        particleCount: 50,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: colors
      });
      confetti({
        particleCount: 50,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: colors
      });
    }, 600);
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
  console.log('DOM loaded, initializing JVWizard...');
  window.jvWizard = new JVWizard();
  console.log('JVWizard initialized:', window.jvWizard);
});