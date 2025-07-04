/**
 * Cookie Consent Manager
 * GDPR/CCPA compliant cookie consent functionality
 */

class CookieConsent {
    constructor() {
        this.cookieName = 'biped_cookie_consent';
        this.consentTypes = {
            necessary: true,  // Always true
            functional: false,
            analytics: false,
            marketing: false
        };
        this.init();
    }

    init() {
        // Check if consent already given
        const existingConsent = this.getConsent();
        if (!existingConsent) {
            this.showConsentBanner();
        } else {
            this.consentTypes = { ...this.consentTypes, ...existingConsent };
            this.loadConsentedScripts();
        }
    }

    showConsentBanner() {
        const banner = this.createBanner();
        document.body.appendChild(banner);
        
        // Animate in
        setTimeout(() => {
            banner.classList.add('translate-y-0');
            banner.classList.remove('translate-y-full');
        }, 100);
    }

    createBanner() {
        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.className = 'fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 shadow-lg z-50 transform translate-y-full transition-transform duration-300';
        
        banner.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">Cookie Preferences</h3>
                        <p class="text-gray-600 text-sm">
                            We use cookies to enhance your experience, analyze usage, and provide personalized content. 
                            You can customize your preferences or accept all cookies.
                            <a href="/privacy" class="text-blue-600 hover:underline ml-1">Learn more</a>
                        </p>
                    </div>
                    <div class="flex flex-col sm:flex-row gap-2 min-w-max">
                        <button id="cookie-settings-btn" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm">
                            Customize
                        </button>
                        <button id="cookie-reject-btn" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm">
                            Reject All
                        </button>
                        <button id="cookie-accept-btn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
                            Accept All
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Bind events
        banner.querySelector('#cookie-accept-btn').addEventListener('click', () => {
            this.acceptAll();
        });

        banner.querySelector('#cookie-reject-btn').addEventListener('click', () => {
            this.rejectAll();
        });

        banner.querySelector('#cookie-settings-btn').addEventListener('click', () => {
            this.showSettings();
        });

        return banner;
    }

    showSettings() {
        const modal = this.createSettingsModal();
        document.body.appendChild(modal);
        
        // Show modal
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            modal.querySelector('.modal-content').classList.remove('scale-95');
            modal.querySelector('.modal-content').classList.add('scale-100');
        }, 10);
    }

    createSettingsModal() {
        const modal = document.createElement('div');
        modal.id = 'cookie-settings-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 opacity-0 transition-opacity duration-300';
        
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 transform scale-95 transition-transform duration-300">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h2 class="text-xl font-semibold text-gray-900">Cookie Preferences</h2>
                </div>
                <div class="px-6 py-4 max-h-96 overflow-y-auto">
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="font-medium text-gray-900">Necessary Cookies</h3>
                                <p class="text-sm text-gray-600">Required for the website to function properly</p>
                            </div>
                            <div class="toggle-switch opacity-50">
                                <input type="checkbox" id="necessary" checked disabled>
                                <span class="toggle-slider"></span>
                            </div>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="font-medium text-gray-900">Functional Cookies</h3>
                                <p class="text-sm text-gray-600">Remember your preferences and settings</p>
                            </div>
                            <div class="toggle-switch">
                                <input type="checkbox" id="functional" ${this.consentTypes.functional ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </div>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="font-medium text-gray-900">Analytics Cookies</h3>
                                <p class="text-sm text-gray-600">Help us understand how you use our website</p>
                            </div>
                            <div class="toggle-switch">
                                <input type="checkbox" id="analytics" ${this.consentTypes.analytics ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </div>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="font-medium text-gray-900">Marketing Cookies</h3>
                                <p class="text-sm text-gray-600">Personalize content and ads based on your interests</p>
                            </div>
                            <div class="toggle-switch">
                                <input type="checkbox" id="marketing" ${this.consentTypes.marketing ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-2">
                    <button id="modal-cancel-btn" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                        Cancel
                    </button>
                    <button id="modal-save-btn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        Save Preferences
                    </button>
                </div>
            </div>
        `;

        // Bind events
        modal.querySelector('#modal-cancel-btn').addEventListener('click', () => {
            this.closeModal(modal);
        });

        modal.querySelector('#modal-save-btn').addEventListener('click', () => {
            this.saveCustomPreferences(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(modal);
            }
        });

        return modal;
    }

    saveCustomPreferences(modal) {
        this.consentTypes = {
            necessary: true,
            functional: modal.querySelector('#functional').checked,
            analytics: modal.querySelector('#analytics').checked,
            marketing: modal.querySelector('#marketing').checked
        };

        this.saveConsent();
        this.loadConsentedScripts();
        this.closeModal(modal);
        this.hideBanner();
    }

    acceptAll() {
        this.consentTypes = {
            necessary: true,
            functional: true,
            analytics: true,
            marketing: true
        };
        this.saveConsent();
        this.loadConsentedScripts();
        this.hideBanner();
    }

    rejectAll() {
        this.consentTypes = {
            necessary: true,
            functional: false,
            analytics: false,
            marketing: false
        };
        this.saveConsent();
        this.hideBanner();
    }

    saveConsent() {
        const consent = {
            ...this.consentTypes,
            timestamp: new Date().getTime(),
            version: '1.0'
        };
        localStorage.setItem(this.cookieName, JSON.stringify(consent));
    }

    getConsent() {
        try {
            const consent = localStorage.getItem(this.cookieName);
            return consent ? JSON.parse(consent) : null;
        } catch (e) {
            return null;
        }
    }

    loadConsentedScripts() {
        // Load analytics if consented
        if (this.consentTypes.analytics) {
            this.loadAnalytics();
        }

        // Load marketing scripts if consented
        if (this.consentTypes.marketing) {
            this.loadMarketing();
        }
    }

    loadAnalytics() {
        // Example: Google Analytics
        console.log('Loading analytics scripts...');
        // Implementation would go here
    }

    loadMarketing() {
        // Example: Marketing pixels
        console.log('Loading marketing scripts...');
        // Implementation would go here
    }

    hideBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.classList.add('translate-y-full');
            banner.classList.remove('translate-y-0');
            setTimeout(() => {
                banner.remove();
            }, 300);
        }
    }

    closeModal(modal) {
        modal.classList.add('opacity-0');
        modal.querySelector('.modal-content').classList.remove('scale-100');
        modal.querySelector('.modal-content').classList.add('scale-95');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }

    // Public method to check consent
    hasConsent(type) {
        return this.consentTypes[type] || false;
    }

    // Public method to revoke consent
    revokeConsent() {
        localStorage.removeItem(this.cookieName);
        location.reload();
    }
}

// CSS for toggle switches
const toggleCSS = `
.toggle-switch {
    position: relative;
    display: inline-block;
    width: 48px;
    height: 24px;
}

.toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .3s;
    border-radius: 24px;
}

.toggle-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .3s;
    border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
    background-color: #2563eb;
}

.toggle-switch input:checked + .toggle-slider:before {
    transform: translateX(24px);
}

.toggle-switch.opacity-50 .toggle-slider {
    opacity: 0.5;
    cursor: not-allowed;
}
`;

// Add CSS to document
const style = document.createElement('style');
style.textContent = toggleCSS;
document.head.appendChild(style);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cookieConsent = new CookieConsent();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CookieConsent;
}