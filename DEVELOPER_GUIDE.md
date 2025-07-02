# Biped Platform Developer Guide

## 🚀 Welcome to Biped Platform Development

This comprehensive guide will help you understand, develop, and contribute to the Biped Platform - an AI-powered autonomous trades marketplace.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Getting Started](#getting-started)
3. [Development Environment](#development-environment)
4. [Code Structure](#code-structure)
5. [Security Guidelines](#security-guidelines)
6. [Performance Optimization](#performance-optimization)
7. [Testing Strategy](#testing-strategy)
8. [API Documentation](#api-documentation)
9. [Deployment Guide](#deployment-guide)
10. [Contributing Guidelines](#contributing-guidelines)

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/HTML)  │◄──►│   (Flask)       │◄──►│   (SQLite/PG)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   AI Engine     │              │
         └──────────────►│   (OpenAI)      │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   External      │
                        │   Services      │
                        │   (N8N/Flowise) │
                        └─────────────────┘
```

### Key Components

- **Frontend**: Modern responsive UI with design system
- **Backend API**: Flask-based REST API with security and performance features
- **AI Engine**: OpenAI integration for intelligent matching and automation
- **Security Layer**: Comprehensive security with authentication, authorization, and input validation
- **Performance Layer**: Caching, monitoring, and optimization utilities
- **Storage**: Persistent file storage with Railway volume support

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ (for frontend development)
- Git
- Railway CLI (for deployment)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd biped-platform
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

5. **Access the application**
   - Frontend: http://localhost:8080
   - API: http://localhost:8080/api
   - Dashboard: http://localhost:8080/dashboard.html

## 🛠️ Development Environment

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Application
SECRET_KEY=your-secret-key-here
DEBUG=True
PORT=8080

# Database
DATABASE_URL=sqlite:///biped.db
DATA_DIR=/data

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# External Services
N8N_WEBHOOK_URL=your-n8n-webhook
FLOWISE_API_URL=your-flowise-api

# Security
JWT_SECRET_KEY=your-jwt-secret
CSRF_SECRET_KEY=your-csrf-secret

# Performance
CACHE_TTL=3600
RATE_LIMIT_ENABLED=True
```

### Development Tools

- **Code Formatting**: Use Black for Python code formatting
- **Linting**: Use flake8 for Python linting
- **Testing**: Use pytest for running tests
- **Documentation**: Use Sphinx for API documentation

## 📁 Code Structure

```
biped-platform/
├── backend/
│   ├── src/
│   │   ├── main.py              # Application entry point
│   │   ├── models/              # Database models
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   └── financial.py
│   │   ├── routes/              # API routes
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── secure_api.py
│   │   │   └── storage.py
│   │   ├── utils/               # Utility modules
│   │   │   ├── security.py      # Security utilities
│   │   │   ├── performance.py   # Performance utilities
│   │   │   └── storage.py       # Storage utilities
│   │   └── static/              # Frontend assets
│   │       ├── css/
│   │       ├── js/
│   │       └── *.html
│   ├── tests/                   # Test files
│   │   ├── test_security.py
│   │   ├── test_performance.py
│   │   └── test_integration.py
│   └── requirements.txt         # Python dependencies
├── docs/                        # Documentation
├── deployment/                  # Deployment configurations
└── README.md
```

### Key Modules

#### Security Module (`utils/security.py`)

Provides comprehensive security features:

```python
from src.utils.security import (
    SecurityManager,
    require_auth,
    require_role,
    validate_csrf,
    sanitize_json_input,
    rate_limit
)

# Example usage
@require_auth
@require_role('admin')
@validate_csrf
@rate_limit(limit=10, window=3600)
def admin_endpoint():
    pass
```

#### Performance Module (`utils/performance.py`)

Provides performance optimization features:

```python
from src.utils.performance import (
    cache_result,
    monitor_performance,
    compress_response,
    paginate_query
)

# Example usage
@cache_result(ttl=300)
@monitor_performance
@compress_response
def expensive_operation():
    pass
```

## 🔒 Security Guidelines

### Authentication & Authorization

1. **JWT Tokens**: Use JWT for stateless authentication
2. **Role-Based Access**: Implement role hierarchy (user < provider < admin)
3. **CSRF Protection**: Validate CSRF tokens for state-changing operations
4. **Rate Limiting**: Implement rate limiting for all endpoints

### Input Validation

```python
# Always sanitize user input
from src.utils.security import security_manager

@sanitize_json_input
def api_endpoint():
    data = request.sanitized_json
    # Use sanitized data
```

### Security Best Practices

1. **Never trust user input** - Always validate and sanitize
2. **Use parameterized queries** - Prevent SQL injection
3. **Implement proper error handling** - Don't leak sensitive information
4. **Use HTTPS in production** - Encrypt data in transit
5. **Regular security audits** - Keep dependencies updated

## ⚡ Performance Optimization

### Caching Strategy

1. **Function-level caching** for expensive operations
2. **Database query caching** for frequently accessed data
3. **Static asset caching** with proper cache headers
4. **CDN integration** for global content delivery

### Database Optimization

```python
# Use pagination for large datasets
from src.utils.performance import paginate_query

def get_projects():
    query = Project.query.filter_by(status='active')
    return paginate_query(query, page=1, per_page=20)
```

### Frontend Optimization

1. **Code splitting** - Load only necessary code
2. **Lazy loading** - Load components on demand
3. **Asset minification** - Reduce file sizes
4. **Image optimization** - Use appropriate formats and sizes

## 🧪 Testing Strategy

### Test Types

1. **Unit Tests** - Test individual functions and classes
2. **Integration Tests** - Test component interactions
3. **Security Tests** - Test security features
4. **Performance Tests** - Test under load
5. **End-to-End Tests** - Test complete user workflows

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_security.py

# Run with coverage
python -m pytest --cov=src tests/

# Run performance tests
python tests/test_performance.py
```

### Test Structure

```python
import unittest
from src.utils.security import SecurityManager

class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        self.security_manager = SecurityManager()
    
    def test_password_validation(self):
        # Test implementation
        pass
```

## 📚 API Documentation

### Authentication Endpoints

#### POST /api/v1/auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "jwt-token-here",
  "csrf_token": "csrf-token-here",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user"
  }
}
```

#### POST /api/v1/auth/register
Register new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!",
  "name": "John Doe",
  "phone": "+1234567890"
}
```

### Project Endpoints

#### GET /api/v1/projects
Get paginated list of projects.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20)
- `status` (string): Filter by status
- `category` (string): Filter by category

#### POST /api/v1/projects
Create new project (requires provider role).

**Headers:**
- `Authorization: Bearer <token>`
- `X-CSRF-Token: <csrf-token>`

### Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

## 🚀 Deployment Guide

### Railway Deployment

1. **Prepare for deployment**
   ```bash
   # Ensure all tests pass
   python -m pytest tests/
   
   # Update requirements.txt
   pip freeze > requirements.txt
   ```

2. **Configure Railway**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Deploy
   railway up
   ```

3. **Environment Variables**
   Set the following in Railway dashboard:
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `DATABASE_URL`
   - `DATA_DIR=/data`

### Production Considerations

1. **Use production WSGI server** (Gunicorn)
2. **Enable HTTPS** with proper certificates
3. **Set up monitoring** and logging
4. **Configure backup strategy**
5. **Implement health checks**

## 🤝 Contributing Guidelines

### Code Style

1. **Python**: Follow PEP 8 guidelines
2. **JavaScript**: Use ES6+ features
3. **HTML/CSS**: Use semantic markup and BEM methodology
4. **Comments**: Write clear, concise comments

### Git Workflow

1. **Create feature branch** from main
2. **Make atomic commits** with clear messages
3. **Write tests** for new features
4. **Update documentation** as needed
5. **Submit pull request** with description

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(auth): add JWT token validation`
- `fix(security): prevent XSS in user input`
- `docs(api): update authentication endpoints`

### Pull Request Process

1. **Ensure tests pass** and coverage is maintained
2. **Update documentation** for API changes
3. **Add changelog entry** for user-facing changes
4. **Request review** from maintainers
5. **Address feedback** promptly

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>
```

#### Database Connection Issues
```bash
# Check database file permissions
ls -la data/biped.db

# Reset database
rm data/biped.db
python src/main.py  # Will recreate database
```

#### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:/path/to/biped-platform/backend"
```

### Performance Issues

1. **Check cache hit rates** in performance stats
2. **Monitor database query performance**
3. **Profile slow endpoints** using performance decorators
4. **Optimize database indexes**

### Security Issues

1. **Review security logs** for suspicious activity
2. **Check rate limiting** effectiveness
3. **Validate input sanitization**
4. **Audit dependencies** for vulnerabilities

## 📞 Support

### Getting Help

1. **Documentation**: Check this guide and API docs
2. **Issues**: Create GitHub issue with details
3. **Discussions**: Use GitHub discussions for questions
4. **Security**: Email security@biped.com for security issues

### Useful Commands

```bash
# Development
python src/main.py                    # Start development server
python -m pytest tests/              # Run tests
python -m pytest --cov=src tests/    # Run tests with coverage

# Production
gunicorn --bind 0.0.0.0:$PORT src.main:app  # Production server

# Database
python -c "from src.models.user import db; db.create_all()"  # Create tables

# Security
python tests/test_security.py        # Run security tests
```

## 📈 Monitoring & Analytics

### Performance Monitoring

Access performance stats at `/api/v1/performance/stats` (admin only):

```json
{
  "performance_stats": {
    "avg_response_time_projects": 0.15,
    "request_count_projects": 1250,
    "cache_hit_function": 850,
    "cache_miss_function": 125
  },
  "cache_stats": {
    "size": 245,
    "max_size": 1000,
    "hit_ratio": 0.87
  }
}
```

### Security Monitoring

Monitor security events through audit logs and security health checks at `/api/health/security`.

---

## 🎯 Next Steps

1. **Explore the codebase** - Start with `src/main.py`
2. **Run the tests** - Understand the test coverage
3. **Try the API** - Use the interactive dashboard
4. **Read the security guide** - Understand security features
5. **Contribute** - Pick an issue and submit a PR

Happy coding! 🚀

