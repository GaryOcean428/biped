#!/bin/bash
# Quick Dependency and Quality Audit
# Streamlined version for rapid assessment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== QUICK QUALITY AUDIT ==="
echo "Project Root: $PROJECT_ROOT"

# Create audit directory
mkdir -p "$AUDIT_DIR"

echo ""
echo "=== Backend Dependency Analysis ==="

cd "$PROJECT_ROOT"

# Python environment info
echo "Python Analysis:" > "$AUDIT_DIR/quick-audit-summary.txt"
python3 --version >> "$AUDIT_DIR/quick-audit-summary.txt"
pip --version >> "$AUDIT_DIR/quick-audit-summary.txt"

# Installed packages
echo "Analyzing Python packages..."
pip list --format=json > "$AUDIT_DIR/python-packages.json" 2>/dev/null || \
pip list > "$AUDIT_DIR/python-packages.txt"

# Outdated packages
pip list --outdated --format=json > "$AUDIT_DIR/python-outdated.json" 2>/dev/null || \
pip list --outdated > "$AUDIT_DIR/python-outdated.txt"

# Security check
if command -v safety &> /dev/null; then
    echo "Running security scan..."
    safety check --json > "$AUDIT_DIR/safety-scan.json" 2>/dev/null || \
    safety check > "$AUDIT_DIR/safety-scan.txt" 2>/dev/null || \
    echo "Safety scan failed" > "$AUDIT_DIR/safety-scan.txt"
else
    echo "Safety tool not available" > "$AUDIT_DIR/safety-scan.txt"
fi

echo ""
echo "=== Frontend Analysis ==="

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"
    
    echo "Frontend package.json analysis:" >> "$AUDIT_DIR/quick-audit-summary.txt"
    if [ -f "package.json" ]; then
        echo "Dependencies count:" >> "$AUDIT_DIR/quick-audit-summary.txt"
        grep -c '".*":' package.json >> "$AUDIT_DIR/quick-audit-summary.txt" 2>/dev/null || echo "0" >> "$AUDIT_DIR/quick-audit-summary.txt"
        
        # Copy package.json for analysis
        cp package.json "$AUDIT_DIR/frontend-package.json"
        
        # NPM audit (quick)
        if command -v npm &> /dev/null; then
            echo "Running npm audit..."
            npm audit --json > "$AUDIT_DIR/npm-audit.json" 2>/dev/null || \
            npm audit > "$AUDIT_DIR/npm-audit.txt" 2>&1 || \
            echo "NPM audit completed with issues"
        fi
    fi
else
    echo "Frontend directory not found" >> "$AUDIT_DIR/quick-audit-summary.txt"
fi

echo ""
echo "=== Code Quality Check ==="

cd "$PROJECT_ROOT"

# Run linting (quick check)
if [ -d "backend/src" ]; then
    echo "Backend code quality:" >> "$AUDIT_DIR/quick-audit-summary.txt"
    
    # Count Python files
    PYTHON_FILES=$(find backend/src -name "*.py" | wc -l)
    echo "Python files: $PYTHON_FILES" >> "$AUDIT_DIR/quick-audit-summary.txt"
    
    # Quick flake8 check
    if command -v flake8 &> /dev/null; then
        echo "Running quick linting check..."
        flake8 backend/src/ --count --statistics > "$AUDIT_DIR/flake8-quick.txt" 2>&1 || \
        echo "Linting issues found"
    fi
    
    # Line count analysis
    find backend/src -name "*.py" -exec wc -l {} + > "$AUDIT_DIR/python-line-counts.txt" 2>/dev/null || true
fi

echo ""
echo "=== Test Coverage Check ==="

# Run a quick test to see current status
if [ -d "tests" ]; then
    echo "Test framework status:" >> "$AUDIT_DIR/quick-audit-summary.txt"
    
    # Count test files
    TEST_FILES=$(find tests -name "test_*.py" | wc -l)
    echo "Test files: $TEST_FILES" >> "$AUDIT_DIR/quick-audit-summary.txt"
    
    # Try running tests quickly
    if command -v pytest &> /dev/null; then
        echo "Running quick test check..."
        PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH" pytest tests/ --tb=no -q > "$AUDIT_DIR/test-quick-results.txt" 2>&1 || \
        echo "Some tests failed (see test-quick-results.txt)"
    fi
fi

echo ""
echo "=== Security Assessment ==="

# Check for potential security issues
echo "Security assessment:" >> "$AUDIT_DIR/quick-audit-summary.txt"

