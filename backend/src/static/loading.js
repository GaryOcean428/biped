// Loading states and UI feedback utilities for TradeHub Platform
class LoadingManager {
    constructor() {
        this.loadingStates = new Map();
        this.createLoadingHTML();
    }

    createLoadingHTML() {
        // Create global loading overlay
        if (!document.getElementById('globalLoadingOverlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'globalLoadingOverlay';
            overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden';
            overlay.innerHTML = `
                <div class="bg-white rounded-lg p-6 flex items-center space-x-3">
                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span class="text-gray-700">Loading...</span>
                </div>
            `;
            document.body.appendChild(overlay);
        }
    }

    // Show loading spinner on button
    showButtonLoading(buttonId, loadingText = 'Loading...') {
        const button = document.getElementById(buttonId);
        if (!button) return;

        // Store original button content
        this.loadingStates.set(buttonId, {
            originalHTML: button.innerHTML,
            originalDisabled: button.disabled
        });

        // Set loading state
        button.disabled = true;
        button.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>${loadingText}</span>
            </div>
        `;
    }

    // Hide loading spinner on button
    hideButtonLoading(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        const originalState = this.loadingStates.get(buttonId);
        if (originalState) {
            button.innerHTML = originalState.originalHTML;
            button.disabled = originalState.originalDisabled;
            this.loadingStates.delete(buttonId);
        }
    }

    // Show loading spinner in container
    showContainerLoading(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Store original content
        this.loadingStates.set(containerId, {
            originalHTML: container.innerHTML
        });

        // Show loading state
        container.innerHTML = `
            <div class="flex items-center justify-center p-8">
                <div class="text-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p class="text-gray-600">${message}</p>
                </div>
            </div>
        `;
    }

    // Hide loading spinner in container
    hideContainerLoading(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const originalState = this.loadingStates.get(containerId);
        if (originalState) {
            container.innerHTML = originalState.originalHTML;
            this.loadingStates.delete(containerId);
        }
    }

    // Show global loading overlay
    showGlobalLoading(message = 'Loading...') {
        const overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            const messageSpan = overlay.querySelector('span');
            if (messageSpan) {
                messageSpan.textContent = message;
            }
            overlay.classList.remove('hidden');
        }
    }

    // Hide global loading overlay
    hideGlobalLoading() {
        const overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    // Show skeleton loading for cards/lists
    showSkeletonLoading(containerId, count = 3) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Store original content
        this.loadingStates.set(containerId, {
            originalHTML: container.innerHTML
        });

        const skeletonHTML = Array(count).fill(0).map(() => `
            <div class="animate-pulse">
                <div class="bg-gray-200 rounded-lg p-4 mb-4">
                    <div class="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                    <div class="h-3 bg-gray-300 rounded w-1/2 mb-2"></div>
                    <div class="h-3 bg-gray-300 rounded w-full"></div>
                </div>
            </div>
        `).join('');

        container.innerHTML = skeletonHTML;
    }

    // Show inline loading spinner
    showInlineLoading(elementId, size = 'small') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const sizeClasses = {
            small: 'h-4 w-4',
            medium: 'h-6 w-6',
            large: 'h-8 w-8'
        };

        const spinner = document.createElement('div');
        spinner.className = `animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size] || sizeClasses.small}`;
        spinner.id = `${elementId}-spinner`;

        element.appendChild(spinner);
    }

    hideInlineLoading(elementId) {
        const spinner = document.getElementById(`${elementId}-spinner`);
        if (spinner) {
            spinner.remove();
        }
    }

    // Progress bar functionality
    showProgressBar(containerId, progress = 0) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const progressBarHTML = `
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                     style="width: ${progress}%" id="${containerId}-progress"></div>
            </div>
        `;

        container.innerHTML = progressBarHTML;
    }

    updateProgressBar(containerId, progress) {
        const progressBar = document.getElementById(`${containerId}-progress`);
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }

    // Form submission loading states
    handleFormSubmission(formId, submitButtonId, loadingText = 'Submitting...') {
        const form = document.getElementById(formId);
        if (!form) return;

        // Show button loading
        this.showButtonLoading(submitButtonId, loadingText);

        // Disable all form inputs
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.disabled = true;
        });

        return () => {
            // Hide button loading
            this.hideButtonLoading(submitButtonId);

            // Re-enable form inputs
            inputs.forEach(input => {
                input.disabled = false;
            });
        };
    }

    // API call with loading states
    async apiCallWithLoading(apiCall, buttonId = null, containerId = null, loadingMessage = 'Loading...') {
        try {
            // Show appropriate loading state
            if (buttonId) {
                this.showButtonLoading(buttonId, loadingMessage);
            } else if (containerId) {
                this.showContainerLoading(containerId, loadingMessage);
            } else {
                this.showGlobalLoading(loadingMessage);
            }

            // Execute API call
            const result = await apiCall();
            return result;

        } catch (error) {
            throw error;
        } finally {
            // Hide loading state
            if (buttonId) {
                this.hideButtonLoading(buttonId);
            } else if (containerId) {
                this.hideContainerLoading(containerId);
            } else {
                this.hideGlobalLoading();
            }
        }
    }

    // Utility to add loading to any async function
    withLoading(asyncFunction, options = {}) {
        return async (...args) => {
            const {
                buttonId,
                containerId,
                message = 'Loading...',
                type = 'global'
            } = options;

            try {
                switch (type) {
                    case 'button':
                        if (buttonId) this.showButtonLoading(buttonId, message);
                        break;
                    case 'container':
                        if (containerId) this.showContainerLoading(containerId, message);
                        break;
                    case 'skeleton':
                        if (containerId) this.showSkeletonLoading(containerId);
                        break;
                    default:
                        this.showGlobalLoading(message);
                }

                return await asyncFunction(...args);
            } finally {
                switch (type) {
                    case 'button':
                        if (buttonId) this.hideButtonLoading(buttonId);
                        break;
                    case 'container':
                        if (containerId) this.hideContainerLoading(containerId);
                        break;
                    case 'skeleton':
                        if (containerId) this.hideContainerLoading(containerId);
                        break;
                    default:
                        this.hideGlobalLoading();
                }
            }
        };
    }
}

// Create global loading manager instance
const loadingManager = new LoadingManager();

// Add CSS for loading animations if not already present
if (!document.getElementById('loadingStyles')) {
    const style = document.createElement('style');
    style.id = 'loadingStyles';
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .animate-spin {
            animation: spin 1s linear infinite;
        }
        
        .animate-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        .loading-disabled {
            pointer-events: none;
            opacity: 0.6;
        }
    `;
    document.head.appendChild(style);
}