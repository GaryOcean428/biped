# TradeHub Platform API Documentation

## Overview
This document provides comprehensive API documentation for the TradeHub Platform, covering all endpoints, authentication, and usage examples.

## Base URL
- **Production**: `https://your-domain.com/api`
- **Development**: `http://localhost:8080/api`

## Authentication
The platform uses session-based authentication with secure cookies.

### Rate Limiting
- **Authentication endpoints**: 10 requests per 5 minutes
- **General API endpoints**: 100 requests per 15 minutes
- **Strict endpoints**: 30 requests per 10 minutes

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Seconds until rate limit resets

## Health & Monitoring Endpoints

### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "TradeHub Platform API",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### GET /health/detailed
Detailed health check with system metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "database": {
    "healthy": true,
    "latency_ms": 25.3
  },
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 67.8,
    "disk_percent": 42.1
  },
  "application": {
    "request_count": 1547,
    "error_count": 3,
    "error_rate": 0.19
  }
}
```

### GET /health/ready
Readiness check for load balancers.

**Response:**
```json
{
  "ready": true,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "checks": {
    "database": "ready",
    "service_categories": "ready"
  }
}
```

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Rate Limit:** 10 requests per 5 minutes

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "Password123",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "customer",
  "phone": "+1234567890",
  "city": "New York",
  "state": "NY"
}
```

**Validation Rules:**
- `email`: Valid email format, max 254 characters
- `password`: Min 8 characters, must contain uppercase, lowercase, and number
- `first_name`, `last_name`: 1-50 characters, required
- `user_type`: Must be "customer" or "provider"
- `phone`: Valid phone format (optional)

**Success Response (201):**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Password must contain at least one uppercase letter",
  "error_type": "validation_error",
  "timestamp": "POST /api/auth/register",
  "status_code": 400
}
```

### POST /auth/login
Authenticate user and create session.

**Rate Limit:** 10 requests per 5 minutes

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "Password123"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer"
  },
  "profile": {
    "preferred_contact_method": "email"
  }
}
```

**Error Response (401):**
```json
{
  "error": "Invalid email or password",
  "error_type": "authentication_error",
  "timestamp": "POST /api/auth/login",
  "status_code": 401
}
```

### POST /auth/logout
Logout user and clear session.

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

### GET /auth/me
Get current authenticated user information.

**Success Response (200):**
```json
{
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer"
  },
  "profile": {
    "preferred_contact_method": "email"
  }
}
```

## Error Handling

### Error Response Format
All API errors follow a consistent format:

```json
{
  "error": "Human-readable error message",
  "error_type": "error_category",
  "timestamp": "HTTP_METHOD /api/endpoint",
  "status_code": 400
}
```

### Error Types
- `validation_error` (400): Input validation failed
- `authentication_error` (401): Authentication required or failed
- `authorization_error` (403): Insufficient permissions
- `not_found_error` (404): Resource not found
- `server_error` (500): Internal server error

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `409`: Conflict (duplicate resource)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error
- `503`: Service Unavailable

## Input Validation

### Email Validation
- Must be valid email format
- Maximum 254 characters (RFC 5321 limit)
- Case-insensitive comparison

### Password Validation
- Minimum 8 characters
- Maximum 128 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one number

### String Validation
- HTML tags are sanitized to prevent XSS
- Dangerous protocols (javascript:) are removed
- Length limits enforced per field

### Phone Number Validation
- Supports US/International formats
- Optional field in most contexts
- Regex pattern: `^\+?1?-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$`

## Security Features

### XSS Prevention
- HTML sanitization on all text inputs
- Removal of dangerous tags: `<script>`, `<iframe>`, `<object>`, `<embed>`
- JavaScript protocol removal

### Rate Limiting
- IP-based tracking
- Configurable limits per endpoint
- Automatic cleanup of old requests
- HTTP headers for client awareness

### Session Security
- Secure session cookies
- Session timeout
- CSRF protection (when enabled)

### Input Sanitization
- Length limits to prevent DoS
- Format validation for all inputs
- SQL injection prevention through ORM

## Development & Testing

### Health Check URLs
```bash
# Basic health
curl http://localhost:8080/api/health

# Detailed health
curl http://localhost:8080/api/health/detailed

# Readiness check
curl http://localhost:8080/api/health/ready

# Liveness check
curl http://localhost:8080/api/health/live
```

### Example Registration Test
```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "User",
    "user_type": "customer"
  }'
```

### Example Login Test
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

## Client-Side Integration

### JavaScript Validation
```javascript
// Validate form before submission
const validation = formValidator.validateRegistrationForm(formData);
if (!validation.valid) {
  // Show errors
  Object.keys(validation.errors).forEach(field => {
    formValidator.showFieldError(field, validation.errors[field]);
  });
  return;
}
```

### Loading States
```javascript
// Show loading during API call
const resetLoading = loadingManager.handleFormSubmission('loginForm', 'loginBtn', 'Signing in...');

try {
  await apiCall('/auth/login', { method: 'POST', body: JSON.stringify(data) });
} finally {
  resetLoading();
}
```

## Production Considerations

### Performance
- Enable response compression
- Use CDN for static assets
- Implement database connection pooling
- Add request/response caching

### Monitoring
- Log all authentication events
- Monitor rate limit violations
- Track error rates and response times
- Set up health check alerts

### Security
- Use HTTPS in production
- Enable CSRF protection
- Implement proper CORS policies
- Regular security audits

This API documentation covers the core functionality and quality improvements implemented. For additional endpoints and features, refer to the specific route files in the `backend/src/routes/` directory.