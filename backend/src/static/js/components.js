/**
 * BIPED REUSABLE COMPONENT LIBRARY
 * ================================
 * 
 * This file contains reusable JavaScript components and utilities
 * that can be used across all pages in the Biped platform.
 */

// ===================================
// GLOBAL CONFIGURATION
// ===================================

const BIPED_CONFIG = {
  API_BASE_URL: '/api',
  TOAST_DURATION: 3000,
  ANIMATION_DURATION: 300,
  BREAKPOINTS: {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536
  }
};

// ===================================
// UTILITY FUNCTIONS
// ===================================

const Utils = {
  /**
   * Debounce function to limit the rate of function calls
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Throttle function to limit function calls to once per interval
   */
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Format currency values
   */
  formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  },

  /**
   * Format dates
   */
  formatDate(date, options = {}) {
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    };
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
  },

  /**
   * Validate email format
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  /**
   * Generate avatar URL
   */
  generateAvatarUrl(name, options = {}) {
    const { size = 40, background = '3b82f6', color = 'fff' } = options;
    const encodedName = encodeURIComponent(name);
    return `https://ui-avatars.com/api/?name=${encodedName}&size=${size}&background=${background}&color=${color}`;
  },

  /**
   * Get current breakpoint
   */
  getCurrentBreakpoint() {
    const width = window.innerWidth;
    if (width >= BIPED_CONFIG.BREAKPOINTS['2xl']) return '2xl';
    if (width >= BIPED_CONFIG.BREAKPOINTS.xl) return 'xl';
    if (width >= BIPED_CONFIG.BREAKPOINTS.lg) return 'lg';
    if (width >= BIPED_CONFIG.BREAKPOINTS.md) return 'md';
    if (width >= BIPED_CONFIG.BREAKPOINTS.sm) return 'sm';
    return 'xs';
  }
};

// ===================================
// API CLIENT
// ===================================

class ApiClient {
  constructor(baseUrl = BIPED_CONFIG.API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include',
      ...options
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response;
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Convenience methods
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body: data });
  }

  put(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body: data });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Global API client instance
const api = new ApiClient();

// ===================================
// TOAST NOTIFICATION COMPONENT
// ===================================

class ToastManager {
  constructor() {
    this.container = this.createContainer();
    this.toasts = new Map();
  }

  createContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'fixed top-4 right-4 z-50 space-y-2';
      document.body.appendChild(container);
    }
    return container;
  }

  show(message, type = 'info', duration = BIPED_CONFIG.TOAST_DURATION) {
    const id = Date.now().toString();
    const toast = this.createToast(id, message, type);
    
    this.container.appendChild(toast);
    this.toasts.set(id, toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.add('translate-x-0', 'opacity-100');
      toast.classList.remove('translate-x-full', 'opacity-0');
    });

    // Auto remove
    if (duration > 0) {
      setTimeout(() => this.remove(id), duration);
    }

    return id;
  }

  createToast(id, message, type) {
    const toast = document.createElement('div');
    toast.id = `toast-${id}`;
    toast.className = `
      transform transition-all duration-300 translate-x-full opacity-0
      max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto
      ring-1 ring-black ring-opacity-5 overflow-hidden
    `;

    const iconMap = {
      success: 'fas fa-check-circle text-green-400',
      error: 'fas fa-exclamation-circle text-red-400',
      warning: 'fas fa-exclamation-triangle text-yellow-400',
      info: 'fas fa-info-circle text-blue-400'
    };

    toast.innerHTML = `
      <div class="p-4">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <i class="${iconMap[type] || iconMap.info}"></i>
          </div>
          <div class="ml-3 w-0 flex-1 pt-0.5">
            <p class="text-sm font-medium text-gray-900">${message}</p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button class="toast-close bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none">
              <span class="sr-only">Close</span>
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    `;

    // Add close event listener
    toast.querySelector('.toast-close').addEventListener('click', () => {
      this.remove(id);
    });

    return toast;
  }

  remove(id) {
    const toast = this.toasts.get(id);
    if (toast) {
      toast.classList.add('translate-x-full', 'opacity-0');
      toast.classList.remove('translate-x-0', 'opacity-100');
      
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
        this.toasts.delete(id);
      }, BIPED_CONFIG.ANIMATION_DURATION);
    }
  }

  // Convenience methods
  success(message, duration) {
    return this.show(message, 'success', duration);
  }

  error(message, duration) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration) {
    return this.show(message, 'info', duration);
  }
}

// Global toast manager instance
const toast = new ToastManager();

// ===================================
// MODAL COMPONENT
// ===================================

class Modal {
  constructor(options = {}) {
    this.options = {
      backdrop: true,
      keyboard: true,
      focus: true,
      ...options
    };
    this.isOpen = false;
    this.element = null;
  }

