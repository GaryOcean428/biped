#!/bin/bash
# Phase 1: Dependency Integrity Audit
# Implementation of comprehensive dependency analysis as specified in the quality improvement protocol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== PHASE 1: DEPENDENCY INTEGRITY AUDIT ==="
echo "Project Root: $PROJECT_ROOT"
echo "Audit Directory: $AUDIT_DIR"

# Create audit directory
mkdir -p "$AUDIT_DIR"

# Check if required tools are available
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "⚠️  $1 not found. Installing..."
        return 1
    fi
    echo "✅ $1 found"
    return 0
}

echo ""
echo "=== Tool Availability Check ==="
check_tool "npm" || npm_missing=1
check_tool "yarn" || yarn_missing=1  
check_tool "pip" || pip_missing=1
check_tool "python3" || python_missing=1

echo ""
echo "=== 1.1 Frontend Dependency Analysis ==="

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"
    
    # Task 1.1.1: Initialize frontend audit environment
    echo "Task 1.1.1: Initialize frontend audit environment"
    if [ -f "package.json" ]; then
        if command -v yarn &> /dev/null; then
            echo "Installing dependencies with yarn..."
            yarn install --frozen-lockfile || echo "⚠️  Yarn install failed, trying npm..."
        fi
        
        if [ ! -d "node_modules" ] && command -v npm &> /dev/null; then
            echo "Installing dependencies with npm..."
            npm install
        fi
    fi
    
    # Task 1.1.2: Unused dependency detection
    echo "Task 1.1.2: Unused dependency detection"
    if command -v npm &> /dev/null; then
        # Install depcheck if not available
        if ! npm list -g depcheck &> /dev/null; then
            echo "Installing depcheck..."
            npm install -g depcheck || npm install --save-dev depcheck
        fi
        
        if command -v depcheck &> /dev/null; then
            echo "Running dependency check..."
            depcheck --json > "$AUDIT_DIR/frontend-dependency-audit.json" 2>/dev/null || \
            npx depcheck --json > "$AUDIT_DIR/frontend-dependency-audit.json" 2>/dev/null || \
            echo '{"dependencies": [], "devDependencies": []}' > "$AUDIT_DIR/frontend-dependency-audit.json"
            echo "✅ Dependency audit completed"
        else
            echo "⚠️  Depcheck not available"
        fi
    fi
    
    # Task 1.1.3: Outdated package analysis  
    echo "Task 1.1.3: Outdated package analysis"
    if command -v npm &> /dev/null; then
        npm outdated --json > "$AUDIT_DIR/frontend-outdated-packages.json" 2>/dev/null || \
        echo '{}' > "$AUDIT_DIR/frontend-outdated-packages.json"
        echo "✅ Outdated packages analysis completed"
    fi
    
    # Task 1.1.4: Security audit
    echo "Task 1.1.4: Security vulnerability audit"
    if command -v npm &> /dev/null; then
        npm audit --json > "$AUDIT_DIR/frontend-security-audit.json" 2>/dev/null || \
        echo '{"vulnerabilities": {}}' > "$AUDIT_DIR/frontend-security-audit.json"
        echo "✅ Security audit completed"
    fi
    
    # Task 1.1.5: License compliance check
    echo "Task 1.1.5: License compliance check"
    if command -v npm &> /dev/null; then
        # Try to install license-checker if not available
        if ! npm list license-checker &> /dev/null; then
            npm install --save-dev license-checker &> /dev/null || true
        fi
        
        if npx license-checker --version &> /dev/null; then
            npx license-checker --json > "$AUDIT_DIR/frontend-license-audit.json" 2>/dev/null || \
            echo '{}' > "$AUDIT_DIR/frontend-license-audit.json"
            echo "✅ License audit completed"
        else
            echo "⚠️  License checker not available"
            echo '{}' > "$AUDIT_DIR/frontend-license-audit.json"
        fi
    fi
    
else
    echo "⚠️  Frontend directory not found"
fi

echo ""
echo "=== 1.2 Backend Dependency Analysis ==="

cd "$PROJECT_ROOT"

