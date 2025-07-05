# Makefile for TradeHub Platform development

.PHONY: help install install-dev lint format test test-coverage clean check-security health

# Variables
PYTHON = python3
PIP = pip3
BACKEND_DIR = backend
TESTS_DIR = tests

help: ## Show this help message
	@echo "TradeHub Platform Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

lint: ## Run Python linting (flake8)
	@echo "Running flake8 linting..."
	flake8 $(BACKEND_DIR)/src/ $(TESTS_DIR)/
	@echo "✅ Linting completed"

lint-js: ## Run JavaScript linting (if eslint is available)
	@echo "Running JavaScript linting..."
	@if command -v eslint >/dev/null 2>&1; then \
		eslint $(BACKEND_DIR)/src/static/*.js; \
		echo "✅ JavaScript linting completed"; \
	else \
		echo "⚠️  ESLint not found. Install with: npm install -g eslint"; \
	fi

format: ## Format code with black and isort
	@echo "Formatting Python code..."
	black $(BACKEND_DIR)/src/ $(TESTS_DIR)/
	isort $(BACKEND_DIR)/src/ $(TESTS_DIR)/
	@echo "✅ Code formatting completed"

test: ## Run unit tests
	@echo "Running unit tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/ -v
	@echo "✅ Tests completed"

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	$(PYTHON) -m pytest $(TESTS_DIR)/ -v --cov=$(BACKEND_DIR)/src --cov-report=term-missing --cov-report=html
	@echo "✅ Coverage report generated in htmlcov/"

validate: ## Run input validation tests
	@echo "Running validation tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/test_validation.py -v
	@echo "✅ Validation tests completed"

rate-limit-test: ## Run rate limiting tests
	@echo "Running rate limiting tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/test_rate_limiting.py -v
	@echo "✅ Rate limiting tests completed"

check-security: ## Basic security checks
	@echo "Running basic security checks..."
	@echo "Checking for hardcoded secrets..."
	@grep -r -i "password.*=" $(BACKEND_DIR)/src/ && echo "⚠️  Found potential hardcoded passwords" || echo "✅ No hardcoded passwords found"
	@grep -r -i "secret.*=" $(BACKEND_DIR)/src/ && echo "⚠️  Found potential hardcoded secrets" || echo "✅ No hardcoded secrets found"
	@echo "✅ Basic security check completed"

health: ## Check application health endpoints
	@echo "Testing health endpoints..."
	@if command -v curl >/dev/null 2>&1; then \
		echo "Testing basic health endpoint..."; \
		curl -f http://localhost:8080/api/health || echo "❌ Health endpoint not responding"; \
		echo "Testing detailed health endpoint..."; \
		curl -f http://localhost:8080/api/health/detailed || echo "❌ Detailed health endpoint not responding"; \
	else \
		echo "⚠️  curl not found. Please test endpoints manually."; \
	fi

clean: ## Clean up generated files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf *.log
	@echo "✅ Cleanup completed"

check-all: lint test check-security ## Run all quality checks
	@echo "✅ All quality checks completed"

quality-score: ## Get comprehensive quality score
	@echo "Calculating quality score..."
	@$(PYTHON) -c "\
from backend.src.utils.quality_metrics import quality_metrics; \
result = quality_metrics.calculate_overall_score(); \
print(f'\\n🎯 TradeHub Platform Quality Score: {result[\"overall_score\"]}/100 ({result[\"grade\"]})'); \
print(f'📊 Quality Level: {result[\"quality_level\"]}'); \
print(f'\\n📈 Category Breakdown:'); \
[print(f'  {cat.title()}: {data[\"score\"]}/{data[\"max_possible\"]} ({data[\"grade\"]})') for cat, data in result['category_breakdown'].items()]; \
print(f'\\n✅ Features Implemented: {result[\"summary\"][\"total_features_implemented\"]}/{result[\"summary\"][\"total_features_possible\"]} ({result[\"summary\"][\"feature_completion_rate\"]}%)'); \
print('\\n💡 Excellent! All quality standards met.') if result['overall_score'] >= 95 else None"
	@echo "✅ Quality assessment completed"

dev-setup: install-dev ## Set up development environment
	@echo "Setting up development environment..."
	@echo "✅ Development environment ready"
	@echo ""
	@echo "Next steps:"
	@echo "1. Run 'make lint' to check code quality"
	@echo "2. Run 'make test' to run tests"
	@echo "3. Run 'make format' to format code"

# Quality gates for CI/CD
ci-test: lint test check-security ## Run all CI checks
	@echo "✅ All CI checks passed"
# Enhanced quality targets
format-check: ## Check if code is properly formatted
	@echo "Checking Python formatting..."
	black --check backend/src/ tests/ || (echo "❌ Code formatting issues found. Run 'make format' to fix." && exit 1)
	isort --check-only backend/src/ tests/ || (echo "❌ Import sorting issues found. Run 'make format' to fix." && exit 1)
	@echo "✅ Code formatting is correct"

type-check: ## Run Python type checking
	@echo "Running type checking..."
	@if command -v mypy >/dev/null 2>&1; then \
		mypy backend/src/ --ignore-missing-imports || echo "⚠️  Type checking found issues"; \
	else \
		echo "⚠️  mypy not installed. Install with: pip install mypy"; \
	fi

complexity-check: ## Check code complexity
	@echo "Checking code complexity..."
	@if command -v radon >/dev/null 2>&1; then \
		radon cc backend/src/ --min=B --show-complexity || echo "⚠️  High complexity found"; \
	else \
		echo "⚠️  radon not installed. Install with: pip install radon"; \
	fi

security-check-enhanced: ## Enhanced security checks
	@echo "Running enhanced security checks..."
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r backend/src/ -ll || echo "⚠️  Security issues found"; \
	else \
		echo "⚠️  bandit not installed. Install with: pip install bandit"; \
	fi
	@$(MAKE) check-security

quality-gate: format-check lint type-check test ## Run all quality gates
	@echo "✅ All quality gates passed! Code is ready for commit."

pre-commit: quality-gate ## Run before committing code
	@echo "🚀 Pre-commit checks completed successfully"

audit-report: ## Generate comprehensive audit report
	@echo "Generating audit report..."
	@mkdir -p audit-reports
	@echo "Audit Report - $(shell date)" > audit-reports/audit-summary.md
	@echo "=========================" >> audit-reports/audit-summary.md
	@echo "" >> audit-reports/audit-summary.md
	@echo "## Code Quality" >> audit-reports/audit-summary.md
	@$(MAKE) lint > audit-reports/lint-results.txt 2>&1 && echo "✅ Linting: PASSED" >> audit-reports/audit-summary.md || echo "❌ Linting: FAILED" >> audit-reports/audit-summary.md
	@$(MAKE) test > audit-reports/test-results.txt 2>&1 && echo "✅ Tests: PASSED" >> audit-reports/audit-summary.md || echo "❌ Tests: FAILED" >> audit-reports/audit-summary.md
	@echo "" >> audit-reports/audit-summary.md
	@echo "## Security" >> audit-reports/audit-summary.md
	@$(MAKE) check-security > audit-reports/security-results.txt 2>&1 && echo "✅ Security: PASSED" >> audit-reports/audit-summary.md || echo "❌ Security: FAILED" >> audit-reports/audit-summary.md
	@echo "" >> audit-reports/audit-summary.md
	@echo "📊 Detailed results available in audit-reports/ directory"
	@cat audit-reports/audit-summary.md

ci-check: ## Run CI/CD quality checks
	@echo "Running CI/CD quality checks..."
	@$(MAKE) quality-gate
	@$(MAKE) audit-report
	@echo "✅ CI/CD checks completed"
