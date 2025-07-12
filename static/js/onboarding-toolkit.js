/**
 * Interactive User Onboarding Toolkit
 * Provides guided tours, tooltips, and interactive tutorials
 */

class OnboardingToolkit {
    constructor() {
        this.currentStep = null;
        this.isOnboardingActive = false;
        this.userStatus = null;
        this.completedSteps = [];
        
        // Initialize tooltip and modal containers
        this.initializeContainers();
        
        // Auto-start onboarding for new users
        this.checkOnboardingStatus();
    }
    
    initializeContainers() {
        // Create tooltip container
        if (!document.getElementById('onboarding-tooltip')) {
            const tooltip = document.createElement('div');
            tooltip.id = 'onboarding-tooltip';
            tooltip.className = 'onboarding-tooltip';
            tooltip.style.cssText = `
                position: fixed;
                z-index: 10000;
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                padding: 20px;
                max-width: 320px;
                display: none;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: 1px solid #e5e7eb;
            `;
            document.body.appendChild(tooltip);
        }
        
        // Create modal container
        if (!document.getElementById('onboarding-modal')) {
            const modal = document.createElement('div');
            modal.id = 'onboarding-modal';
            modal.className = 'onboarding-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 9999;
                display: none;
                justify-content: center;
                align-items: center;
                padding: 20px;
                box-sizing: border-box;
            `;
            document.body.appendChild(modal);
        }
        
        // Create spotlight overlay
        if (!document.getElementById('onboarding-spotlight')) {
            const spotlight = document.createElement('div');
            spotlight.id = 'onboarding-spotlight';
            spotlight.className = 'onboarding-spotlight';
            spotlight.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 9998;
                display: none;
                pointer-events: none;
            `;
            document.body.appendChild(spotlight);
        }
    }
    
    async checkOnboardingStatus() {
        try {
            // Check if user is logged in
            const userStatusResponse = await fetch('/api/user-status');
            const userStatus = await userStatusResponse.json();
            
            if (userStatus.logged_in) {
                // Get onboarding status for logged-in users
                const response = await fetch('/api/onboarding/status');
                const data = await response.json();
                
                if (data.success) {
                    this.userStatus = data.status;
                    
                    // Auto-start onboarding if not complete
                    if (!this.userStatus.is_onboarding_complete && this.userStatus.current_step) {
                        this.startOnboarding();
                    }
                }
            } else {
                // Show guest tips for non-logged-in users
                this.showGuestTips();
            }
        } catch (error) {
            console.error('Error checking onboarding status:', error);
        }
    }
    
    async showGuestTips() {
        try {
            const response = await fetch('/api/onboarding/guest-tips');
            const data = await response.json();
            
            if (data.success && data.tips.length > 0) {
                // Show first tip after a short delay
                setTimeout(() => {
                    this.showGuestTip(data.tips[0]);
                }, 2000);
            }
        } catch (error) {
            console.error('Error getting guest tips:', error);
        }
    }
    
    showGuestTip(tip) {
        const target = document.querySelector(tip.target);
        if (!target) return;
        
        const tooltip = document.getElementById('onboarding-tooltip');
        
        tooltip.innerHTML = `
            <div class="onboarding-tip-content">
                <h3 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #1f2937;">
                    ${tip.title}
                </h3>
                <p style="margin: 0 0 15px 0; font-size: 14px; color: #6b7280; line-height: 1.4;">
                    ${tip.description}
                </p>
                <div class="tip-actions" style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="onboardingToolkit.hideTooltip()" 
                            style="padding: 6px 12px; border: 1px solid #d1d5db; background: white; 
                                   border-radius: 4px; font-size: 12px; cursor: pointer;">
                        Got it
                    </button>
                    <button onclick="window.location.href='/register'" 
                            style="padding: 6px 12px; background: #3b82f6; color: white; border: none; 
                                   border-radius: 4px; font-size: 12px; cursor: pointer;">
                        Register for More
                    </button>
                </div>
            </div>
        `;
        
        this.positionTooltip(tooltip, target, 'bottom');
        tooltip.style.display = 'block';
    }
    
    startOnboarding() {
        if (!this.userStatus || !this.userStatus.current_step) return;
        
        this.isOnboardingActive = true;
        this.currentStep = this.userStatus.current_step;
        
        // Show current step
        this.showStep(this.currentStep);
    }
    
