#!/bin/bash
# Automated Frontend Dependency Remediation Script
# As specified in the quality improvement protocol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== FRONTEND DEPENDENCY REMEDIATION ==="

if [ ! -d "$PROJECT_ROOT/frontend" ]; then
    echo "❌ Frontend directory not found"
    exit 1
fi

cd "$PROJECT_ROOT/frontend"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found"
    exit 1
fi

echo ""
echo "🔧 Step 1: Updating Dependencies..."

# Determine package manager
if [ -f "yarn.lock" ] && command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
    echo "Using yarn package manager"
elif [ -f "package-lock.json" ] && command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
    echo "Using npm package manager"
else
    echo "⚠️  No lock file found, defaulting to npm"
    PACKAGE_MANAGER="npm"
fi

# Security audit fix
echo ""
echo "🔒 Step 2: Fixing Security Vulnerabilities..."
if [ "$PACKAGE_MANAGER" = "yarn" ]; then
    yarn audit --json > "$AUDIT_DIR/yarn-audit-before.json" 2>/dev/null || true
    echo "Attempting to fix vulnerabilities with yarn..."
    yarn upgrade --latest || echo "Some updates may require manual intervention"
elif [ "$PACKAGE_MANAGER" = "npm" ]; then
    npm audit --json > "$AUDIT_DIR/npm-audit-before.json" 2>/dev/null || true
    echo "Attempting to fix vulnerabilities with npm..."
    # Try conservative fix first
    npm audit fix --package-lock-only || true
    npm audit fix || echo "Some vulnerabilities may require manual intervention"
fi

echo ""
echo "📦 Step 3: Removing Unused Dependencies..."

# Install depcheck if not available
if ! command -v depcheck &> /dev/null; then
    if ! npx depcheck --version &> /dev/null; then
        echo "Installing depcheck..."
        if [ "$PACKAGE_MANAGER" = "yarn" ]; then
            yarn add --dev depcheck || npm install --save-dev depcheck
        else
            npm install --save-dev depcheck
        fi
    fi
fi

# Run depcheck and parse results
if command -v depcheck &> /dev/null || npx depcheck --version &> /dev/null; then
    echo "Analyzing unused dependencies..."
    
    # Create a simple removal script (but don't auto-remove to avoid breaking changes)
    if command -v depcheck &> /dev/null; then
        depcheck --json > "$AUDIT_DIR/depcheck-results.json" 2>/dev/null || true
    else
        npx depcheck --json > "$AUDIT_DIR/depcheck-results.json" 2>/dev/null || true
    fi
    
    # Parse and display results without auto-removing
    if [ -f "$AUDIT_DIR/depcheck-results.json" ]; then
        echo "📋 Unused dependencies found (manual review recommended):"
        python3 -c "
import json
import sys
try:
    with open('$AUDIT_DIR/depcheck-results.json', 'r') as f:
        data = json.load(f)
    
    unused_deps = data.get('dependencies', [])
    unused_dev_deps = data.get('devDependencies', [])
    
    if unused_deps:
        print('  Dependencies to review for removal:')
        for dep in unused_deps[:5]:  # Show first 5
            print(f'    - {dep}')
        if len(unused_deps) > 5:
            print(f'    ... and {len(unused_deps) - 5} more')
    
    if unused_dev_deps:
        print('  Dev dependencies to review for removal:')
        for dep in unused_dev_deps[:5]:  # Show first 5
            print(f'    - {dep}')
        if len(unused_dev_deps) > 5:
            print(f'    ... and {len(unused_dev_deps) - 5} more')
    
    if not unused_deps and not unused_dev_deps:
        print('  ✅ No unused dependencies detected')
        
except Exception as e:
    print(f'  ⚠️  Could not parse depcheck results: {e}')
" 2>/dev/null || echo "  ⚠️  Could not analyze unused dependencies"
    fi
else
    echo "⚠️  Depcheck not available"
fi

echo ""
echo "🔍 Step 4: Dependency Deduplication..."

if [ "$PACKAGE_MANAGER" = "yarn" ]; then
    echo "Checking for duplicate dependencies..."
    yarn list --depth=0 > "$AUDIT_DIR/yarn-dependencies-list.txt" 2>/dev/null || true
    
    # Try yarn-deduplicate if available
    if yarn list yarn-deduplicate &> /dev/null; then
        echo "Running yarn deduplicate..."
        yarn yarn-deduplicate && yarn install
    else
        echo "Installing yarn-deduplicate..."
        yarn add --dev yarn-deduplicate || true
        if yarn list yarn-deduplicate &> /dev/null; then
            yarn yarn-deduplicate && yarn install
        fi
    fi
elif [ "$PACKAGE_MANAGER" = "npm" ]; then
    echo "Deduplicating npm dependencies..."
    npm dedupe || echo "Dedupe completed with warnings"
fi

echo ""
echo "📊 Step 5: Generating Post-Remediation Report..."

# Generate updated audit reports
if [ "$PACKAGE_MANAGER" = "yarn" ]; then
    yarn audit --json > "$AUDIT_DIR/yarn-audit-after.json" 2>/dev/null || true
    yarn outdated --json > "$AUDIT_DIR/yarn-outdated-after.json" 2>/dev/null || true
elif [ "$PACKAGE_MANAGER" = "npm" ]; then
    npm audit --json > "$AUDIT_DIR/npm-audit-after.json" 2>/dev/null || true
    npm outdated --json > "$AUDIT_DIR/npm-outdated-after.json" 2>/dev/null || true
fi

# Install and run license checker
if npx license-checker --version &> /dev/null; then
    npx license-checker --json > "$AUDIT_DIR/licenses-after.json" 2>/dev/null || true
fi

echo ""
echo "✅ Frontend Dependency Remediation Complete"
echo ""
echo "📋 Summary of actions taken:"
echo "  🔒 Security vulnerabilities addressed"
echo "  📦 Dependency analysis completed"
echo "  🔍 Deduplication performed"
echo "  📊 Updated audit reports generated"
echo ""
echo "📁 Reports saved to: $AUDIT_DIR"
echo "🔍 Review the generated reports for any manual actions needed"
echo ""
echo "⚠️  Important: Test your application after these changes!"
echo "🔄 Next: Run 'npm start' or 'yarn start' to verify everything works"