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