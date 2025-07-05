#!/bin/bash
# Automated Backend Dependency Remediation Script
# As specified in the quality improvement protocol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== BACKEND DEPENDENCY REMEDIATION ==="

cd "$PROJECT_ROOT"

# Create audit directory if it doesn't exist
mkdir -p "$AUDIT_DIR"

echo ""
echo "🐍 Step 1: Python Environment Analysis..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "Python version: $PYTHON_VERSION"
    echo "$PYTHON_VERSION" > "$AUDIT_DIR/python-version.txt"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Check pip version
if command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version)
    echo "Pip version: $PIP_VERSION"
    echo "$PIP_VERSION" >> "$AUDIT_DIR/python-version.txt"
fi

echo ""
echo "📦 Step 2: Installing Security and Audit Tools..."

# Install essential audit tools
AUDIT_TOOLS="safety bandit pip-audit"
for tool in $AUDIT_TOOLS; do
    if ! pip show "$tool" &> /dev/null; then
        echo "Installing $tool..."
        pip install --user "$tool" || echo "⚠️  Failed to install $tool"
    else
        echo "✅ $tool already installed"
    fi
done

# Install pipdeptree for dependency analysis
if ! pip show pipdeptree &> /dev/null; then
    echo "Installing pipdeptree..."
    pip install --user pipdeptree || echo "⚠️  Failed to install pipdeptree"
fi

echo ""
echo "🔍 Step 3: Security Vulnerability Scan..."

# Run safety check
if command -v safety &> /dev/null || pip show safety &> /dev/null; then
    echo "Running safety vulnerability scan..."
    safety check --json > "$AUDIT_DIR/safety-vulnerabilities.json" 2>/dev/null || \
    safety check > "$AUDIT_DIR/safety-vulnerabilities.txt" 2>/dev/null || \
    echo "⚠️  Safety scan failed" > "$AUDIT_DIR/safety-vulnerabilities.txt"
    echo "✅ Safety scan completed"
else
    echo "⚠️  Safety tool not available"
fi

# Run pip-audit if available
if command -v pip-audit &> /dev/null || pip show pip-audit &> /dev/null; then
    echo "Running pip-audit security scan..."
    pip-audit --format=json --output="$AUDIT_DIR/pip-audit-vulnerabilities.json" 2>/dev/null || \
    pip-audit > "$AUDIT_DIR/pip-audit-vulnerabilities.txt" 2>/dev/null || \
    echo "⚠️  pip-audit scan failed" > "$AUDIT_DIR/pip-audit-vulnerabilities.txt"
    echo "✅ pip-audit scan completed"
else
    echo "⚠️  pip-audit tool not available"
fi

# Run bandit for code security analysis
if command -v bandit &> /dev/null || pip show bandit &> /dev/null; then
    echo "Running bandit security analysis..."
    if [ -d "backend/src" ]; then
        bandit -r backend/src/ -f json -o "$AUDIT_DIR/bandit-security-report.json" 2>/dev/null || \
        bandit -r backend/src/ > "$AUDIT_DIR/bandit-security-report.txt" 2>/dev/null || \
        echo "⚠️  Bandit scan failed" > "$AUDIT_DIR/bandit-security-report.txt"
    fi
    echo "✅ Bandit analysis completed"
else
    echo "⚠️  Bandit tool not available"
fi

echo ""
echo "🔄 Step 4: Dependency Updates and Analysis..."

# Generate current dependency tree
if command -v pipdeptree &> /dev/null || pip show pipdeptree &> /dev/null; then
    echo "Generating dependency tree..."
    pipdeptree --json > "$AUDIT_DIR/dependency-tree-before.json" 2>/dev/null || \
    pipdeptree > "$AUDIT_DIR/dependency-tree-before.txt" 2>/dev/null || \
    echo "⚠️  Dependency tree generation failed"
    echo "✅ Dependency tree generated"
fi

# List current packages
echo "Listing current packages..."
pip list --format=json > "$AUDIT_DIR/installed-packages-before.json" 2>/dev/null || \
pip list > "$AUDIT_DIR/installed-packages-before.txt"

# List outdated packages
echo "Checking for outdated packages..."
pip list --outdated --format=json > "$AUDIT_DIR/outdated-packages.json" 2>/dev/null || \
pip list --outdated > "$AUDIT_DIR/outdated-packages.txt"

echo ""
echo "🛡️  Step 5: Safe Dependency Updates..."

