// Authentication functionality for Biped platform

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        // Check if user is already logged in
        this.checkAuthStatus();
        
        // Bind form events
        this.bindEvents();
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/me', {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.updateUI();
                this.redirectToDashboard();
            }
        } catch (error) {
            console.log('Not authenticated');
        }
    }

    bindEvents() {
        // Login form
        const loginForm = document.querySelector('#loginModal form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Signup form
        const signupForm = document.querySelector('#signupModal form');
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignup(e));
        }

        // Job posting form
        const jobForm = document.querySelector('#jobModal form');
        if (jobForm) {
            jobForm.addEventListener('submit', (e) => this.handleJobPost(e));
        }

        // User type selection in signup
        const userTypeButtons = document.querySelectorAll('#signupModal .grid button');
        userTypeButtons.forEach((button, index) => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectUserType(index === 0 ? 'customer' : 'provider');
            });
        });
    }

    selectUserType(type) {
        // Update UI to show selected user type
        const buttons = document.querySelectorAll('#signupModal .grid button');
        buttons.forEach((btn, index) => {
            if ((index === 0 && type === 'customer') || (index === 1 && type === 'provider')) {
                btn.classList.add('btn-primary');
                btn.classList.remove('btn-secondary');
            } else {
                btn.classList.add('btn-secondary');
                btn.classList.remove('btn-primary');
            }
        });

        // Store selected type
        this.selectedUserType = type;

        // Update form fields based on user type
        this.updateSignupForm(type);
    }

    updateSignupForm(type) {
        const form = document.querySelector('#signupModal form');
        
        // Remove existing dynamic fields
        const dynamicFields = form.querySelectorAll('.dynamic-field');
        dynamicFields.forEach(field => field.remove());

        if (type === 'provider') {
            // Add provider-specific fields
            const providerFields = `
                <div class="dynamic-field mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Business Name</label>
                    <input type="text" name="business_name" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                </div>
                <div class="dynamic-field mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                    <input type="tel" name="phone" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                </div>
                <div class="dynamic-field mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Years of Experience</label>
                    <select name="years_experience" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        <option value="">Select experience</option>
                        <option value="1">1-2 years</option>
                        <option value="3">3-5 years</option>
                        <option value="6">6-10 years</option>
                        <option value="11">10+ years</option>
                    </select>
                </div>
            `;
            
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.insertAdjacentHTML('beforebegin', providerFields);
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const email = form.querySelector('input[type="email"]').value;
        const password = form.querySelector('input[type="password"]').value;

        if (!email || !password) {
            this.showError('Please fill in all fields');
            return;
        }

        this.showLoading('Signing in...');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentUser = data.user;
                this.hideLoading();
                this.showSuccess('Login successful!');
                hideModal('loginModal');
                this.updateUI();
                this.redirectToDashboard();
            } else {
                this.hideLoading();
                this.showError(data.error || 'Login failed');
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error. Please try again.');
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const form = e.target;
        const fullName = form.querySelector('input[type="text"]').value;
        const email = form.querySelector('input[type="email"]').value;
        const password = form.querySelector('input[type="password"]').value;

        if (!fullName || !email || !password) {
            this.showError('Please fill in all required fields');
            return;
        }

        if (!this.selectedUserType) {
            this.showError('Please select whether you need services or are a provider');
            return;
        }

        // Split full name
        const nameParts = fullName.trim().split(' ');
        const firstName = nameParts[0];
        const lastName = nameParts.slice(1).join(' ') || '';

        const signupData = {
            first_name: firstName,
            last_name: lastName,
            email: email,
            password: password,
            user_type: this.selectedUserType
        };

        // Add provider-specific fields if applicable
        if (this.selectedUserType === 'provider') {
            const businessName = form.querySelector('input[name="business_name"]')?.value;
            const phone = form.querySelector('input[name="phone"]')?.value;
            const yearsExperience = form.querySelector('select[name="years_experience"]')?.value;

            if (businessName) signupData.business_name = businessName;
            if (phone) signupData.phone = phone;
            if (yearsExperience) signupData.years_experience = parseInt(yearsExperience);
        }

        this.showLoading('Creating account...');

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(signupData)
            });

            const data = await response.json();

            if (response.ok) {
                this.currentUser = data.user;
                this.hideLoading();
                this.showSuccess('Account created successfully!');
                hideModal('signupModal');
                this.updateUI();
                this.redirectToDashboard();
            } else {
                this.hideLoading();
                this.showError(data.error || 'Registration failed');
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error. Please try again.');
        }
    }

    async handleJobPost(e) {
        e.preventDefault();

        // Check if user is logged in
        if (!this.currentUser) {
            hideModal('jobModal');
            this.showError('Please sign in to post a job');
            setTimeout(() => showLoginModal(), 1000);
            return;
        }

        // Check if user is a customer
        if (this.currentUser.user_type !== 'customer') {
            this.showError('Only customers can post jobs');
            return;
        }

        const form = e.target;
        const description = form.querySelector('textarea').value;
        const category = form.querySelector('select').value;
        const budget = form.querySelectorAll('select')[1].value;
        const location = form.querySelector('input[type="text"]').value;
        const timeline = form.querySelectorAll('select')[2].value;

        if (!description || !category || !location) {
            this.showError('Please fill in all required fields');
            return;
        }

        const jobData = {
            title: `${category} Job`,
            description: description,
            category: category,
            budget_range: budget,
            location: location,
            timeline: timeline,
            status: 'open'
        };

        this.showLoading('Posting job...');

        try {
            const response = await fetch('/api/jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(jobData)
            });

            const data = await response.json();

            if (response.ok) {
                this.hideLoading();
                this.showSuccess('Job posted successfully!');
                hideModal('jobModal');
                // Redirect to job management or dashboard
                window.location.href = '/dashboard';
            } else {
                this.hideLoading();
                this.showError(data.error || 'Failed to post job');
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error. Please try again.');
        }
    }

    async logout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });

            if (response.ok) {
                this.currentUser = null;
                this.updateUI();
                this.showSuccess('Logged out successfully');
                window.location.href = '/';
            }
        } catch (error) {
            this.showError('Logout failed');
        }
    }

    updateUI() {
        const signInBtn = document.querySelector('button[onclick="showLoginModal()"]');
        const getStartedBtn = document.querySelector('button[onclick="showSignupModal()"]');

        if (this.currentUser) {
            // User is logged in - show user menu
            if (signInBtn && getStartedBtn) {
                const userMenu = `
                    <div class="flex items-center space-x-4">
                        <span class="text-gray-700">Welcome, ${this.currentUser.first_name}!</span>
                        <button onclick="window.location.href='/dashboard'" class="btn-primary text-white px-4 py-2 rounded-lg font-medium">
                            Dashboard
                        </button>
                        <button onclick="authManager.logout()" class="btn-secondary px-4 py-2 rounded-lg font-medium">
                            Logout
                        </button>
                    </div>
                `;
                signInBtn.parentElement.innerHTML = userMenu;
            }
        }
    }

    redirectToDashboard() {
        // Only redirect if we're on the landing page
        if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        }
    }

    showLoading(message) {
        // Create or update loading overlay
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            document.body.appendChild(overlay);
        }

        overlay.innerHTML = `
            <div class="bg-white p-6 rounded-lg shadow-lg text-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p class="text-gray-700">${message}</p>
            </div>
        `;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});

// Global functions for backward compatibility
function showProviderSignup() {
    showSignupModal();
    // Auto-select provider type
    setTimeout(() => {
        if (window.authManager) {
            window.authManager.selectUserType('provider');
        }
    }, 100);
}

