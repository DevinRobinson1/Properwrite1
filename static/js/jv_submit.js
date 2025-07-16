// Google Maps API callback function
function initJVAutocomplete() {
  console.log('Google Maps API loaded - initializing JV autocomplete');
  if (window.jvWizard) {
    window.jvWizard.initGooglePlaces();
  }
}

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
    this.initNumberFormatting();
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

  initNumberFormatting() {
    // Format number fields with commas
    const numberFields = ['asking_price', 'arv', 'rehab_cost'];
    
    numberFields.forEach(fieldName => {
      const input = document.querySelector(`[name="${fieldName}"]`);
      if (input) {
        input.addEventListener('input', (e) => {
          this.formatNumberInput(e.target);
        });
        
        input.addEventListener('blur', (e) => {
          this.formatNumberInput(e.target);
        });
      }
    });
  }

  formatNumberInput(input) {
    // Get raw value without commas
    let value = input.value.replace(/,/g, '');
    
    // Only format if it's a valid number
    if (value && !isNaN(value)) {
      // Format with commas
      const formatted = parseInt(value).toLocaleString('en-US');
      input.value = formatted;
    }
  }

  getUnformattedValue(input) {
    // Return raw numeric value without commas
    return input.value.replace(/,/g, '');
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
    if (!currentFieldset) {
      console.log('No fieldset found for current step:', this.currentStep);
      return false;
    }

    const requiredFields = currentFieldset.querySelectorAll('input[required], select[required]');
    console.log('Required fields found:', requiredFields.length);
    
    let isValid = true;
    requiredFields.forEach(field => {
      console.log('Checking field:', field.name, 'value:', field.value);
      if (!field.value.trim()) {
        field.classList.add('border-red-300');
        isValid = false;
        console.log('Field is empty:', field.name);
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
        console.log('Email validation failed:', emailField.value);
      } else {
        console.log('Email validation passed:', emailField.value);
      }
    }

    // Phone validation
    const phoneField = currentFieldset.querySelector('input[type="tel"]');
    if (phoneField && phoneField.value) {
      const phoneRegex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
      if (!phoneRegex.test(phoneField.value)) {
        phoneField.classList.add('border-red-300');
        isValid = false;
        console.log('Phone validation failed:', phoneField.value);
      } else {
        console.log('Phone validation passed:', phoneField.value);
      }
    }

    console.log('Validation result:', isValid);
    
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

  // HTML escape function to prevent XSS
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  generateReview() {
    const formData = this.getFormData();
    const reviewContainer = document.getElementById('review-container');
    
    // Clear existing content
    reviewContainer.innerHTML = '';
    
    // Create container div
    const container = document.createElement('div');
    container.className = 'space-y-2';
    
    // Helper function to create review item
    const createReviewItem = (label, value) => {
      const item = document.createElement('div');
      item.className = 'review-item';
      
      const labelSpan = document.createElement('span');
      labelSpan.className = 'review-label';
      labelSpan.textContent = label + ':';
      
      const valueSpan = document.createElement('span');
      valueSpan.className = 'review-value';
      valueSpan.textContent = value;
      
      item.appendChild(labelSpan);
      item.appendChild(valueSpan);
      return item;
    };
    
    // Helper function to create review item with link
    const createReviewItemWithLink = (label, url, linkText) => {
      const item = document.createElement('div');
      item.className = 'review-item';
      
      const labelSpan = document.createElement('span');
      labelSpan.className = 'review-label';
      labelSpan.textContent = label + ':';
      
      const valueSpan = document.createElement('span');
      valueSpan.className = 'review-value';
      
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.className = 'text-blue-600 hover:underline';
      link.textContent = linkText;
      
      valueSpan.appendChild(link);
      item.appendChild(labelSpan);
      item.appendChild(valueSpan);
      return item;
    };
    
    // Add form data to review
    if (formData.email) {
      container.appendChild(createReviewItem('Email', formData.email));
    }
    
    if (formData.phone) {
      container.appendChild(createReviewItem('Phone', formData.phone));
    }
    
    if (formData.address) {
      container.appendChild(createReviewItem('Address', formData.address));
    }
    
    if (formData.deal_type) {
      container.appendChild(createReviewItem('Deal Type', formData.deal_type));
    }
    
    if (formData.asking_price) {
      const price = '$' + parseInt(formData.asking_price).toLocaleString();
      container.appendChild(createReviewItem('Asking Price', price));
    }
    
    if (formData.arv) {
      const arv = '$' + parseInt(formData.arv).toLocaleString();
      container.appendChild(createReviewItem('ARV', arv));
    }
    
    if (formData.rehab_cost) {
      const rehab = '$' + parseInt(formData.rehab_cost).toLocaleString();
      container.appendChild(createReviewItem('Rehab Cost', rehab));
    }
    
    if (formData.property_status) {
      container.appendChild(createReviewItem('Property Status', formData.property_status));
    }
    
    if (formData.closing_date) {
      const date = new Date(formData.closing_date);
      container.appendChild(createReviewItem('Expected Closing', date.toLocaleDateString()));
    }
    
    if (formData.property_description) {
      container.appendChild(createReviewItem('Description', formData.property_description));
    }
    
    if (formData.photo_link) {
      // Validate URL format before creating link
      try {
        new URL(formData.photo_link);
        container.appendChild(createReviewItemWithLink('Photo Link', formData.photo_link, 'View Photos'));
      } catch (e) {
        container.appendChild(createReviewItem('Photo Link', formData.photo_link));
      }
    }
    
    if (formData.additional_notes) {
      container.appendChild(createReviewItem('Additional Notes', formData.additional_notes));
    }
    
    // Add container to DOM
    reviewContainer.appendChild(container);
    
    // Add AI analysis if available
    if (formData.arv && formData.asking_price) {
      this.generateAIAnalysis(formData);
    }
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
    const numberFields = ['asking_price', 'arv', 'rehab_cost'];
    
    inputs.forEach(input => {
      if (input.name && input.value) {
        // Remove commas from number fields before sending to backend
        if (numberFields.includes(input.name)) {
          formData[input.name] = input.value.replace(/,/g, '');
        } else {
          formData[input.name] = input.value;
        }
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

    const submitButton = document.querySelector('button[type="submit"]');
    
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';
    
    try {
      // Use FormData to include CSRF token
      const formData = new FormData(document.getElementById('jv-form'));
      
      // Add MAO analysis before submission
      const dealData = this.getFormData();
      const maoAnalysis = this.calculateMAO(dealData);
      
      // Add analysis to form data
      formData.append('mao_analysis', JSON.stringify(maoAnalysis));
      
      // Debug: Log form data
      console.log('Form data being submitted:', Array.from(formData.entries()));
      console.log('MAO analysis:', maoAnalysis);
      
      console.log('🚀 Submitting to /api/jv-submit endpoint');
      const response = await fetch('/api/jv-submit', {
        method: 'POST',
        body: formData  // Don't set Content-Type header with FormData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText.slice(0, 200)}`);
      }

      const result = await response.json();

      if (response.ok) {
        console.log('✅ Deal submitted successfully!', result);
        
        // Show analysis results if available
        if (result.underwrite_result) {
          this.showAnalysisResults(result.underwrite_result);
        }
        
        // Trigger confetti celebration
        this.triggerConfetti();
        
        this.showMessage('Deal submitted successfully! We\'ll review it and get back to you soon.', 'success');
        this.clearStorage();
        
        // Redirect after 5 seconds to show success
        setTimeout(() => {
          window.location.href = '/';
        }, 5000);
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

  calculateMAO(dealData) {
    const askingPrice = parseFloat(dealData.asking_price?.replace(/,/g, '') || 0);
    const arv = parseFloat(dealData.arv?.replace(/,/g, '') || 0);
    const rehabCost = parseFloat(dealData.rehab_cost?.replace(/,/g, '') || 0);
    
    console.log('Calculating MAO with:', { askingPrice, arv, rehabCost });
    
    // Standard wholesale MAO calculation
    const wholesaleMAO = arv * 0.70 - rehabCost;
    const assignmentFee = 15000; // Standard assignment fee
    const finalMAO = wholesaleMAO - assignmentFee;
    
    // Novation calculation (higher profit potential)
    const novationMAO = arv * 0.85 - rehabCost - 25000; // Higher ARV%, account for closing costs
    
    // Profit calculations
    const wholesaleProfit = finalMAO - askingPrice;
    const novationProfit = novationMAO - askingPrice;
    
    // Deal recommendations
    const recommendations = [];
    
    if (wholesaleProfit > 0) {
      recommendations.push({
        strategy: 'Wholesale',
        mao: finalMAO,
        profit: wholesaleProfit,
        confidence: wholesaleProfit > 10000 ? 'High' : 'Medium'
      });
    }
    
    if (novationProfit > 0 && novationProfit > wholesaleProfit) {
      recommendations.push({
        strategy: 'Novation',
        mao: novationMAO,
        profit: novationProfit,
        confidence: novationProfit > 15000 ? 'High' : 'Medium'
      });
    }
    
    // Approval logic
    let approvalStatus = 'pending';
    let approvalReason = '';
    
    if (recommendations.length === 0) {
      approvalStatus = 'needs_review';
      approvalReason = 'No profitable strategies found - requires manual review';
    } else if (Math.max(wholesaleProfit, novationProfit) > 20000) {
      approvalStatus = 'auto_approved';
      approvalReason = 'High profit potential - automatically approved';
    } else if (Math.max(wholesaleProfit, novationProfit) > 10000) {
      approvalStatus = 'likely_approved';
      approvalReason = 'Good profit potential - likely to be approved';
    } else {
      approvalStatus = 'needs_review';
      approvalReason = 'Lower profit margins - requires careful review';
    }
    
    return {
      askingPrice,
      arv,
      rehabCost,
      wholesaleMAO: finalMAO,
      novationMAO,
      wholesaleProfit,
      novationProfit,
      recommendations,
      approvalStatus,
      approvalReason
    };
  }

  showAnalysisResults(analysis) {
    console.log('📊 Showing analysis results:', analysis);
    
    const reviewContainer = document.getElementById('review-container');
    if (!reviewContainer) {
      console.warn('Review container not found');
      return;
    }
    
    // Handle different response formats
    const status = analysis.status || 'unknown';
    const reasons = analysis.reasons || [];
    const mao = analysis.mao || 0;
    
    let analysisHTML = `
      <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 class="text-lg font-semibold text-blue-900 mb-3">
          <i class="fas fa-chart-line mr-2"></i>Deal Analysis Results
        </h3>
    `;
    
    // Status display
    const statusColor = status === 'auto-approved' ? 'text-green-600' : 
                       status === 'likely-approved' ? 'text-yellow-600' : 'text-red-600';
    
    analysisHTML += `
      <div class="p-3 bg-gray-50 rounded border">
        <div class="flex items-center justify-between">
          <span class="font-medium">Status:</span>
          <span class="font-semibold ${statusColor}">${status.replace('_', ' ').replace('-', ' ').toUpperCase()}</span>
        </div>
        ${mao > 0 ? `<p class="text-sm text-gray-600 mt-1">Maximum Allowable Offer: $${mao.toLocaleString()}</p>` : ''}
        ${reasons.length > 0 ? `<div class="mt-2 text-sm text-gray-600">
          <ul class="list-disc pl-4">
            ${reasons.map(reason => `<li>${reason}</li>`).join('')}
          </ul>
        </div>` : ''}
      </div>
    `;
    
    analysisHTML += '</div>';
    
    reviewContainer.innerHTML += analysisHTML;
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