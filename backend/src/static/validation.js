// Frontend validation utilities for TradeHub Platform
class FormValidator {
    constructor() {
        this.emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        this.phoneRegex = /^\+?1?-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$/;
        this.passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    }

    // Validation methods
    validateEmail(email) {
        if (!email || typeof email !== 'string') {
            return { valid: false, message: 'Email is required' };
        }
        
        const trimmed = email.trim();
        if (trimmed.length > 254) {
            return { valid: false, message: 'Email address too long' };
        }
        
        if (!this.emailRegex.test(trimmed)) {
            return { valid: false, message: 'Please enter a valid email address' };
        }
        
        return { valid: true, message: '' };
    }

    validatePassword(password) {
        if (!password || typeof password !== 'string') {
            return { valid: false, message: 'Password is required' };
        }
        
        if (password.length < 8) {
            return { valid: false, message: 'Password must be at least 8 characters long' };
        }
        
        if (password.length > 128) {
            return { valid: false, message: 'Password too long' };
        }
        
        if (!/[A-Z]/.test(password)) {
            return { valid: false, message: 'Password must contain at least one uppercase letter' };
        }
        
        if (!/[a-z]/.test(password)) {
            return { valid: false, message: 'Password must contain at least one lowercase letter' };
        }
        
        if (!/\d/.test(password)) {
            return { valid: false, message: 'Password must contain at least one number' };
        }
        
        return { valid: true, message: '' };
    }

    validatePhone(phone) {
        if (!phone || typeof phone !== 'string') {
            return { valid: false, message: 'Phone number is required' };
        }
        
        const trimmed = phone.trim();
        if (!this.phoneRegex.test(trimmed)) {
            return { valid: false, message: 'Please enter a valid phone number' };
        }
        
        return { valid: true, message: '' };
    }

    validateName(name, fieldName = 'Name') {
        if (!name || typeof name !== 'string') {
            return { valid: false, message: `${fieldName} is required` };
        }
        
        const trimmed = name.trim();
        if (trimmed.length < 1) {
            return { valid: false, message: `${fieldName} is required` };
        }
        
        if (trimmed.length > 50) {
            return { valid: false, message: `${fieldName} must be no more than 50 characters` };
        }
        
        return { valid: true, message: '' };
    }

    validateRequired(value, fieldName) {
        if (!value || (typeof value === 'string' && value.trim() === '')) {
            return { valid: false, message: `${fieldName} is required` };
        }
        return { valid: true, message: '' };
    }

    // Form validation methods
    validateRegistrationForm(formData) {
        const errors = {};
        
        // Validate email
        const emailResult = this.validateEmail(formData.email);
        if (!emailResult.valid) {
            errors.email = emailResult.message;
        }
        
        // Validate password
        const passwordResult = this.validatePassword(formData.password);
        if (!passwordResult.valid) {
            errors.password = passwordResult.message;
        }
        
        // Validate first name
        const firstNameResult = this.validateName(formData.firstName, 'First name');
        if (!firstNameResult.valid) {
            errors.firstName = firstNameResult.message;
        }
        
        // Validate last name
        const lastNameResult = this.validateName(formData.lastName, 'Last name');
        if (!lastNameResult.valid) {
            errors.lastName = lastNameResult.message;
        }
        
        // Validate user type
        if (!formData.userType || !['customer', 'provider'].includes(formData.userType)) {
            errors.userType = 'Please select a user type';
        }
        
        // Validate phone if provided
        if (formData.phone && formData.phone.trim()) {
            const phoneResult = this.validatePhone(formData.phone);
            if (!phoneResult.valid) {
                errors.phone = phoneResult.message;
            }
        }
        
        return {
            valid: Object.keys(errors).length === 0,
            errors: errors
        };
    }

    validateLoginForm(formData) {
        const errors = {};
        
        // Validate email
        const emailResult = this.validateEmail(formData.email);
        if (!emailResult.valid) {
            errors.email = emailResult.message;
        }
        
        // Validate password (just check if present for login)
        if (!formData.password || formData.password.trim() === '') {
            errors.password = 'Password is required';
        }
        
        return {
            valid: Object.keys(errors).length === 0,
            errors: errors
        };
    }

    // UI validation helpers
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        // Remove existing error styling
        field.classList.remove('border-red-500', 'border-green-500');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        if (message) {
            // Add error styling
            field.classList.add('border-red-500');
            
            // Create error message element
            const errorElement = document.createElement('div');
            errorElement.className = 'error-message text-red-500 text-sm mt-1';
            errorElement.textContent = message;
            
            // Insert error message after the field
            field.parentNode.insertBefore(errorElement, field.nextSibling);
        } else {
            // Add success styling
            field.classList.add('border-green-500');
        }
    }

    clearFieldErrors(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        // Remove all error styling and messages
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            field.classList.remove('border-red-500', 'border-green-500');
        });
        
        const errorMessages = form.querySelectorAll('.error-message');
        errorMessages.forEach(error => error.remove());
    }

    // Real-time validation
    setupRealTimeValidation(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        const fields = form.querySelectorAll('input[type="email"], input[type="password"], input[type="text"], input[type="tel"]');
        
        fields.forEach(field => {
            let timeout;
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.validateField(field);
                }, 500); // Debounce validation
            });
            
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
        });
    }

    validateField(field) {
        const fieldType = field.type;
        const fieldName = field.name || field.id;
        const fieldValue = field.value;
        
        let result = { valid: true, message: '' };
        
        switch (fieldType) {
            case 'email':
                result = this.validateEmail(fieldValue);
                break;
            case 'password':
                result = this.validatePassword(fieldValue);
                break;
            case 'tel':
                if (fieldValue.trim()) {
                    result = this.validatePhone(fieldValue);
                }
                break;
            case 'text':
                if (fieldName === 'firstName' || fieldName === 'lastName') {
                    result = this.validateName(fieldValue, fieldName === 'firstName' ? 'First name' : 'Last name');
                }
                break;
        }
        
        this.showFieldError(field.id, result.valid ? '' : result.message);
        return result.valid;
    }
}

// Create global validator instance
const formValidator = new FormValidator();