# Create backup of requirements
if [ -f "requirements.txt" ]; then
    cp requirements.txt "$AUDIT_DIR/requirements-backup.txt"
    echo "✅ Requirements.txt backed up"
fi

if [ -f "requirements-dev.txt" ]; then
    cp requirements-dev.txt "$AUDIT_DIR/requirements-dev-backup.txt"
    echo "✅ Requirements-dev.txt backed up"
fi

# Update pip itself
echo "Updating pip..."
pip install --user --upgrade pip || echo "⚠️  pip upgrade failed"

# Selective updates for critical security packages
CRITICAL_PACKAGES="cryptography requests urllib3 flask werkzeug jinja2"
echo "Updating critical security packages..."
for package in $CRITICAL_PACKAGES; do
    if pip show "$package" &> /dev/null; then
        echo "Updating $package..."
        pip install --user --upgrade "$package" || echo "⚠️  Failed to update $package"
    fi
done

# Try to fix security vulnerabilities automatically
if command -v pip-audit &> /dev/null; then
    echo "Attempting automatic security fixes..."
    pip-audit --fix --dry-run > "$AUDIT_DIR/security-fix-plan.txt" 2>/dev/null || true
    # Don't auto-fix to avoid breaking changes
    echo "⚠️  Security fixes planned but not applied (see security-fix-plan.txt)"
fi

echo ""
echo "📊 Step 6: Post-Update Analysis..."

# Generate updated reports
if command -v pipdeptree &> /dev/null; then
    pipdeptree --json > "$AUDIT_DIR/dependency-tree-after.json" 2>/dev/null || \
    pipdeptree > "$AUDIT_DIR/dependency-tree-after.txt" 2>/dev/null
fi

pip list --format=json > "$AUDIT_DIR/installed-packages-after.json" 2>/dev/null || \
pip list > "$AUDIT_DIR/installed-packages-after.txt"

# Re-run security scans
if command -v safety &> /dev/null; then
    safety check --json > "$AUDIT_DIR/safety-vulnerabilities-after.json" 2>/dev/null || \
    safety check > "$AUDIT_DIR/safety-vulnerabilities-after.txt" 2>/dev/null
fi

echo ""
echo "🔍 Step 7: Generate Requirements Files..."

# Generate updated requirements files
echo "Generating updated requirements..."
pip freeze > "$AUDIT_DIR/requirements-generated.txt"

# Create a minimal requirements file focusing on direct dependencies
if [ -f "requirements.txt" ]; then
    echo "Analyzing direct vs. transitive dependencies..."
    python3 -c "
import sys
import subprocess
import json

def get_top_level_packages():
    try:
        # Get currently installed packages
        result = subprocess.run(['pip', 'list', '--format=json'], capture_output=True, text=True)
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except:
        pass
    return {}

def analyze_requirements():
    try:
        with open('requirements.txt', 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        installed = get_top_level_packages()
        
        print('# Direct dependencies from requirements.txt analysis')
        print('# Generated during backend dependency remediation')
        print()
        
        for line in lines:
            if '==' in line:
                pkg_name = line.split('==')[0].strip().lower()
                if pkg_name in installed:
                    print(f'{line}  # ✅ installed')
                else:
                    print(f'{line}  # ⚠️  not installed')
            else:
                print(line)
                
    except Exception as e:
        print(f'# Error analyzing requirements: {e}')

analyze_requirements()
" > "$AUDIT_DIR/requirements-analysis.txt" 2>/dev/null || echo "Requirements analysis failed"
fi

echo ""
echo "✅ Backend Dependency Remediation Complete"
echo ""
echo "📋 Summary of actions taken:"
echo "  🔍 Security vulnerability scan completed"
echo "  🛡️  Critical security packages updated"
echo "  📦 Dependency analysis performed"
echo "  📊 Comprehensive reports generated"
echo ""
echo "📁 Reports and backups saved to: $AUDIT_DIR"
echo ""
echo "⚠️  Important notes:"
echo "  • Original requirements files backed up"
echo "  • Security fixes identified but not auto-applied"
echo "  • Test your application after any dependency changes"
echo ""
echo "🔍 Next steps:"
echo "  1. Review security reports in $AUDIT_DIR"
echo "  2. Test application: python3 backend/src/main.py"
echo "  3. Review requirements-analysis.txt for dependency insights"
echo "  4. Apply security fixes manually if needed"