    async showStep(step) {
        try {
            // Start the step
            await this.startStep(step.step_key);
            
            const content = step.tutorial_content;
            
            if (content.type === 'modal') {
                this.showModal(content.content, step);
            } else if (content.type === 'tooltip') {
                this.showTooltip(content.content, step);
            } else if (content.type === 'highlight') {
                this.highlightElement(content.content, step);
            }
        } catch (error) {
            console.error('Error showing step:', error);
        }
    }
    
    showModal(content, step) {
        const modal = document.getElementById('onboarding-modal');
        const theme = step.theme || 'default';
        
        let themeColors = {
            'default': { bg: '#3b82f6', text: 'white' },
            'success': { bg: '#10b981', text: 'white' },
            'warning': { bg: '#f59e0b', text: 'white' },
            'info': { bg: '#06b6d4', text: 'white' }
        };
        
        const themeColor = themeColors[theme] || themeColors.default;
        
        modal.innerHTML = `
            <div class="onboarding-modal-content" style="
                background: white;
                border-radius: 12px;
                padding: 0;
                max-width: 500px;
                width: 100%;
                box-shadow: 0 25px 50px rgba(0,0,0,0.25);
                animation: onboarding-modal-appear 0.3s ease-out;
            ">
                <div class="modal-header" style="
                    background: ${themeColor.bg};
                    color: ${themeColor.text};
                    padding: 24px;
                    border-radius: 12px 12px 0 0;
                    text-align: center;
                ">
                    <h2 style="margin: 0; font-size: 20px; font-weight: 600;">
                        ${content.title}
                    </h2>
                </div>
                
                <div class="modal-body" style="padding: 24px;">
                    <p style="margin: 0 0 20px 0; font-size: 16px; color: #374151; line-height: 1.6;">
                        ${content.body}
                    </p>
                    
                    ${content.features ? `
                        <div class="features-list" style="margin: 20px 0;">
                            ${content.features.map(feature => `
                                <div style="display: flex; align-items: center; margin: 10px 0; font-size: 14px; color: #4b5563;">
                                    <span style="margin-right: 8px;">${feature}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${content.next_steps ? `
                        <div class="next-steps" style="margin: 20px 0;">
                            <h4 style="margin: 0 0 10px 0; font-size: 16px; color: #1f2937;">What's Next:</h4>
                            ${content.next_steps.map(step => `
                                <div style="margin: 8px 0; padding: 8px 12px; background: #f3f4f6; 
                                           border-radius: 6px; font-size: 14px; color: #4b5563;">
                                    ${step}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                
                <div class="modal-footer" style="
                    padding: 20px 24px;
                    border-top: 1px solid #e5e7eb;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div class="progress-indicator" style="font-size: 12px; color: #6b7280;">
                        Step ${step.sequence_order} of ${this.userStatus.total_steps}
                    </div>
                    
                    <div class="modal-actions" style="display: flex; gap: 12px;">
                        ${content.skip_option ? `
                            <button onclick="onboardingToolkit.skipStep('${step.step_key}')" 
                                    style="padding: 8px 16px; border: 1px solid #d1d5db; background: white; 
                                           border-radius: 6px; font-size: 14px; cursor: pointer;">
                                Skip
                            </button>
                        ` : ''}
                        
                        <button onclick="onboardingToolkit.completeStep('${step.step_key}')" 
                                style="padding: 8px 16px; background: ${themeColor.bg}; color: ${themeColor.text}; 
                                       border: none; border-radius: 6px; font-size: 14px; cursor: pointer;">
                            ${content.cta_text || 'Continue'}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        modal.style.display = 'flex';
        
        // Add animation styles
        this.addAnimationStyles();
    }
    
    showTooltip(content, step) {
        const target = document.querySelector(step.target_selector);
        if (!target) {
            console.warn('Target element not found:', step.target_selector);
            return;
        }
        
        const tooltip = document.getElementById('onboarding-tooltip');
        
        tooltip.innerHTML = `
            <div class="onboarding-tooltip-content">
                <div class="tooltip-header" style="margin-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #1f2937;">
                        ${content.title}
                    </h3>
                </div>
                
                <div class="tooltip-body" style="margin-bottom: 16px;">
                    <p style="margin: 0 0 12px 0; font-size: 14px; color: #4b5563; line-height: 1.4;">
                        ${content.body}
                    </p>
                    
                    ${content.tip ? `
                        <div class="tooltip-tip" style="
                            background: #f0f9ff;
                            border: 1px solid #0ea5e9;
                            border-radius: 4px;
                            padding: 8px;
                            margin: 8px 0;
                        ">
                            <div style="font-size: 12px; color: #0369a1;">
                                💡 ${content.tip}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${content.strategies ? `
                        <div class="strategies-list" style="margin: 12px 0;">
                            ${Object.entries(content.strategies).map(([key, value]) => `
                                <div style="margin: 6px 0; font-size: 13px;">
                                    <strong style="color: #1f2937;">${key}:</strong> 
                                    <span style="color: #6b7280;">${value}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                
                <div class="tooltip-actions" style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="progress-dots" style="display: flex; gap: 4px;">
                        ${Array.from({length: this.userStatus.total_steps}, (_, i) => `
                            <div style="width: 6px; height: 6px; border-radius: 50%; 
                                        background: ${i < step.sequence_order ? '#3b82f6' : '#e5e7eb'};"></div>
                        `).join('')}
                    </div>
                    
                    <div class="action-buttons" style="display: flex; gap: 8px;">
                        <button onclick="onboardingToolkit.skipStep('${step.step_key}')" 
                                style="padding: 6px 12px; border: 1px solid #d1d5db; background: white; 
                                       border-radius: 4px; font-size: 12px; cursor: pointer;">
                            Skip
                        </button>
                        <button onclick="onboardingToolkit.completeStep('${step.step_key}')" 
                                style="padding: 6px 12px; background: #3b82f6; color: white; border: none; 
                                       border-radius: 4px; font-size: 12px; cursor: pointer;">
                            Got it
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.positionTooltip(tooltip, target, step.position || 'bottom');
        tooltip.style.display = 'block';
        
        // Highlight the target element
        this.highlightTargetElement(target);
    }
    
    highlightElement(content, step) {
        const target = document.querySelector(step.target_selector);
        if (!target) return;
        
        // Create spotlight effect
        this.createSpotlight(target);
        
        // Show tooltip alongside highlight
        this.showTooltip(content, step);
    }
    
    createSpotlight(target) {
        const spotlight = document.getElementById('onboarding-spotlight');
        const rect = target.getBoundingClientRect();
        
        spotlight.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 9998;
            display: block;
            pointer-events: none;
        `;
        
        // Create hole in spotlight
        const hole = `
            radial-gradient(circle at ${rect.left + rect.width/2}px ${rect.top + rect.height/2}px, 
                          transparent ${Math.max(rect.width, rect.height)/2 + 10}px, 
                          rgba(0,0,0,0.7) ${Math.max(rect.width, rect.height)/2 + 15}px)
        `;
        
        spotlight.style.background = hole;
    }
    
    highlightTargetElement(target) {
        // Add highlight class
        target.classList.add('onboarding-highlight');
        
        // Add highlight styles if not already present
        if (!document.getElementById('onboarding-highlight-styles')) {
            const style = document.createElement('style');
            style.id = 'onboarding-highlight-styles';
            style.textContent = `
                .onboarding-highlight {
                    position: relative;
                    animation: onboarding-pulse 2s infinite;
                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3) !important;
                    border-radius: 6px !important;
                }
                
                @keyframes onboarding-pulse {
                    0% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3); }
                    50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.2); }
                    100% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3); }
                }
                
                @keyframes onboarding-modal-appear {
                    from {
                        opacity: 0;
                        transform: translateY(-20px) scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    positionTooltip(tooltip, target, position) {
        const rect = target.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top - tooltipRect.height - 10;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = rect.bottom + 10;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 10;
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 10;
                break;
            default:
                top = rect.bottom + 10;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
        }
        
        // Keep tooltip within viewport
        const padding = 10;
        top = Math.max(padding, Math.min(top, window.innerHeight - tooltipRect.height - padding));
        left = Math.max(padding, Math.min(left, window.innerWidth - tooltipRect.width - padding));
        
        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
    }
    
    async startStep(stepKey) {
        try {
            const response = await fetch('/api/onboarding/start-step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    step_key: stepKey
                })
            });
            
            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error starting step:', error);
            return false;
        }
    }
    
    async completeStep(stepKey) {
        try {
            const response = await fetch('/api/onboarding/complete-step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    step_key: stepKey,
                    interaction_data: {
                        completed_at: new Date().toISOString(),
                        user_agent: navigator.userAgent,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        }
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideAllOverlays();
                this.removeHighlights();
                
                // Show next step if available
                if (data.next_step) {
                    setTimeout(() => {
                        this.showStep(data.next_step);
                    }, 1000);
                } else {
                    // Onboarding complete
                    this.isOnboardingActive = false;
                    this.showCompletionCelebration();
                }
            }
            
            return data.success;
        } catch (error) {
            console.error('Error completing step:', error);
            return false;
        }
    }
    
    async skipStep(stepKey) {
        try {
            const response = await fetch('/api/onboarding/skip-step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    step_key: stepKey
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideAllOverlays();
                this.removeHighlights();
                
                // Show next step if available
                if (data.next_step) {
                    setTimeout(() => {
                        this.showStep(data.next_step);
                    }, 500);
                } else {
                    this.isOnboardingActive = false;
                }
            }
            
            return data.success;
        } catch (error) {
            console.error('Error skipping step:', error);
            return false;
        }
    }
    
    hideAllOverlays() {
        document.getElementById('onboarding-tooltip').style.display = 'none';
        document.getElementById('onboarding-modal').style.display = 'none';
        document.getElementById('onboarding-spotlight').style.display = 'none';
    }
    
    hideTooltip() {
        document.getElementById('onboarding-tooltip').style.display = 'none';
        this.removeHighlights();
    }
    
    removeHighlights() {
        const highlighted = document.querySelectorAll('.onboarding-highlight');
        highlighted.forEach(el => el.classList.remove('onboarding-highlight'));
    }
    
    showCompletionCelebration() {
        const modal = document.getElementById('onboarding-modal');
        
        modal.innerHTML = `
            <div class="completion-celebration" style="
                background: white;
                border-radius: 12px;
                padding: 40px;
                max-width: 400px;
                text-align: center;
                box-shadow: 0 25px 50px rgba(0,0,0,0.25);
                animation: onboarding-modal-appear 0.3s ease-out;
            ">
                <div class="celebration-icon" style="font-size: 48px; margin-bottom: 20px;">
                    🎉
                </div>
                <h2 style="margin: 0 0 16px 0; font-size: 24px; color: #1f2937;">
                    Onboarding Complete!
                </h2>
                <p style="margin: 0 0 24px 0; font-size: 16px; color: #6b7280; line-height: 1.5;">
                    You're now ready to analyze real estate deals like a professional investor.
                </p>
                <button onclick="onboardingToolkit.hideAllOverlays()" 
                        style="padding: 12px 24px; background: #10b981; color: white; border: none; 
                               border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: 600;">
                    Start Analyzing Deals
                </button>
            </div>
        `;
        
        modal.style.display = 'flex';
    }
    
    addAnimationStyles() {
        if (!document.getElementById('onboarding-animations')) {
            const style = document.createElement('style');
            style.id = 'onboarding-animations';
            style.textContent = `
                @keyframes onboarding-modal-appear {
                    from {
                        opacity: 0;
                        transform: translateY(-20px) scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
                
                @keyframes onboarding-pulse {
                    0% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3); }
                    50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.2); }
                    100% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3); }
                }
                
                .onboarding-highlight {
                    position: relative;
                    animation: onboarding-pulse 2s infinite;
                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3) !important;
                    border-radius: 6px !important;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    async triggerEvent(eventType, eventData = {}) {
        try {
            const response = await fetch('/api/onboarding/trigger-event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_type: eventType,
                    event_data: eventData
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.triggered_steps.length > 0) {
                // Show triggered steps
                for (const step of data.triggered_steps) {
                    setTimeout(() => {
                        this.showStep(step);
                    }, step.delay_seconds * 1000);
                }
            }
            
            return data.success;
        } catch (error) {
            console.error('Error triggering event:', error);
            return false;
        }
    }
    
    // Utility methods for manual control
    async restartOnboarding() {
        try {
            const response = await fetch('/api/onboarding/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideAllOverlays();
                this.removeHighlights();
                
                // Restart onboarding
                setTimeout(() => {
                    this.checkOnboardingStatus();
                }, 1000);
            }
            
            return data.success;
        } catch (error) {
            console.error('Error restarting onboarding:', error);
            return false;
        }
    }
    
    stopOnboarding() {
        this.isOnboardingActive = false;
        this.hideAllOverlays();
        this.removeHighlights();
    }
}

// Initialize the onboarding toolkit when the page loads
let onboardingToolkit;

document.addEventListener('DOMContentLoaded', function() {
    onboardingToolkit = new OnboardingToolkit();
    
    // Make it globally accessible
    window.onboardingToolkit = onboardingToolkit;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OnboardingToolkit;
}