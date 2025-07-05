#!/bin/bash
# Phase 3: Code Quality Analysis
# Implementation of comprehensive code quality audit as specified in the quality improvement protocol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== PHASE 3: CODE QUALITY ANALYSIS ==="

# Create audit directory
mkdir -p "$AUDIT_DIR"

echo ""
echo "=== 3.1 Frontend Code Quality ==="

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"
    
    # Task 3.1.1: Setup comprehensive linting
    echo "Task 3.1.1: Frontend linting setup"
    
    # Install ESLint and related packages if not present
    ESLINT_PACKAGES="eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y eslint-plugin-import prettier eslint-config-prettier eslint-plugin-prettier"
    
    echo "Checking ESLint setup..."
    for package in $ESLINT_PACKAGES; do
        if ! npm list "$package" &> /dev/null; then
            echo "Installing $package..."
            npm install --save-dev "$package" || echo "⚠️  Failed to install $package"
        fi
    done
    
    # Task 3.1.2: Generate comprehensive ESLint configuration
    echo "Task 3.1.2: ESLint configuration"
    
    # Backup existing config
    [ -f ".eslintrc.json" ] && cp .eslintrc.json "$AUDIT_DIR/eslintrc-backup.json"
    
    # Check if we should use TypeScript rules
    TS_FILES=$(find src -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l || echo "0")
    
    if [ "$TS_FILES" -gt 0 ]; then
        echo "Creating TypeScript-enabled ESLint configuration..."
        cat > .eslintrc.json << 'EOF'
{
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module",
    "ecmaFeatures": {
      "jsx": true
    }
  },
  "plugins": [
    "@typescript-eslint",
    "react",
    "react-hooks",
    "jsx-a11y",
    "import",
    "prettier"
  ],
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
    "plugin:import/recommended",
    "plugin:import/typescript",
    "prettier"
  ],
  "rules": {
    "prettier/prettier": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "error",
    "react/prop-types": "off",
    "react/react-in-jsx-scope": "off",
    "import/order": ["error", {
      "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
      "newlines-between": "always"
    }]
  },
  "settings": {
    "react": {
      "version": "detect"
    },
    "import/resolver": {
      "typescript": {}
    }
  }
}
EOF
    else
        echo "Creating JavaScript ESLint configuration..."
        cat > .eslintrc.json << 'EOF'
{
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module",
    "ecmaFeatures": {
      "jsx": true
    }
  },
  "plugins": [
    "react",
    "react-hooks",
    "jsx-a11y",
    "import",
    "prettier"
  ],
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
    "plugin:import/recommended",
    "prettier"
  ],
  "rules": {
    "prettier/prettier": "error",
    "no-unused-vars": "error",
    "react/prop-types": "warn",
    "react/react-in-jsx-scope": "off",
    "import/order": ["error", {
      "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
      "newlines-between": "always"
    }]
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
EOF
    fi
    echo "✅ ESLint configuration updated"
    
    # Task 3.1.3: Configure Prettier
    echo "Task 3.1.3: Prettier configuration"
    
    if [ ! -f ".prettierrc" ]; then
        cat > .prettierrc << 'EOF'
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
EOF
        echo "✅ Prettier configuration created"
    else
        echo "✅ Prettier configuration exists"
    fi
    
    # Task 3.1.4: Run comprehensive linting
    echo "Task 3.1.4: Running ESLint analysis"
    
    if npx eslint --version &> /dev/null; then
        echo "Running ESLint analysis..."
        npx eslint src/ --ext .ts,.tsx,.js,.jsx --format json > "$AUDIT_DIR/eslint-audit.json" 2>/dev/null || \
        npx eslint src/ --ext .ts,.tsx,.js,.jsx > "$AUDIT_DIR/eslint-audit.txt" 2>&1 || \
        echo "ESLint analysis completed with issues"
        
        # Count issues
        if [ -f "$AUDIT_DIR/eslint-audit.json" ]; then
            ESLINT_ISSUES=$(python3 -c "
import json
try:
    with open('$AUDIT_DIR/eslint-audit.json', 'r') as f:
        data = json.load(f)
    total_issues = sum(len(file_data.get('messages', [])) for file_data in data)
    print(f'ESLint issues found: {total_issues}')
except:
    print('Could not parse ESLint results')
" 2>/dev/null)
            echo "$ESLINT_ISSUES" >> "$AUDIT_DIR/frontend-quality-summary.txt"
        fi
        
        echo "✅ ESLint analysis completed"
    else
        echo "⚠️  ESLint not available"
    fi
    
    # Task 3.1.5: Format code with Prettier (dry run)
    echo "Task 3.1.5: Prettier formatting analysis"
    
    if npx prettier --version &> /dev/null; then
        echo "Checking Prettier formatting..."
        npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,scss,md}" > "$AUDIT_DIR/prettier-check.txt" 2>&1 || \
        echo "Prettier formatting issues found (see prettier-check.txt)"
        echo "✅ Prettier analysis completed"
    else
        echo "⚠️  Prettier not available"
    fi
    
    # Task 3.1.6: Code complexity analysis
    echo "Task 3.1.6: Code complexity analysis"
    
    # Manual complexity analysis
    echo "Analyzing code complexity..." 
    find src -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | head -20 | xargs wc -l > "$AUDIT_DIR/file-size-analysis.txt" 2>/dev/null || true
    
    echo "✅ Frontend code quality analysis completed"
    
else
    echo "⚠️  Frontend directory not found"
fi

echo ""
echo "=== 3.2 Backend Code Quality ==="

cd "$PROJECT_ROOT"

# Task 3.2.1: Install Python code quality tools
echo "Task 3.2.1: Python code quality tools setup"

PYTHON_QUALITY_TOOLS="black isort flake8 radon vulture"
for tool in $PYTHON_QUALITY_TOOLS; do
    if pip show "$tool" &> /dev/null; then
        echo "✅ $tool already installed"
    else
        echo "Installing $tool..."
        pip install --user "$tool" || echo "⚠️  Failed to install $tool"
    fi
done

# Task 3.2.2: Configure Pylint (if installed)
echo "Task 3.2.2: Pylint configuration"

if pip show pylint &> /dev/null; then
    echo "✅ Pylint is available"
    
    if [ ! -f ".pylintrc" ]; then
        echo "Creating Pylint configuration..."
        cat > .pylintrc << 'EOF'
[MASTER]
init-hook='import sys; sys.path.append(".")'

[MESSAGES CONTROL]
disable=C0330,C0326,R0903,R0913,W0613

[FORMAT]
max-line-length=88
good-names=i,j,k,ex,Run,_,db,app

[DESIGN]
max-args=7
max-locals=15
max-returns=6
max-branches=12
max-statements=50
EOF
        echo "✅ Pylint configuration created"
    else
        echo "✅ Pylint configuration exists"
    fi
else
    echo "⚠️  Pylint not installed"
fi

# Task 3.2.3: Update pyproject.toml for Black and isort
echo "Task 3.2.3: Black and isort configuration"

# The pyproject.toml already exists, verify it has the right settings
if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml exists"
    cp pyproject.toml "$AUDIT_DIR/pyproject-toml-backup.toml"
else
    echo "Creating pyproject.toml..."
    cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  migrations
  | venv
  | .venv
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
EOF
    echo "✅ pyproject.toml created"
fi

# Task 3.2.4: Run comprehensive Python analysis
echo "Task 3.2.4: Running Python code quality analysis"

if [ -d "backend/src" ]; then
    
    # Pylint analysis
    if command -v pylint &> /dev/null; then
        echo "Running Pylint analysis..."
        pylint backend/src/ --output-format=json > "$AUDIT_DIR/pylint-audit.json" 2>/dev/null || \
        pylint backend/src/ > "$AUDIT_DIR/pylint-audit.txt" 2>&1 || \
        echo "Pylint analysis completed with issues"
        echo "✅ Pylint analysis completed"
    fi
    
    # Flake8 analysis
    if command -v flake8 &> /dev/null; then
        echo "Running Flake8 analysis..."
        flake8 backend/src/ --format=json > "$AUDIT_DIR/flake8-audit.json" 2>/dev/null || \
        flake8 backend/src/ > "$AUDIT_DIR/flake8-audit.txt" 2>&1 || \
        echo "Flake8 analysis completed with issues"
        echo "✅ Flake8 analysis completed"
    fi
    
    # Black formatting check
    if command -v black &> /dev/null; then
        echo "Running Black formatting check..."
        black --check --diff backend/src/ > "$AUDIT_DIR/black-audit.txt" 2>&1 || \
        echo "Black formatting issues found"
        echo "✅ Black analysis completed"
    fi
    
    # isort check
    if command -v isort &> /dev/null; then
        echo "Running isort check..."
        isort --check-only --diff backend/src/ > "$AUDIT_DIR/isort-audit.txt" 2>&1 || \
        echo "isort issues found"
        echo "✅ isort analysis completed"
    fi
    
else
    echo "⚠️  Backend source directory not found"
fi

# Task 3.2.5: Security analysis (using bandit)
echo "Task 3.2.5: Security code analysis"

if [ -d "backend/src" ] && command -v bandit &> /dev/null; then
    echo "Running Bandit security analysis..."
    bandit -r backend/src/ -f json -o "$AUDIT_DIR/bandit-code-audit.json" 2>/dev/null || \
    bandit -r backend/src/ > "$AUDIT_DIR/bandit-code-audit.txt" 2>&1 || \
    echo "Bandit analysis completed"
    echo "✅ Security analysis completed"
else
    echo "⚠️  Bandit security analysis skipped"
fi

# Task 3.2.6: Code complexity metrics
echo "Task 3.2.6: Code complexity metrics"

if [ -d "backend/src" ] && command -v radon &> /dev/null; then
    echo "Running Radon complexity analysis..."
    radon cc backend/src/ --json > "$AUDIT_DIR/radon-complexity.json" 2>/dev/null || \
    radon cc backend/src/ > "$AUDIT_DIR/radon-complexity.txt" 2>&1 || \
    echo "Radon complexity analysis completed"
    
    radon mi backend/src/ --json > "$AUDIT_DIR/radon-maintainability.json" 2>/dev/null || \
    radon mi backend/src/ > "$AUDIT_DIR/radon-maintainability.txt" 2>&1 || \
    echo "Radon maintainability analysis completed"
    
    echo "✅ Complexity analysis completed"
else
    echo "⚠️  Radon complexity analysis skipped"
fi

# Generate summary
echo ""
echo "=== Code Quality Analysis Summary ==="

# Create comprehensive summary
cat > "$AUDIT_DIR/code-quality-summary.txt" << EOF
Code Quality Analysis Summary
============================
Generated: $(date)

Frontend Analysis:
EOF

if [ -d "$PROJECT_ROOT/frontend" ]; then
    echo "  ✅ Frontend directory analyzed" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/eslint-audit.json" ] && echo "  📋 ESLint analysis: eslint-audit.json" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/prettier-check.txt" ] && echo "  🎨 Prettier analysis: prettier-check.txt" >> "$AUDIT_DIR/code-quality-summary.txt"