  create(content, title = '') {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 overflow-y-auto';
    modal.setAttribute('aria-labelledby', 'modal-title');
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');

    modal.innerHTML = `
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="modal-backdrop fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="modal-content inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          ${title ? `
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">${title}</h3>
            </div>
          ` : ''}
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6">
            ${content}
          </div>
        </div>
      </div>
    `;

    return modal;
  }

  show(content, title) {
    if (this.isOpen) return;

    this.element = this.create(content, title);
    document.body.appendChild(this.element);
    document.body.classList.add('overflow-hidden');

    // Event listeners
    if (this.options.backdrop) {
      this.element.querySelector('.modal-backdrop').addEventListener('click', () => {
        this.hide();
      });
    }

    if (this.options.keyboard) {
      document.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    // Animate in
    requestAnimationFrame(() => {
      this.element.querySelector('.modal-backdrop').classList.add('opacity-100');
      this.element.querySelector('.modal-content').classList.add('opacity-100', 'translate-y-0', 'sm:scale-100');
    });

    this.isOpen = true;

    // Focus management
    if (this.options.focus) {
      const focusableElement = this.element.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusableElement) {
        focusableElement.focus();
      }
    }
  }

  hide() {
    if (!this.isOpen || !this.element) return;

    // Animate out
    this.element.querySelector('.modal-backdrop').classList.remove('opacity-100');
    this.element.querySelector('.modal-content').classList.remove('opacity-100', 'translate-y-0', 'sm:scale-100');

    setTimeout(() => {
      if (this.element && this.element.parentNode) {
        this.element.parentNode.removeChild(this.element);
      }
      document.body.classList.remove('overflow-hidden');
      this.element = null;
      this.isOpen = false;
    }, BIPED_CONFIG.ANIMATION_DURATION);

    // Remove event listeners
    document.removeEventListener('keydown', this.handleKeydown.bind(this));
  }

  handleKeydown(event) {
    if (event.key === 'Escape') {
      this.hide();
    }
  }
}

// ===================================
// FORM VALIDATION COMPONENT
// ===================================

class FormValidator {
  constructor(form, rules = {}) {
    this.form = form;
    this.rules = rules;
    this.errors = {};
    this.init();
  }

  init() {
    this.form.addEventListener('submit', this.handleSubmit.bind(this));
    
    // Add real-time validation
    Object.keys(this.rules).forEach(fieldName => {
      const field = this.form.querySelector(`[name="${fieldName}"]`);
      if (field) {
        field.addEventListener('blur', () => this.validateField(fieldName));
        field.addEventListener('input', Utils.debounce(() => this.validateField(fieldName), 300));
      }
    });
  }

  handleSubmit(event) {
    event.preventDefault();
    
    if (this.validate()) {
      // Form is valid, trigger custom event
      this.form.dispatchEvent(new CustomEvent('validSubmit', {
        detail: { formData: new FormData(this.form) }
      }));
    }
  }

  validate() {
    this.errors = {};
    let isValid = true;

    Object.keys(this.rules).forEach(fieldName => {
      if (!this.validateField(fieldName)) {
        isValid = false;
      }
    });

    return isValid;
  }

  validateField(fieldName) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    const rules = this.rules[fieldName];
    const value = field ? field.value.trim() : '';

    delete this.errors[fieldName];

    if (rules.required && !value) {
      this.setError(fieldName, rules.required.message || `${fieldName} is required`);
      return false;
    }

    if (value && rules.email && !Utils.isValidEmail(value)) {
      this.setError(fieldName, rules.email.message || 'Please enter a valid email address');
      return false;
    }

    if (value && rules.minLength && value.length < rules.minLength.value) {
      this.setError(fieldName, rules.minLength.message || `Minimum ${rules.minLength.value} characters required`);
      return false;
    }

    if (value && rules.pattern && !rules.pattern.value.test(value)) {
      this.setError(fieldName, rules.pattern.message || 'Invalid format');
      return false;
    }

    if (rules.custom && !rules.custom.validator(value)) {
      this.setError(fieldName, rules.custom.message || 'Invalid value');
      return false;
    }

    this.clearError(fieldName);
    return true;
  }

  setError(fieldName, message) {
    this.errors[fieldName] = message;
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    
    if (field) {
      field.classList.add('border-red-500');
      field.classList.remove('border-gray-300');
      
      // Show error message
      let errorElement = field.parentNode.querySelector('.error-message');
      if (!errorElement) {
        errorElement = document.createElement('p');
        errorElement.className = 'error-message text-sm text-red-600 mt-1';
        field.parentNode.appendChild(errorElement);
      }
      errorElement.textContent = message;
    }
  }

  clearError(fieldName) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    
    if (field) {
      field.classList.remove('border-red-500');
      field.classList.add('border-gray-300');
      
      const errorElement = field.parentNode.querySelector('.error-message');
      if (errorElement) {
        errorElement.remove();
      }
    }
  }
}

