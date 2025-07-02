// Biped Frontend JavaScript
class BipedApp {
    constructor() {
        this.apiBase = '/api';
        this.currentUser = null;
        this.currentStep = 1;
        this.quoteData = {};
        this.serviceCategories = [];
        
        this.init();
    }

    async init() {
        await this.loadServiceCategories();
        this.setupEventListeners();
        this.checkAuthStatus();
        this.initializeValidation();
    }
    
    initializeValidation() {
        // Set up real-time validation for forms
        if (typeof formValidator !== 'undefined') {
            formValidator.setupRealTimeValidation('loginForm');
            formValidator.setupRealTimeValidation('signupForm');
        }
    }

    // API Methods
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                credentials: 'include',
                ...options
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'API request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            this.showNotification(error.message, 'error');
            throw error;
        }
    }

    async loadServiceCategories() {
        try {
            const data = await this.apiCall('/services/categories');
            this.serviceCategories = data.categories;
            this.renderServiceCategories();
            this.renderServiceOptions();
        } catch (error) {
            console.error('Failed to load service categories:', error);
        }
    }

    async checkAuthStatus() {
        try {
            const data = await this.apiCall('/auth/me');
            this.currentUser = data.user;
            this.updateAuthUI();
        } catch (error) {
            // User not logged in
            this.currentUser = null;
            this.updateAuthUI();
        }
    }

    async login(email, password) {
        try {
            const data = await this.apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            
            this.currentUser = data.user;
            this.updateAuthUI();
            this.closeModal('loginModal');
            this.showNotification('Login successful!', 'success');
            
            return data;
        } catch (error) {
            throw error;
        }
    }

    async signup(userData) {
        try {
            const data = await this.apiCall('/auth/register', {
                method: 'POST',
                body: JSON.stringify(userData)
            });
            
            this.currentUser = data.user;
            this.updateAuthUI();
            this.closeModal('signupModal');
            this.showNotification('Account created successfully!', 'success');
            
            return data;
        } catch (error) {
            throw error;
        }
    }

    async logout() {
        try {
            await this.apiCall('/auth/logout', { method: 'POST' });
            this.currentUser = null;
            this.updateAuthUI();
            this.showNotification('Logged out successfully', 'success');
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }

    async getPriceEstimate(serviceId, postcode) {
        try {
            const data = await this.apiCall('/services/estimate', {
                method: 'POST',
                body: JSON.stringify({ service_id: serviceId, postcode })
            });
            return data.estimate;
        } catch (error) {
            console.error('Failed to get price estimate:', error);
            return null;
        }
    }

    // UI Methods
    renderServiceCategories() {
        const container = document.getElementById('serviceCategories');
        if (!container) return;

        container.innerHTML = this.serviceCategories.map(category => `
            <div class="card-hover bg-white rounded-lg p-6 text-center cursor-pointer border border-gray-200" 
                 data-category-id="${category.id}">
                <div class="text-3xl mb-3">
                    <i class="fas fa-${this.getIconClass(category.icon)} text-blue-600"></i>
                </div>
                <h3 class="font-semibold text-gray-900">${category.name}</h3>
                <p class="text-sm text-gray-600 mt-1">${category.description}</p>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('[data-category-id]').forEach(card => {
            card.addEventListener('click', () => {
                const categoryId = card.dataset.categoryId;
                this.selectServiceCategory(categoryId);
            });
        });
    }

    renderServiceOptions() {
        const container = document.getElementById('serviceOptions');
        if (!container) return;

        container.innerHTML = this.serviceCategories.map(category => `
            <button class="service-option text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                    data-service-id="${category.id}">
                <div class="flex items-center">
                    <i class="fas fa-${this.getIconClass(category.icon)} text-blue-600 mr-3"></i>
                    <div>
                        <div class="font-medium">${category.name}</div>
                        <div class="text-sm text-gray-600">${category.description}</div>
                    </div>
                </div>
            </button>
        `).join('');
    }

    getIconClass(icon) {
        const iconMap = {
            'wrench': 'wrench',
            'bolt': 'bolt',
            'hammer': 'hammer',
            'paint-brush': 'paint-roller',
            'leaf': 'leaf',
            'sparkles': 'sparkles',
            'home': 'home',
            'square': 'th-large'
        };
        return iconMap[icon] || 'tools';
    }

    selectServiceCategory(categoryId) {
        this.quoteData.serviceId = categoryId;
        this.openModal('quoteModal');
        this.updateQuoteStep(1);
    }

    updateAuthUI() {
        const loginBtn = document.getElementById('loginBtn');
        const signupBtn = document.getElementById('signupBtn');
        
        if (this.currentUser) {
            loginBtn.textContent = this.currentUser.first_name;
            loginBtn.onclick = () => this.showUserMenu();
            signupBtn.textContent = 'Dashboard';
            signupBtn.onclick = () => this.showDashboard();
        } else {
            loginBtn.textContent = 'Login';
            loginBtn.onclick = () => this.openModal('loginModal');
            signupBtn.textContent = 'Sign Up';
            signupBtn.onclick = () => this.openModal('signupModal');
        }
    }

    updateQuoteStep(step) {
        this.currentStep = step;
        
        // Hide all steps
        document.querySelectorAll('.quote-step').forEach(el => el.classList.add('hidden'));
        
        // Show current step
        const currentStepEl = document.getElementById(`quoteStep${step}`);
        if (currentStepEl) {
            currentStepEl.classList.remove('hidden');
        }
        
        // Update progress indicators
        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            indicator.classList.remove('active', 'completed');
            if (index < step - 1) {
                indicator.classList.add('completed');
            } else if (index === step - 1) {
                indicator.classList.add('active');
            }
        });
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prevStep');
        const nextBtn = document.getElementById('nextStep');
        
        prevBtn.classList.toggle('hidden', step === 1);
        
        if (step === 4) {
            nextBtn.textContent = 'Get Started';
        } else {
            nextBtn.textContent = 'Next';
        }
    }

    async handleQuoteNext() {
        switch (this.currentStep) {
            case 1:
                const selectedService = document.querySelector('.service-option.selected');
                if (!selectedService) {
                    this.showNotification('Please select a service', 'error');
                    return;
                }
                this.quoteData.serviceId = selectedService.dataset.serviceId;
                this.updateQuoteStep(2);
                break;
                
            case 2:
                const postcode = document.getElementById('postcodeInput').value.trim();
                if (!postcode) {
                    this.showNotification('Please enter your postcode', 'error');
                    return;
                }
                this.quoteData.postcode = postcode;
                this.updateQuoteStep(3);
                break;
                
            case 3:
                const description = document.getElementById('projectDescription').value.trim();
                if (!description) {
                    this.showNotification('Please describe your project', 'error');
                    return;
                }
                this.quoteData.description = description;
                await this.showPriceEstimate();
                this.updateQuoteStep(4);
                break;
                
            case 4:
                if (this.currentUser) {
                    // Create job posting
                    this.createJobPosting();
                } else {
                    // Show signup modal
                    this.closeModal('quoteModal');
                    this.openModal('signupModal');
                }
                break;
        }
    }

    async showPriceEstimate() {
        const container = document.getElementById('priceEstimate');
        if (!container) return;

        container.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i></div>';

        try {
            const estimate = await this.getPriceEstimate(this.quoteData.serviceId, this.quoteData.postcode);
            
            if (estimate) {
                container.innerHTML = `
                    <div class="text-center">
                        <h4 class="text-2xl font-bold text-gray-900 mb-2">Estimated Cost</h4>
                        <div class="text-3xl font-bold text-blue-600 mb-2">
                            $${estimate.min_price || 'N/A'} - $${estimate.max_price || 'N/A'}
                        </div>
                        <p class="text-gray-600">
                            Based on ${estimate.provider_count} local professionals
                        </p>
                        ${estimate.typical_duration_hours ? `
                            <p class="text-sm text-gray-500 mt-2">
                                Typical duration: ${estimate.typical_duration_hours} hours
                            </p>
                        ` : ''}
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="text-center">
                        <h4 class="text-xl font-bold text-gray-900 mb-2">Get Custom Quotes</h4>
                        <p class="text-gray-600">
                            Connect with local professionals to get personalized quotes for your project.
                        </p>
                    </div>
                `;
            }
        } catch (error) {
            container.innerHTML = `
                <div class="text-center">
                    <h4 class="text-xl font-bold text-gray-900 mb-2">Get Custom Quotes</h4>
                    <p class="text-gray-600">
                        Connect with local professionals to get personalized quotes for your project.
                    </p>
                </div>
            `;
        }
    }

    setupEventListeners() {
        // Quote flow
        document.getElementById('getQuoteBtn')?.addEventListener('click', () => {
            const searchTerm = document.getElementById('serviceSearch').value.trim();
            if (searchTerm) {
                this.quoteData.searchTerm = searchTerm;
                this.openModal('quoteModal');
                this.updateQuoteStep(1);
            } else {
                this.showNotification('Please enter a service you need', 'error');
            }
        });

        // Service search
        document.getElementById('serviceSearch')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('getQuoteBtn').click();
            }
        });

        // Quote modal navigation
        document.getElementById('nextStep')?.addEventListener('click', () => {
            this.handleQuoteNext();
        });

        document.getElementById('prevStep')?.addEventListener('click', () => {
            if (this.currentStep > 1) {
                this.updateQuoteStep(this.currentStep - 1);
            }
        });

        // Service option selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.service-option')) {
                document.querySelectorAll('.service-option').forEach(el => el.classList.remove('selected', 'border-blue-500', 'bg-blue-50'));
                const option = e.target.closest('.service-option');
                option.classList.add('selected', 'border-blue-500', 'bg-blue-50');
            }
        });

        // Modal controls
        document.getElementById('closeModal')?.addEventListener('click', () => {
            this.closeModal('quoteModal');
        });

        document.getElementById('closeLoginModal')?.addEventListener('click', () => {
            this.closeModal('loginModal');
        });

        document.getElementById('closeSignupModal')?.addEventListener('click', () => {
            this.closeModal('signupModal');
        });

        // Auth forms
        document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                email: document.getElementById('loginEmail').value,
                password: document.getElementById('loginPassword').value
            };
            
            // Validate form data
            const validation = formValidator.validateLoginForm(formData);
            if (!validation.valid) {
                // Show validation errors
                Object.keys(validation.errors).forEach(field => {
                    const fieldId = field === 'email' ? 'loginEmail' : 'loginPassword';
                    formValidator.showFieldError(fieldId, validation.errors[field]);
                });
                return;
            }
            
            // Clear any existing errors
            formValidator.clearFieldErrors('loginForm');
            
            try {
                // Use loading manager for form submission
                const resetLoading = loadingManager.handleFormSubmission('loginForm', 'loginBtn', 'Signing in...');
                
                await this.login(formData.email, formData.password);
                
                resetLoading();
            } catch (error) {
                // Error already shown by apiCall
                const resetLoading = loadingManager.handleFormSubmission('loginForm', 'loginBtn');
                resetLoading();
            }
        });

        document.getElementById('signupForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const userData = {
                firstName: document.getElementById('firstName').value,
                lastName: document.getElementById('lastName').value,
                email: document.getElementById('signupEmail').value,
                password: document.getElementById('signupPassword').value,
                userType: document.getElementById('customerTab').classList.contains('border-blue-600') ? 'customer' : 'provider'
            };
            
            // Validate registration form
            const validation = formValidator.validateRegistrationForm(userData);
            if (!validation.valid) {
                // Show validation errors
                Object.keys(validation.errors).forEach(field => {
                    formValidator.showFieldError(field, validation.errors[field]);
                });
                return;
            }
            
            // Clear any existing errors
            formValidator.clearFieldErrors('signupForm');
            
            // Convert to backend format
            const backendData = {
                first_name: userData.firstName,
                last_name: userData.lastName,
                email: userData.email,
                password: userData.password,
                user_type: userData.userType
            };
            
            try {
                // Use loading manager for form submission
                const resetLoading = loadingManager.handleFormSubmission('signupForm', 'signupBtn', 'Creating account...');
                
                await this.signup(backendData);
                
                resetLoading();
            } catch (error) {
                // Error already shown by apiCall
                const resetLoading = loadingManager.handleFormSubmission('signupForm', 'signupBtn');
                resetLoading();
            }
        });

        // Tab switching
        document.getElementById('customerTab')?.addEventListener('click', () => {
            this.switchTab('customer');
        });

        document.getElementById('providerTab')?.addEventListener('click', () => {
            this.switchTab('provider');
        });

        // Modal switching
        document.getElementById('switchToSignup')?.addEventListener('click', () => {
            this.closeModal('loginModal');
            this.openModal('signupModal');
        });

        document.getElementById('switchToLogin')?.addEventListener('click', () => {
            this.closeModal('signupModal');
            this.openModal('loginModal');
        });

        // Close modals on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('show');
            }
        });
    }

    switchTab(type) {
        const customerTab = document.getElementById('customerTab');
        const providerTab = document.getElementById('providerTab');
        
        if (type === 'customer') {
            customerTab.classList.add('border-blue-600', 'text-blue-600');
            customerTab.classList.remove('border-gray-200', 'text-gray-600');
            providerTab.classList.add('border-gray-200', 'text-gray-600');
            providerTab.classList.remove('border-blue-600', 'text-blue-600');
        } else {
            providerTab.classList.add('border-blue-600', 'text-blue-600');
            providerTab.classList.remove('border-gray-200', 'text-gray-600');
            customerTab.classList.add('border-gray-200', 'text-gray-600');
            customerTab.classList.remove('border-blue-600', 'text-blue-600');
        }
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = 'auto';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    showUserMenu() {
        // Simple implementation - could be expanded
        if (confirm('Would you like to logout?')) {
            this.logout();
        }
    }

    showDashboard() {
        // Redirect to dashboard or show dashboard modal
        this.showNotification('Dashboard feature coming soon!', 'info');
    }

    async createJobPosting() {
        try {
            const jobData = {
                service_id: this.quoteData.serviceId,
                title: `${this.serviceCategories.find(c => c.id == this.quoteData.serviceId)?.name} Service`,
                description: this.quoteData.description,
                street_address: 'TBD',
                city: 'TBD',
                state: 'TBD',
                postcode: this.quoteData.postcode
            };

            const result = await this.apiCall('/jobs/', {
                method: 'POST',
                body: JSON.stringify(jobData)
            });

            this.closeModal('quoteModal');
            this.showNotification('Job posted successfully! You will receive quotes soon.', 'success');
            
        } catch (error) {
            console.error('Failed to create job posting:', error);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.bipedApp = new BipedApp();
});