# Look for common security anti-patterns
if [ -d "backend/src" ]; then
    echo "Checking for hardcoded secrets..."
    grep -r -i "password.*=" backend/src/ > "$AUDIT_DIR/security-password-check.txt" 2>/dev/null || \
    echo "No obvious password patterns found" > "$AUDIT_DIR/security-password-check.txt"
    
    grep -r -i "secret.*=" backend/src/ > "$AUDIT_DIR/security-secret-check.txt" 2>/dev/null || \
    echo "No obvious secret patterns found" > "$AUDIT_DIR/security-secret-check.txt"
    
    grep -r -i "api.*key" backend/src/ > "$AUDIT_DIR/security-apikey-check.txt" 2>/dev/null || \
    echo "No obvious API key patterns found" > "$AUDIT_DIR/security-apikey-check.txt"
fi

echo ""
echo "=== Infrastructure Check ==="

# Check deployment configuration
echo "Infrastructure assessment:" >> "$AUDIT_DIR/quick-audit-summary.txt"

[ -f "Dockerfile" ] && echo "✅ Dockerfile present" >> "$AUDIT_DIR/quick-audit-summary.txt"
[ -f "railway.toml" ] && echo "✅ Railway config present" >> "$AUDIT_DIR/quick-audit-summary.txt"
[ -f "requirements.txt" ] && echo "✅ Requirements.txt present" >> "$AUDIT_DIR/quick-audit-summary.txt"
[ -f "Makefile" ] && echo "✅ Makefile present" >> "$AUDIT_DIR/quick-audit-summary.txt"
[ -f ".gitignore" ] && echo "✅ .gitignore present" >> "$AUDIT_DIR/quick-audit-summary.txt"

echo ""
echo "=== Quick Audit Summary ==="

# Generate final summary
cat > "$AUDIT_DIR/audit-executive-summary.txt" << EOF
Quick Quality Audit Summary
===========================
Generated: $(date)

AUDIT SCOPE:
- Backend Python codebase
- Frontend React application  
- Dependencies and security
- Code quality and testing
- Infrastructure configuration

KEY FINDINGS:
EOF

# Add findings based on what we discovered
if [ -f "$AUDIT_DIR/python-packages.txt" ]; then
    PACKAGE_COUNT=$(wc -l < "$AUDIT_DIR/python-packages.txt" 2>/dev/null || echo "0")
    echo "- Python packages installed: $PACKAGE_COUNT" >> "$AUDIT_DIR/audit-executive-summary.txt"
fi

if [ -f "$AUDIT_DIR/python-outdated.txt" ]; then
    OUTDATED_COUNT=$(grep -c ".*" "$AUDIT_DIR/python-outdated.txt" 2>/dev/null || echo "0")
    echo "- Outdated Python packages: $OUTDATED_COUNT" >> "$AUDIT_DIR/audit-executive-summary.txt"
fi

if [ -f "$AUDIT_DIR/npm-audit.json" ]; then
    echo "- Frontend security audit: Completed (see npm-audit.json)" >> "$AUDIT_DIR/audit-executive-summary.txt"
elif [ -f "$AUDIT_DIR/npm-audit.txt" ]; then
    echo "- Frontend security audit: Completed (see npm-audit.txt)" >> "$AUDIT_DIR/audit-executive-summary.txt"
fi

if [ -f "$AUDIT_DIR/flake8-quick.txt" ]; then
    echo "- Backend code quality: Analysis completed (see flake8-quick.txt)" >> "$AUDIT_DIR/audit-executive-summary.txt"
fi

if [ -f "$AUDIT_DIR/test-quick-results.txt" ]; then
    echo "- Test suite: Analysis completed (see test-quick-results.txt)" >> "$AUDIT_DIR/audit-executive-summary.txt"
fi

cat >> "$AUDIT_DIR/audit-executive-summary.txt" << EOF

RECOMMENDATIONS:
1. Review security scan results in safety-scan.txt
2. Update outdated packages listed in python-outdated.txt
3. Address linting issues in flake8-quick.txt
4. Review frontend security issues in npm-audit.txt
5. Enhance test coverage if needed

NEXT STEPS:
- Run comprehensive remediation scripts
- Implement automated quality gates
- Set up continuous monitoring
- Address critical security findings

REPORTS GENERATED:
EOF

ls -1 "$AUDIT_DIR"/*.txt "$AUDIT_DIR"/*.json 2>/dev/null | sed 's/.*\//- /' >> "$AUDIT_DIR/audit-executive-summary.txt" || true

echo ""
echo "📊 Quick audit completed successfully!"
echo "📁 Reports saved to: $AUDIT_DIR"
echo ""
echo "📋 Executive Summary:"
cat "$AUDIT_DIR/audit-executive-summary.txt"
echo ""
echo "🔍 Review detailed reports in the audit-reports directory"
echo "🚀 Next: Run remediation scripts to address findings"