// ===================================
// LOADING COMPONENT
// ===================================

class LoadingManager {
  constructor() {
    this.activeLoaders = new Set();
  }

  show(target = document.body, message = 'Loading...') {
    const loaderId = Date.now().toString();
    const loader = this.createLoader(loaderId, message);
    
    if (target === document.body) {
      target.appendChild(loader);
    } else {
      target.style.position = 'relative';
      target.appendChild(loader);
    }
    
    this.activeLoaders.add(loaderId);
    return loaderId;
  }

  createLoader(id, message) {
    const loader = document.createElement('div');
    loader.id = `loader-${id}`;
    loader.className = 'absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50';
    
    loader.innerHTML = `
      <div class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="mt-2 text-sm text-gray-600">${message}</p>
      </div>
    `;
    
    return loader;
  }

  hide(loaderId) {
    const loader = document.getElementById(`loader-${loaderId}`);
    if (loader) {
      loader.remove();
      this.activeLoaders.delete(loaderId);
    }
  }

  hideAll() {
    this.activeLoaders.forEach(id => this.hide(id));
  }
}

// Global loading manager instance
const loading = new LoadingManager();

// ===================================
// TAB COMPONENT
// ===================================

class TabManager {
  constructor(container) {
    this.container = container;
    this.tabButtons = container.querySelectorAll('[data-tab]');
    this.tabContents = container.querySelectorAll('.tab-content');
    this.init();
  }

  init() {
    this.tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        this.switchTab(button.dataset.tab);
      });
    });
  }

  switchTab(tabId) {
    // Update buttons
    this.tabButtons.forEach(button => {
      if (button.dataset.tab === tabId) {
        button.classList.add('active', 'border-primary', 'text-primary');
        button.classList.remove('text-gray-500', 'border-transparent');
      } else {
        button.classList.remove('active', 'border-primary', 'text-primary');
        button.classList.add('text-gray-500', 'border-transparent');
      }
    });

    // Update content
    this.tabContents.forEach(content => {
      if (content.id === tabId) {
        content.classList.add('active');
        content.classList.remove('hidden');
      } else {
        content.classList.remove('active');
        content.classList.add('hidden');
      }
    });
  }
}

// ===================================
// MOBILE MENU COMPONENT
// ===================================

class MobileMenu {
  constructor(menuButton, sidebar) {
    this.menuButton = menuButton;
    this.sidebar = sidebar;
    this.isOpen = false;
    this.init();
  }

  init() {
    this.menuButton.addEventListener('click', () => {
      this.toggle();
    });

    // Close on backdrop click
    document.addEventListener('click', (event) => {
      if (this.isOpen && !this.sidebar.contains(event.target) && !this.menuButton.contains(event.target)) {
        this.close();
      }
    });

    // Close on escape key
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.sidebar.classList.remove('hidden');
    this.sidebar.classList.add('open');
    document.body.classList.add('overflow-hidden');
    this.isOpen = true;
  }

  close() {
    this.sidebar.classList.add('hidden');
    this.sidebar.classList.remove('open');
    document.body.classList.remove('overflow-hidden');
    this.isOpen = false;
  }
}

// ===================================
// AUTHENTICATION UTILITIES
// ===================================

const Auth = {
  async getCurrentUser() {
    try {
      return await api.get('/auth/me');
    } catch (error) {
      return null;
    }
  },

  async login(credentials) {
    return await api.post('/auth/login', credentials);
  },

  async logout() {
    try {
      await api.post('/auth/logout');
      window.location.href = '/';
    } catch (error) {
      // Force redirect even if logout fails
      window.location.href = '/';
    }
  },

  async register(userData) {
    return await api.post('/auth/register', userData);
  },

  redirectIfNotAuthenticated() {
    this.getCurrentUser().then(user => {
      if (!user) {
        window.location.href = '/';
      }
    });
  }
};

// ===================================
// GLOBAL INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', function() {
  // Initialize mobile menu if elements exist
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileSidebar = document.getElementById('mobile-sidebar');
  if (mobileMenuButton && mobileSidebar) {
    new MobileMenu(mobileMenuButton, mobileSidebar);
  }

  // Initialize tabs if they exist
  const tabContainers = document.querySelectorAll('.tab-container');
  tabContainers.forEach(container => {
    new TabManager(container);
  });

  // Global logout handlers
  document.querySelectorAll('[data-action="logout"]').forEach(button => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      Auth.logout();
    });
  });

  // Global form validation
  document.querySelectorAll('form[data-validate]').forEach(form => {
    const rules = JSON.parse(form.dataset.validate);
    new FormValidator(form, rules);
  });
});

// Export for use in other scripts
window.Biped = {
  Utils,
  ApiClient,
  api,
  toast,
  Modal,
  FormValidator,
  loading,
  TabManager,
  MobileMenu,
  Auth,
  BIPED_CONFIG
};

