# Code Quality Standards for Biped Platform

## Overview
This document outlines the code quality standards and practices for the Biped platform.

## Code Formatting
- **Python**: Use Black formatter with 88-character line length
- **JavaScript/TypeScript**: Use Prettier with provided configuration
- **Import Sorting**: Use isort for Python imports

## Linting Standards
- **Python**: Flake8 with project-specific configuration
- **JavaScript**: ESLint with React and accessibility plugins
- **Maximum Complexity**: 12 (cyclomatic complexity)

## Testing Requirements
- **Unit Tests**: All new functions must have unit tests
- **Integration Tests**: API endpoints must have integration tests
- **Test Coverage**: Aim for 80%+ coverage
- **Test Structure**: Use pytest fixtures and clear test names

## Security Standards
- **Input Validation**: All user inputs must be validated
- **Rate Limiting**: API endpoints must have rate limiting
- **Environment Variables**: Sensitive data in environment variables only
- **Dependencies**: Regular security scans and updates

## Development Workflow
1. Run `make format` before committing
2. Run `make lint` to check code quality
3. Run `make test` to ensure tests pass
4. Run `make quality-gate` for comprehensive check
5. Use `make pre-commit` before pushing code

## Quality Gates
The following checks must pass before code can be merged:
- [ ] Code formatting (Black, Prettier)
- [ ] Linting (Flake8, ESLint)
- [ ] Type checking (MyPy, TypeScript)
- [ ] Unit tests pass
- [ ] Security checks pass
- [ ] Code complexity within limits

## Tools and Configuration
- **Black**: Code formatting for Python
- **isort**: Import sorting for Python
- **Flake8**: Linting for Python
- **MyPy**: Type checking for Python
- **ESLint**: Linting for JavaScript/TypeScript
- **Prettier**: Code formatting for frontend
- **pytest**: Testing framework for Python
- **Bandit**: Security linting for Python

## Continuous Improvement
- Monthly dependency updates
- Quarterly security audits
- Annual tooling review
- Regular performance profiling