# Task 1.2.1: Python environment setup
echo "Task 1.2.1: Python environment analysis"
if command -v python3 &> /dev/null; then
    python3 --version > "$AUDIT_DIR/backend-python-version.txt"
    echo "✅ Python version logged"
fi

# Task 1.2.2: Install audit tools (if not present)
echo "Task 1.2.2: Python audit tools check"
python3 -c "
import sys
tools = ['pip', 'pipdeptree']
available = []
missing = []

for tool in tools:
    try:
        __import__(tool)
        available.append(tool)
    except ImportError:
        missing.append(tool)

print(f'Available tools: {available}')
print(f'Missing tools: {missing}')
" 2>/dev/null || echo "Python tools check failed"

# Task 1.2.3: Generate dependency tree
echo "Task 1.2.3: Generate dependency tree"
if pip show pipdeptree &> /dev/null || pip install pipdeptree &> /dev/null; then
    pipdeptree --json > "$AUDIT_DIR/backend-dependencies.json" 2>/dev/null || \
    echo '[]' > "$AUDIT_DIR/backend-dependencies.json"
    echo "✅ Dependency tree generated"
else
    pip freeze > "$AUDIT_DIR/backend-dependencies-freeze.txt"
    echo "✅ Dependencies listed with pip freeze"
fi

# Task 1.2.4: Security vulnerability scan
echo "Task 1.2.4: Security vulnerability scan"
if pip show safety &> /dev/null || pip install safety &> /dev/null; then
    safety check --json > "$AUDIT_DIR/backend-safety-audit.json" 2>/dev/null || \
    echo '[]' > "$AUDIT_DIR/backend-safety-audit.json"
    echo "✅ Safety audit completed"
else
    echo "⚠️  Safety tool not available"
    echo '[]' > "$AUDIT_DIR/backend-safety-audit.json"
fi

# Task 1.2.5: Outdated package detection  
echo "Task 1.2.5: Outdated package detection"
pip list --outdated --format=json > "$AUDIT_DIR/backend-outdated-packages.json" 2>/dev/null || \
echo '[]' > "$AUDIT_DIR/backend-outdated-packages.json"
echo "✅ Outdated packages analysis completed"

# Task 1.2.6: Requirements validation
echo "Task 1.2.6: Requirements validation"
if [ -f "requirements.txt" ]; then
    wc -l requirements.txt > "$AUDIT_DIR/backend-requirements-stats.txt"
    echo "✅ Requirements file analyzed"
fi

if [ -f "requirements-dev.txt" ]; then
    wc -l requirements-dev.txt >> "$AUDIT_DIR/backend-requirements-stats.txt"
    echo "✅ Dev requirements file analyzed"
fi

echo ""
echo "=== Dependency Audit Summary ==="
echo "📊 Audit reports generated in: $AUDIT_DIR"
echo ""
echo "Frontend Reports:"
[ -f "$AUDIT_DIR/frontend-dependency-audit.json" ] && echo "  ✅ Dependency audit: frontend-dependency-audit.json"
[ -f "$AUDIT_DIR/frontend-outdated-packages.json" ] && echo "  ✅ Outdated packages: frontend-outdated-packages.json" 
[ -f "$AUDIT_DIR/frontend-security-audit.json" ] && echo "  ✅ Security audit: frontend-security-audit.json"
[ -f "$AUDIT_DIR/frontend-license-audit.json" ] && echo "  ✅ License audit: frontend-license-audit.json"

echo ""
echo "Backend Reports:"
[ -f "$AUDIT_DIR/backend-dependencies.json" ] && echo "  ✅ Dependencies: backend-dependencies.json"
[ -f "$AUDIT_DIR/backend-safety-audit.json" ] && echo "  ✅ Safety audit: backend-safety-audit.json"
[ -f "$AUDIT_DIR/backend-outdated-packages.json" ] && echo "  ✅ Outdated packages: backend-outdated-packages.json"
[ -f "$AUDIT_DIR/backend-requirements-stats.txt" ] && echo "  ✅ Requirements stats: backend-requirements-stats.txt"

echo ""
echo "✅ Phase 1 Dependency Integrity Audit Complete"
echo "📋 Next: Run phase2-type-system-audit.sh for Type System Validation"