else
    echo "  ⚠️  Frontend directory not found" >> "$AUDIT_DIR/code-quality-summary.txt"
fi

echo "" >> "$AUDIT_DIR/code-quality-summary.txt"
echo "Backend Analysis:" >> "$AUDIT_DIR/code-quality-summary.txt"

if [ -d "backend/src" ]; then
    echo "  ✅ Backend source directory analyzed" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/pylint-audit.json" ] && echo "  📋 Pylint analysis: pylint-audit.json" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/flake8-audit.json" ] && echo "  📋 Flake8 analysis: flake8-audit.json" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/black-audit.txt" ] && echo "  🎨 Black formatting: black-audit.txt" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/isort-audit.txt" ] && echo "  📦 Import sorting: isort-audit.txt" >> "$AUDIT_DIR/code-quality-summary.txt"
    [ -f "$AUDIT_DIR/radon-complexity.json" ] && echo "  📊 Complexity analysis: radon-complexity.json" >> "$AUDIT_DIR/code-quality-summary.txt"
else
    echo "  ⚠️  Backend source directory not found" >> "$AUDIT_DIR/code-quality-summary.txt"
fi

echo ""
echo "📊 Code quality audit reports generated in: $AUDIT_DIR"
cat "$AUDIT_DIR/code-quality-summary.txt"

echo ""
echo "✅ Phase 3 Code Quality Analysis Complete"
echo "📋 Next: Run phase4-security-audit.sh for Security Vulnerability Scan"