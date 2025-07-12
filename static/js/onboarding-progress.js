/**
 * Onboarding Progress Component
 * Displays user onboarding progress and provides manual controls
 */

class OnboardingProgress {
    constructor() {
        this.progressData = null;
        this.isVisible = false;
        this.init();
    }
    
    init() {
        this.createProgressWidget();
        this.loadProgressData();
        this.bindEvents();
    }
    
    createProgressWidget() {
        // Create floating progress widget
        const widget = document.createElement('div');
        widget.id = 'onboarding-progress-widget';
        widget.className = 'onboarding-progress-widget';
        widget.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            padding: 16px;
            max-width: 280px;
            border: 1px solid #e5e7eb;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: none;
        `;
        
        widget.innerHTML = `
            <div class="progress-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #1f2937;">
                    🎯 Getting Started
                </h3>
                <button id="close-progress-widget" style="background: none; border: none; font-size: 16px; cursor: pointer; color: #6b7280;">
                    ×
                </button>
            </div>
            
            <div class="progress-content">
                <div class="progress-bar-container" style="background: #f3f4f6; border-radius: 6px; height: 8px; margin-bottom: 12px;">
                    <div id="progress-bar" class="progress-bar" style="background: linear-gradient(90deg, #3b82f6, #8b5cf6); height: 100%; border-radius: 6px; width: 0%; transition: width 0.3s ease;"></div>
                </div>
                
                <div class="progress-text" style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">
                    <span id="progress-percentage">0%</span> complete • 
                    <span id="steps-remaining">8 steps</span> remaining
                </div>
                
                <div class="progress-actions" style="display: flex; gap: 8px;">
                    <button id="continue-onboarding" class="btn-primary" style="flex: 1; padding: 8px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-size: 12px; cursor: pointer;">
                        Continue
                    </button>
                    <button id="skip-onboarding" class="btn-secondary" style="flex: 1; padding: 8px 12px; background: #f3f4f6; color: #6b7280; border: none; border-radius: 6px; font-size: 12px; cursor: pointer;">
                        Skip
                    </button>
                </div>
                
                <div class="progress-toggle" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #f3f4f6;">
                    <label style="display: flex; align-items: center; font-size: 12px; color: #6b7280; cursor: pointer;">
                        <input type="checkbox" id="auto-onboarding" style="margin-right: 8px;">
                        Show helpful tips automatically
                    </label>
                </div>
            </div>
        `;
        
        document.body.appendChild(widget);
    }
    
    bindEvents() {
        document.getElementById('close-progress-widget').addEventListener('click', () => {
            this.hide();
        });
        
        document.getElementById('continue-onboarding').addEventListener('click', () => {
            this.continueOnboarding();
        });
        
        document.getElementById('skip-onboarding').addEventListener('click', () => {
            this.skipOnboarding();
        });
        
        document.getElementById('auto-onboarding').addEventListener('change', (e) => {
            this.toggleAutoOnboarding(e.target.checked);
        });
    }
    
    async loadProgressData() {
        try {
            const response = await fetch('/api/onboarding/status');
            const data = await response.json();
            
            if (data.success) {
                this.progressData = data.status;
                this.updateDisplay();
                
                // Show widget if onboarding is not complete
                if (!this.progressData.is_onboarding_complete) {
                    this.show();
                }
            }
        } catch (error) {
            console.error('Error loading onboarding progress:', error);
        }
    }
    
    updateDisplay() {
        if (!this.progressData) return;
        
        const progressBar = document.getElementById('progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
        const stepsRemaining = document.getElementById('steps-remaining');
        
        if (progressBar) {
            progressBar.style.width = `${this.progressData.progress_percentage}%`;
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = `${Math.round(this.progressData.progress_percentage)}%`;
        }
        
        if (stepsRemaining) {
            const remaining = this.progressData.steps_remaining;
            stepsRemaining.textContent = `${remaining} step${remaining !== 1 ? 's' : ''}`;
        }
        
        // Update button states
        const continueBtn = document.getElementById('continue-onboarding');
        if (continueBtn) {
            if (this.progressData.is_onboarding_complete) {
                continueBtn.textContent = 'Completed ✓';
                continueBtn.disabled = true;
                continueBtn.style.background = '#10b981';
            } else {
                continueBtn.textContent = 'Continue';
                continueBtn.disabled = false;
            }
        }
    }
    
    show() {
        const widget = document.getElementById('onboarding-progress-widget');
        if (widget) {
            widget.style.display = 'block';
            this.isVisible = true;
        }
    }
    
    hide() {
        const widget = document.getElementById('onboarding-progress-widget');
        if (widget) {
            widget.style.display = 'none';
            this.isVisible = false;
        }
    }
    
    async continueOnboarding() {
        if (!this.progressData || !this.progressData.current_step) {
            return;
        }
        
        // Trigger the current step
        if (window.onboardingToolkit) {
            window.onboardingToolkit.startOnboarding();
        }
        
        this.hide();
    }
    
    async skipOnboarding() {
        try {
            const response = await fetch('/api/onboarding/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hide();
                this.showNotification('Onboarding skipped. You can restart it anytime from your dashboard.', 'info');
            }
        } catch (error) {
            console.error('Error skipping onboarding:', error);
        }
    }
    
    toggleAutoOnboarding(enabled) {
        localStorage.setItem('auto_onboarding', enabled ? 'true' : 'false');
        
        if (window.onboardingToolkit) {
            if (enabled) {
                window.onboardingToolkit.checkOnboardingStatus();
            } else {
                window.onboardingToolkit.stopOnboarding();
            }
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: white;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            padding: 16px;
            max-width: 320px;
            border-left: 4px solid ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 18px;">
                    ${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ️'}
                </div>
                <div style="font-size: 14px; color: #374151;">
                    ${message}
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 4 seconds
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }
    
    // Public methods for external control
    refresh() {
        this.loadProgressData();
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in before creating progress widget
    fetch('/api/user-status')
        .then(response => response.json())
        .then(data => {
            if (data.logged_in) {
                window.onboardingProgress = new OnboardingProgress();
            }
        })
        .catch(error => {
            console.error('Error checking user status:', error);
        });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OnboardingProgress;
}