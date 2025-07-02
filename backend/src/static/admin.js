// Admin Dashboard JavaScript
class AdminDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.isAuthenticated = false;
        this.adminToken = localStorage.getItem('adminToken');
        this.init();
    }

    async init() {
        // Check authentication
        if (!this.adminToken) {
            this.showLoginForm();
            return;
        }

        // Verify token
        const isValid = await this.verifyToken();
        if (!isValid) {
            this.showLoginForm();
            return;
        }

        this.isAuthenticated = true;
        this.setupEventListeners();
        this.loadDashboardData();
        this.initCharts();
    }

    async verifyToken() {
        try {
            const response = await fetch('/api/admin/verify', {
                headers: {
                    'Authorization': `Bearer ${this.adminToken}`,
                    'Content-Type': 'application/json'
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Token verification failed:', error);
            return false;
        }
    }

    showLoginForm() {
        // Create login overlay
        const loginOverlay = document.createElement('div');
        loginOverlay.id = 'loginOverlay';
        loginOverlay.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
        loginOverlay.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
                <div class="text-center mb-6">
                    <h2 class="text-2xl font-bold text-gray-900">Admin Login</h2>
                    <p class="text-gray-600">Please sign in to access the admin dashboard</p>
                </div>
                <form id="adminLoginForm">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Username</label>
                            <input type="text" id="adminUsername" required
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                            <input type="password" id="adminPassword" required
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                        </div>
                        <button type="submit" class="w-full btn-primary text-white py-3 rounded-md font-medium">
                            Sign In
                        </button>
                    </div>
                </form>
                <div id="loginError" class="mt-4 text-red-600 text-sm hidden"></div>
            </div>
        `;
        document.body.appendChild(loginOverlay);

        // Handle login form
        document.getElementById('adminLoginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLogin();
        });
    }

    async handleLogin() {
        const username = document.getElementById('adminUsername').value;
        const password = document.getElementById('adminPassword').value;
        const errorDiv = document.getElementById('loginError');

        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.adminToken = data.token;
                localStorage.setItem('adminToken', this.adminToken);
                document.getElementById('loginOverlay').remove();
                this.isAuthenticated = true;
                this.setupEventListeners();
                this.loadDashboardData();
                this.initCharts();
            } else {
                errorDiv.textContent = data.error || 'Login failed';
                errorDiv.classList.remove('hidden');
            }
        } catch (error) {
            errorDiv.textContent = 'Network error. Please try again.';
            errorDiv.classList.remove('hidden');
        }
    }

    setupEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.showSection(section);
            });
        });

        // Sidebar toggle
        document.getElementById('sidebarToggle')?.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('-translate-x-full');
        });

        // Profile dropdown
        document.getElementById('profileBtn')?.addEventListener('click', () => {
            const dropdown = document.getElementById('profileDropdown');
            dropdown.classList.toggle('hidden');
        });

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.logout();
        });

        // Form submissions
        document.getElementById('addUserForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addUser();
        });

        document.getElementById('addServiceForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addService();
        });

        // Search and filters
        document.getElementById('userSearch')?.addEventListener('input', () => {
            this.filterUsers();
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#profileBtn')) {
                document.getElementById('profileDropdown')?.classList.add('hidden');
            }
        });
    }

    showSection(sectionName) {
        // Update sidebar active state
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`)?.classList.add('active');

        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected section
        document.getElementById(`${sectionName}Section`)?.classList.remove('hidden');
        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(section) {
        switch (section) {
            case 'users':
                await this.loadUsers();
                break;
            case 'services':
                await this.loadServices();
                break;
            case 'jobs':
                await this.loadJobs();
                break;
            case 'payments':
                await this.loadPayments();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
        }
    }

    async loadDashboardData() {
        try {
            const response = await this.apiCall('/api/admin/analytics/dashboard');
            const data = response;

            // Update stats cards
            document.getElementById('totalUsers').textContent = data.total_users || 0;
            document.getElementById('activeJobs').textContent = data.active_jobs || 0;
            document.getElementById('totalRevenue').textContent = `$${(data.total_revenue || 0).toLocaleString()}`;
            document.getElementById('platformFee').textContent = `$${(data.platform_fees || 0).toLocaleString()}`;

            // Update growth percentages
            document.getElementById('userGrowth').textContent = `${data.user_growth || 0}%`;
            document.getElementById('jobGrowth').textContent = `${data.job_growth || 0}%`;
            document.getElementById('revenueGrowth').textContent = `${data.revenue_growth || 0}%`;
            document.getElementById('feeGrowth').textContent = `${data.fee_growth || 0}%`;

            // Update sidebar counts
            document.getElementById('userCount').textContent = data.total_users || 0;
            document.getElementById('serviceCount').textContent = data.total_services || 0;
            document.getElementById('jobCount').textContent = data.active_jobs || 0;
            document.getElementById('paymentCount').textContent = data.total_payments || 0;

            // Load recent activity
            this.loadRecentActivity(data.recent_activity || []);

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    loadRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!activities.length) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent activity</p>';
            return;
        }

        container.innerHTML = activities.map(activity => `
            <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-${this.getActivityIcon(activity.type)} text-blue-600 text-sm"></i>
                    </div>
                </div>
                <div class="flex-1">
                    <p class="text-sm text-gray-900">${activity.description}</p>
                    <p class="text-xs text-gray-500">${this.formatDate(activity.created_at)}</p>
                </div>
            </div>
        `).join('');
    }

    getActivityIcon(type) {
        const icons = {
            'user_registered': 'user-plus',
            'job_created': 'briefcase',
            'payment_received': 'credit-card',
            'service_added': 'tools',
            'admin_action': 'shield-alt'
        };
        return icons[type] || 'info-circle';
    }

    async loadUsers() {
        try {
            const response = await this.apiCall('/api/admin/users');
            const users = response.users || [];
            this.renderUsersTable(users);
        } catch (error) {
            console.error('Failed to load users:', error);
            this.showNotification('Failed to load users', 'error');
        }
    }

    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!users.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No users found</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <i class="fas fa-user text-gray-600"></i>
                            </div>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${user.full_name || 'N/A'}</div>
                            <div class="text-sm text-gray-500">${user.email}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.user_type === 'provider' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}">
                        ${user.user_type || 'customer'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge status-${user.status || 'active'}">${user.status || 'active'}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${this.formatDate(user.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="adminDashboard.editUser(${user.id})" class="text-blue-600 hover:text-blue-900 mr-3">Edit</button>
                    <button onclick="adminDashboard.suspendUser(${user.id})" class="text-red-600 hover:text-red-900">Suspend</button>
                </td>
            </tr>
        `).join('');
    }

    async loadServices() {
        try {
            const response = await this.apiCall('/api/admin/services');
            const services = response.services || [];
            this.renderServicesGrid(services);
        } catch (error) {
            console.error('Failed to load services:', error);
            this.showNotification('Failed to load services', 'error');
        }
    }

    renderServicesGrid(services) {
        const grid = document.getElementById('servicesGrid');
        if (!services.length) {
            grid.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">No services found</div>';
            return;
        }

        grid.innerHTML = services.map(service => `
            <div class="bg-white rounded-lg shadow-sm p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">${service.name}</h3>
                    <div class="flex space-x-2">
                        <button onclick="adminDashboard.editService(${service.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="adminDashboard.deleteService(${service.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <p class="text-gray-600 text-sm mb-3">${service.description || 'No description'}</p>
                <div class="flex justify-between items-center">
                    <span class="text-lg font-bold text-green-600">$${service.base_price || 0}</span>
                    <span class="text-sm text-gray-500">${service.category || 'General'}</span>
                </div>
                <div class="mt-3 text-xs text-gray-500">
                    ${service.provider_count || 0} providers
                </div>
            </div>
        `).join('');
    }

    async loadJobs() {
        try {
            const response = await this.apiCall('/api/admin/jobs');
            const jobs = response.jobs || [];
            this.renderJobsTable(jobs);
        } catch (error) {
            console.error('Failed to load jobs:', error);
            this.showNotification('Failed to load jobs', 'error');
        }
    }

    renderJobsTable(jobs) {
        const tbody = document.getElementById('jobsTableBody');
        if (!jobs.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-500">No jobs found</td></tr>';
            return;
        }

        tbody.innerHTML = jobs.map(job => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">${job.title}</div>
                    <div class="text-sm text-gray-500">${job.description?.substring(0, 50)}...</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${job.customer_name || 'N/A'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${job.provider_name || 'Unassigned'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    $${job.budget || 0}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge status-${job.status || 'pending'}">${job.status || 'pending'}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="adminDashboard.viewJob(${job.id})" class="text-blue-600 hover:text-blue-900 mr-3">View</button>
                    <button onclick="adminDashboard.moderateJob(${job.id})" class="text-yellow-600 hover:text-yellow-900">Moderate</button>
                </td>
            </tr>
        `).join('');
    }

    async loadPayments() {
        try {
            const response = await this.apiCall('/api/admin/payments');
            const payments = response.payments || [];
            const stats = response.stats || {};
            
            // Update payment stats
            document.getElementById('totalProcessed').textContent = `$${(stats.total_processed || 0).toLocaleString()}`;
            document.getElementById('pendingEscrow').textContent = `$${(stats.pending_escrow || 0).toLocaleString()}`;
            document.getElementById('totalFees').textContent = `$${(stats.total_fees || 0).toLocaleString()}`;
            
            this.renderPaymentsTable(payments);
        } catch (error) {
            console.error('Failed to load payments:', error);
            this.showNotification('Failed to load payments', 'error');
        }
    }

    renderPaymentsTable(payments) {
        const tbody = document.getElementById('paymentsTableBody');
        if (!payments.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-500">No payments found</td></tr>';
            return;
        }

        tbody.innerHTML = payments.map(payment => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    #${payment.id}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${payment.job_title || 'N/A'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    $${(payment.total_amount / 100).toFixed(2)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge status-${payment.status}">${payment.status}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${this.formatDate(payment.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="adminDashboard.viewPayment(${payment.id})" class="text-blue-600 hover:text-blue-900 mr-3">View</button>
                    ${payment.status === 'paid' && !payment.escrow_released ? 
                        `<button onclick="adminDashboard.releaseEscrow(${payment.id})" class="text-green-600 hover:text-green-900">Release</button>` : 
                        ''
                    }
                </td>
            </tr>
        `).join('');
    }

    async loadAnalytics() {
        try {
            const response = await this.apiCall('/api/admin/analytics/detailed');
            this.renderAnalyticsCharts(response);
        } catch (error) {
            console.error('Failed to load analytics:', error);
            this.showNotification('Failed to load analytics', 'error');
        }
    }

    initCharts() {
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart')?.getContext('2d');
        if (revenueCtx) {
            this.revenueChart = new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue',
                        data: [1200, 1900, 3000, 5000, 2000, 3000],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

        // User Growth Chart
        const userCtx = document.getElementById('userChart')?.getContext('2d');
        if (userCtx) {
            this.userChart = new Chart(userCtx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'New Users',
                        data: [12, 19, 30, 50, 20, 30],
                        backgroundColor: '#10b981'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    renderAnalyticsCharts(data) {
        // Monthly Revenue Chart
        const monthlyCtx = document.getElementById('monthlyRevenueChart')?.getContext('2d');
        if (monthlyCtx && data.monthly_revenue) {
            new Chart(monthlyCtx, {
                type: 'line',
                data: {
                    labels: data.monthly_revenue.labels,
                    datasets: [{
                        label: 'Monthly Revenue',
                        data: data.monthly_revenue.data,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Service Categories Chart
        const categoriesCtx = document.getElementById('serviceCategoriesChart')?.getContext('2d');
        if (categoriesCtx && data.service_categories) {
            new Chart(categoriesCtx, {
                type: 'doughnut',
                data: {
                    labels: data.service_categories.labels,
                    datasets: [{
                        data: data.service_categories.data,
                        backgroundColor: [
                            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    // CRUD Operations
    async addUser() {
        const formData = {
            full_name: document.getElementById('newUserName').value,
            email: document.getElementById('newUserEmail').value,
            user_type: document.getElementById('newUserType').value,
            password: document.getElementById('newUserPassword').value
        };

        try {
            await this.apiCall('/api/admin/users', 'POST', formData);
            this.showNotification('User added successfully', 'success');
            this.hideModal('addUserModal');
            this.loadUsers();
            document.getElementById('addUserForm').reset();
        } catch (error) {
            this.showNotification('Failed to add user', 'error');
        }
    }

    async addService() {
        const formData = {
            name: document.getElementById('newServiceName').value,
            category: document.getElementById('newServiceCategory').value,
            base_price: parseFloat(document.getElementById('newServicePrice').value),
            description: document.getElementById('newServiceDescription').value
        };

        try {
            await this.apiCall('/api/admin/services', 'POST', formData);
            this.showNotification('Service added successfully', 'success');
            this.hideModal('addServiceModal');
            this.loadServices();
            document.getElementById('addServiceForm').reset();
        } catch (error) {
            this.showNotification('Failed to add service', 'error');
        }
    }

    async editUser(userId) {
        // Implementation for editing user
        this.showNotification('Edit user functionality coming soon', 'info');
    }

    async suspendUser(userId) {
        if (confirm('Are you sure you want to suspend this user?')) {
            try {
                await this.apiCall(`/api/admin/users/${userId}/suspend`, 'POST');
                this.showNotification('User suspended successfully', 'success');
                this.loadUsers();
            } catch (error) {
                this.showNotification('Failed to suspend user', 'error');
            }
        }
    }

    async editService(serviceId) {
        this.showNotification('Edit service functionality coming soon', 'info');
    }

    async deleteService(serviceId) {
        if (confirm('Are you sure you want to delete this service?')) {
            try {
                await this.apiCall(`/api/admin/services/${serviceId}`, 'DELETE');
                this.showNotification('Service deleted successfully', 'success');
                this.loadServices();
            } catch (error) {
                this.showNotification('Failed to delete service', 'error');
            }
        }
    }

    async viewJob(jobId) {
        this.showNotification('View job functionality coming soon', 'info');
    }

    async moderateJob(jobId) {
        this.showNotification('Moderate job functionality coming soon', 'info');
    }

    async viewPayment(paymentId) {
        this.showNotification('View payment functionality coming soon', 'info');
    }

    async releaseEscrow(paymentId) {
        if (confirm('Are you sure you want to release the escrow for this payment?')) {
            try {
                await this.apiCall(`/api/admin/payments/${paymentId}/release`, 'POST');
                this.showNotification('Escrow released successfully', 'success');
                this.loadPayments();
            } catch (error) {
                this.showNotification('Failed to release escrow', 'error');
            }
        }
    }

    // Utility Functions
    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Authorization': `Bearer ${this.adminToken}`,
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            if (response.status === 401) {
                this.logout();
                throw new Error('Unauthorized');
            }
            throw new Error(`API call failed: ${response.statusText}`);
        }

        return await response.json();
    }

    showModal(modalId) {
        document.getElementById(modalId)?.classList.add('show');
    }

    hideModal(modalId) {
        document.getElementById(modalId)?.classList.remove('show');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    filterUsers() {
        const searchTerm = document.getElementById('userSearch').value.toLowerCase();
        const typeFilter = document.getElementById('userTypeFilter').value;
        const statusFilter = document.getElementById('userStatusFilter').value;

        // Implementation for filtering users
        this.loadUsers(); // For now, just reload
    }

    async saveSettings() {
        const settings = {
            platform_fee_rate: parseFloat(document.getElementById('platformFeeRate').value),
            auto_release_days: parseInt(document.getElementById('autoReleaseDays').value),
            email_notifications: document.getElementById('emailNotifications').checked,
            weekly_reports: document.getElementById('weeklyReports').checked
        };

        try {
            await this.apiCall('/api/admin/settings', 'POST', settings);
            this.showNotification('Settings saved successfully', 'success');
        } catch (error) {
            this.showNotification('Failed to save settings', 'error');
        }
    }

    async exportData() {
        try {
            const response = await fetch('/api/admin/export', {
                headers: {
                    'Authorization': `Bearer ${this.adminToken}`
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `tradehub-data-${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
                this.showNotification('Data exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            this.showNotification('Failed to export data', 'error');
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    logout() {
        localStorage.removeItem('adminToken');
        window.location.reload();
    }
}

// Initialize admin dashboard
const adminDashboard = new AdminDashboard();

// Global functions for onclick handlers
window.showModal = (modalId) => adminDashboard.showModal(modalId);
window.hideModal = (modalId) => adminDashboard.hideModal(modalId);
window.filterUsers = () => adminDashboard.filterUsers();
window.saveSettings = () => adminDashboard.saveSettings();
window.exportData = () => adminDashboard.exportData();

