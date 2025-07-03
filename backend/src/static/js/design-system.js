/**
 * Biped Platform Design System JavaScript v2.0
 * Modern UI/UX Framework with Dark/Light Mode, Real-time Features, and Performance Optimization
 */

class BipedDesignSystem {
    constructor() {
        this.theme = localStorage.getItem('biped-theme') || 'light';
        this.notifications = [];
        this.websocket = null;
        this.cache = new Map();
        this.observers = new Map();
        this.components = new Map();
        
        this.init();
    }

    init() {
        this.initTheme();
        this.initComponents();
        this.initWebSocket();
        this.initPerformanceOptimizations();
        this.initAccessibility();
        this.initAnalytics();
        
        console.log('🎨 Biped Design System v2.0 initialized');
    }

    // Theme Management
    initTheme() {
        // Set initial theme
        document.documentElement.setAttribute('data-theme', this.theme);
        
        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                if (!localStorage.getItem('biped-theme')) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }

        // Create theme toggle button
        this.createThemeToggle();
    }

    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('biped-theme', theme);
        
        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
        
        // Update theme toggle button
        this.updateThemeToggle();
    }

    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle btn btn-ghost';
        toggle.innerHTML = this.getThemeIcon();
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.addEventListener('click', () => this.toggleTheme());
        
        // Add to navigation if it exists
        const nav = document.querySelector('nav .flex.items-center.space-x-4');
        if (nav) {
            nav.insertBefore(toggle, nav.firstChild);
        }
    }

    updateThemeToggle() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.innerHTML = this.getThemeIcon();
        }
    }

    getThemeIcon() {
        return this.theme === 'light' 
            ? '<i class="fas fa-moon"></i>' 
            : '<i class="fas fa-sun"></i>';
    }

    // Component System
    initComponents() {
        this.registerComponent('modal', ModalComponent);
        this.registerComponent('notification', NotificationComponent);
        this.registerComponent('dropdown', DropdownComponent);
        this.registerComponent('tooltip', TooltipComponent);
        this.registerComponent('tabs', TabsComponent);
        this.registerComponent('accordion', AccordionComponent);
        this.registerComponent('carousel', CarouselComponent);
        this.registerComponent('datepicker', DatePickerComponent);
        this.registerComponent('fileupload', FileUploadComponent);
        this.registerComponent('chart', ChartComponent);
        
        // Auto-initialize components
        this.initializeComponents();
    }

    registerComponent(name, componentClass) {
        this.components.set(name, componentClass);
    }

    initializeComponents() {
        this.components.forEach((ComponentClass, name) => {
            const elements = document.querySelectorAll(`[data-component="${name}"]`);
            elements.forEach(element => {
                if (!element._bipedComponent) {
                    element._bipedComponent = new ComponentClass(element, this);
                }
            });
        });
    }

    // Real-time Features
    initWebSocket() {
        if (!window.WebSocket) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.showNotification('Connected to real-time updates', 'success');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (e) {
                    console.error('WebSocket message parse error:', e);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.initWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (e) {
            console.warn('WebSocket not available:', e);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'notification':
                this.showNotification(data.message, data.level || 'info');
                break;
            case 'job_update':
                this.updateJobStatus(data.jobId, data.status);
                break;
            case 'message':
                this.handleNewMessage(data);
                break;
            case 'analytics':
                this.updateAnalytics(data);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    // Notification System
    showNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date()
        };
        
        this.notifications.push(notification);
        this.renderNotification(notification);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => this.removeNotification(notification.id), duration);
        }
        
        return notification.id;
    }

    removeNotification(id) {
        this.notifications = this.notifications.filter(n => n.id !== id);
        const element = document.querySelector(`[data-notification-id="${id}"]`);
        if (element) {
            element.classList.add('fade-out');
            setTimeout(() => element.remove(), 300);
        }
    }

    renderNotification(notification) {
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1080;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }

        const element = document.createElement('div');
        element.className = `alert alert-${notification.type} fade-in`;
        element.setAttribute('data-notification-id', notification.id);
        element.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
            <div class="flex-1">
                <div class="font-medium">${notification.message}</div>
                <div class="text-sm opacity-75">${this.formatTime(notification.timestamp)}</div>
            </div>
            <button onclick="designSystem.removeNotification(${notification.id})" class="btn btn-ghost btn-sm">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(element);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Performance Optimizations
    initPerformanceOptimizations() {
        // Lazy loading for images
        this.initLazyLoading();
        
        // Intersection Observer for animations
        this.initScrollAnimations();
        
        // Debounced resize handler
        this.initResizeHandler();
        
        // Preload critical resources
        this.preloadCriticalResources();
    }

    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    initScrollAnimations() {
        if ('IntersectionObserver' in window) {
            const animationObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                    }
                });
            }, { threshold: 0.1 });

            document.querySelectorAll('[data-animate]').forEach(el => {
                animationObserver.observe(el);
            });
        }
    }

    initResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    handleResize() {
        // Update mobile menu state
        this.updateMobileMenu();
        
        // Recalculate component positions
        this.components.forEach((component, name) => {
            if (component.onResize) {
                component.onResize();
            }
        });
    }

    preloadCriticalResources() {
        const criticalResources = [
            '/static/css/design-system.css',
            '/static/js/design-system.js'
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            document.head.appendChild(link);
        });
    }

    // Accessibility Features
    initAccessibility() {
        // Focus management
        this.initFocusManagement();
        
        // Keyboard navigation
        this.initKeyboardNavigation();
        
        // Screen reader support
        this.initScreenReaderSupport();
        
        // High contrast mode detection
        this.initHighContrastMode();
    }

    initFocusManagement() {
        // Focus trap for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }

    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            }
        } else {
            if (document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    }

    initKeyboardNavigation() {
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    this.closeModal(modal);
                }
            }
        });
    }

    initScreenReaderSupport() {
        // Add ARIA labels to interactive elements
        document.querySelectorAll('button:not([aria-label])').forEach(button => {
            if (!button.textContent.trim()) {
                button.setAttribute('aria-label', 'Button');
            }
        });
    }

    initHighContrastMode() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-contrast: high)');
            mediaQuery.addListener((e) => {
                document.documentElement.classList.toggle('high-contrast', e.matches);
            });
            
            if (mediaQuery.matches) {
                document.documentElement.classList.add('high-contrast');
            }
        }
    }

    // Analytics & Metrics
    initAnalytics() {
        this.analytics = {
            pageViews: 0,
            interactions: 0,
            errors: 0,
            performance: {}
        };

        // Track page views
        this.trackPageView();
        
        // Track interactions
        this.trackInteractions();
        
        // Track errors
        this.trackErrors();
        
        // Track performance
        this.trackPerformance();
    }

    trackPageView() {
        this.analytics.pageViews++;
        this.sendAnalytics('page_view', {
            url: window.location.href,
            timestamp: new Date().toISOString()
        });
    }

    trackInteractions() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('button, a, [data-track]')) {
                this.analytics.interactions++;
                this.sendAnalytics('interaction', {
                    element: e.target.tagName,
                    action: 'click',
                    timestamp: new Date().toISOString()
                });
            }
        });
    }

    trackErrors() {
        window.addEventListener('error', (e) => {
            this.analytics.errors++;
            this.sendAnalytics('error', {
                message: e.message,
                filename: e.filename,
                line: e.lineno,
                timestamp: new Date().toISOString()
            });
        });
    }

    trackPerformance() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    this.analytics.performance = {
                        loadTime: perfData.loadEventEnd - perfData.loadEventStart,
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0
                    };
                    
                    this.sendAnalytics('performance', this.analytics.performance);
                }, 1000);
            });
        }
    }

    sendAnalytics(event, data) {
        // Send to analytics endpoint
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'analytics',
                event,
                data,
                timestamp: new Date().toISOString()
            }));
        }
    }

    // Utility Functions
    formatTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

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
    }

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
    }

    // API Helper
    async api(endpoint, options = {}) {
        const url = `/api${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            this.showNotification(`API Error: ${error.message}`, 'error');
            throw error;
        }
    }

    // Mobile Menu
    updateMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenu && window.innerWidth > 768) {
            mobileMenu.classList.add('hidden');
        }
    }

    toggleMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenu) {
            mobileMenu.classList.toggle('hidden');
        }
    }

    // Modal Management
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Focus first focusable element
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }
    }

    closeModal(modal) {
        if (typeof modal === 'string') {
            modal = document.getElementById(modal);
        }
        
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    // Form Validation
    validateForm(form) {
        const errors = [];
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                errors.push(`${input.name || input.id} is required`);
                input.classList.add('error');
            } else {
                input.classList.remove('error');
            }
        });

        return errors;
    }

    // Loading States
    showLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    }

    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }
}

// Component Classes
class ModalComponent {
    constructor(element, designSystem) {
        this.element = element;
        this.designSystem = designSystem;
        this.init();
    }

    init() {
        // Add close button functionality
        const closeButtons = this.element.querySelectorAll('[data-modal-close]');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => this.close());
        });

        // Close on backdrop click
        this.element.addEventListener('click', (e) => {
            if (e.target === this.element) {
                this.close();
            }
        });
    }

    open() {
        this.element.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.element.classList.remove('show');
        document.body.style.overflow = '';
    }
}

class NotificationComponent {
    constructor(element, designSystem) {
        this.element = element;
        this.designSystem = designSystem;
        this.init();
    }

    init() {
        // Auto-hide after delay
        const delay = this.element.dataset.delay || 5000;
        if (delay > 0) {
            setTimeout(() => this.hide(), delay);
        }

        // Add close button
        const closeButton = this.element.querySelector('[data-notification-close]');
        if (closeButton) {
            closeButton.addEventListener('click', () => this.hide());
        }
    }

    hide() {
        this.element.classList.add('fade-out');
        setTimeout(() => this.element.remove(), 300);
    }
}

class DropdownComponent {
    constructor(element, designSystem) {
        this.element = element;
        this.designSystem = designSystem;
        this.trigger = element.querySelector('[data-dropdown-trigger]');
        this.menu = element.querySelector('[data-dropdown-menu]');
        this.isOpen = false;
        this.init();
    }

    init() {
        if (this.trigger) {
            this.trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle();
            });
        }

        // Close on outside click
        document.addEventListener('click', () => {
            if (this.isOpen) {
                this.close();
            }
        });
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.menu.classList.remove('hidden');
        this.menu.classList.add('fade-in');
    }

    close() {
        this.isOpen = false;
        this.menu.classList.add('hidden');
        this.menu.classList.remove('fade-in');
    }
}

class TooltipComponent {
    constructor(element, designSystem) {
        this.element = element;
        this.designSystem = designSystem;
        this.init();
    }

    init() {
        this.element.addEventListener('mouseenter', () => this.show());
        this.element.addEventListener('mouseleave', () => this.hide());
    }

    show() {
        const tooltip = this.element.querySelector('.tooltip-content');
        if (tooltip) {
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
        }
    }

    hide() {
        const tooltip = this.element.querySelector('.tooltip-content');
        if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        }
    }
}

// Additional component classes would be implemented here...
class TabsComponent {
    constructor(element, designSystem) {
        this.element = element;
        this.designSystem = designSystem;
        this.init();
    }

    init() {
        const tabs = this.element.querySelectorAll('[data-tab]');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });
    }

    switchTab(tabId) {
        // Hide all tab contents
        this.element.querySelectorAll('[data-tab-content]').forEach(content => {
            content.classList.add('hidden');
        });

        // Remove active class from all tabs
        this.element.querySelectorAll('[data-tab]').forEach(tab => {
            tab.classList.remove('active');
        });

        // Show selected tab content
        const targetContent = this.element.querySelector(`[data-tab-content="${tabId}"]`);
        if (targetContent) {
            targetContent.classList.remove('hidden');
        }

        // Add active class to selected tab
        const targetTab = this.element.querySelector(`[data-tab="${tabId}"]`);
        if (targetTab) {
            targetTab.classList.add('active');
        }
    }
}

// Accordion Component
class AccordionComponent {
    constructor(element) {
        this.element = element;
        this.init();
    }

    init() {
        const headers = this.element.querySelectorAll('[data-accordion-header]');
        headers.forEach(header => {
            header.addEventListener('click', (e) => {
                this.toggle(e.target.closest('[data-accordion-item]'));
            });
        });
    }

    toggle(item) {
        const content = item.querySelector('[data-accordion-content]');
        const isOpen = item.classList.contains('open');
        
        if (isOpen) {
            item.classList.remove('open');
            content.style.maxHeight = null;
        } else {
            item.classList.add('open');
            content.style.maxHeight = content.scrollHeight + 'px';
        }
    }
}

// Carousel Component
class CarouselComponent {
    constructor(element) {
        this.element = element;
        this.currentSlide = 0;
        this.slides = this.element.querySelectorAll('[data-slide]');
        this.init();
    }

    init() {
        const prevBtn = this.element.querySelector('[data-carousel-prev]');
        const nextBtn = this.element.querySelector('[data-carousel-next]');
        
        if (prevBtn) prevBtn.addEventListener('click', () => this.prev());
        if (nextBtn) nextBtn.addEventListener('click', () => this.next());
        
        this.updateSlides();
    }

    next() {
        this.currentSlide = (this.currentSlide + 1) % this.slides.length;
        this.updateSlides();
    }

    prev() {
        this.currentSlide = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
        this.updateSlides();
    }

    updateSlides() {
        this.slides.forEach((slide, index) => {
            slide.classList.toggle('active', index === this.currentSlide);
        });
    }
}

// DatePicker Component
class DatePickerComponent {
    constructor(element) {
        this.element = element;
        this.input = element.querySelector('input[type="date"]') || element;
        this.init();
    }

    init() {
        if (!this.input.type || this.input.type !== 'date') {
            this.input.type = 'date';
        }
        
        this.input.addEventListener('change', (e) => {
            this.onDateChange(e.target.value);
        });
    }

    onDateChange(value) {
        this.element.dispatchEvent(new CustomEvent('datechange', {
            detail: { value }
        }));
    }

    setValue(date) {
        this.input.value = date;
    }

    getValue() {
        return this.input.value;
    }
}

// FileUpload Component
class FileUploadComponent {
    constructor(element) {
        this.element = element;
        this.input = element.querySelector('input[type="file"]');
        this.dropZone = element.querySelector('[data-drop-zone]');
        this.init();
    }

    init() {
        if (this.input) {
            this.input.addEventListener('change', (e) => this.handleFiles(e.target.files));
        }

        if (this.dropZone) {
            this.dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.dropZone.classList.add('drag-over');
            });

            this.dropZone.addEventListener('dragleave', () => {
                this.dropZone.classList.remove('drag-over');
            });

            this.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.dropZone.classList.remove('drag-over');
                this.handleFiles(e.dataTransfer.files);
            });
        }
    }

    handleFiles(files) {
        Array.from(files).forEach(file => {
            this.element.dispatchEvent(new CustomEvent('fileselected', {
                detail: { file }
            }));
        });
    }
}

// Chart Component
class ChartComponent {
    constructor(element) {
        this.element = element;
        this.canvas = element.querySelector('canvas');
        this.data = JSON.parse(element.dataset.chartData || '{}');
        this.type = element.dataset.chartType || 'line';
        this.init();
    }

    init() {
        if (this.canvas) {
            this.renderChart();
        }
    }

    renderChart() {
        // Basic chart rendering - in a real implementation, you'd use Chart.js or similar
        const ctx = this.canvas.getContext('2d');
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Simple line chart implementation
        if (this.type === 'line' && this.data.datasets) {
            this.drawLineChart(ctx, width, height);
        }
    }

    drawLineChart(ctx, width, height) {
        const padding = 40;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;
        
        // Draw axes
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        
        // Y-axis
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.stroke();
        
        // X-axis
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Draw data if available
        if (this.data.datasets && this.data.datasets.length > 0) {
            const dataset = this.data.datasets[0];
            const points = dataset.data || [];
            
            if (points.length > 1) {
                ctx.strokeStyle = dataset.borderColor || '#3b82f6';
                ctx.lineWidth = 2;
                ctx.beginPath();
                
                points.forEach((point, index) => {
                    const x = padding + (index / (points.length - 1)) * chartWidth;
                    const y = height - padding - (point / 100) * chartHeight; // Assuming 0-100 scale
                    
                    if (index === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                });
                
                ctx.stroke();
            }
        }
    }

    updateData(newData) {
        this.data = newData;
        this.renderChart();
    }
}

// Initialize the design system
const designSystem = new BipedDesignSystem();

// Global functions for backward compatibility
function toggleMobileMenu() {
    designSystem.toggleMobileMenu();
}

function showModal(modalId) {
    designSystem.showModal(modalId);
}

function closeModal(modalId) {
    designSystem.closeModal(modalId);
}

function showNotification(message, type, duration) {
    return designSystem.showNotification(message, type, duration);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BipedDesignSystem;
}

