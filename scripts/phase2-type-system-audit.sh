#!/bin/bash
# Phase 2: Type System Validation
# Implementation of comprehensive type system audit as specified in the quality improvement protocol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== PHASE 2: TYPE SYSTEM VALIDATION ==="

# Create audit directory
mkdir -p "$AUDIT_DIR"

echo ""
echo "=== 2.1 TypeScript Configuration Audit ==="

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"
    
    # Task 2.1.1: TypeScript strict mode audit
    echo "Task 2.1.1: TypeScript configuration analysis"
    
    # Check if TypeScript is installed
    if npm list typescript &> /dev/null || npm list --global typescript &> /dev/null; then
        echo "✅ TypeScript found"
        if command -v tsc &> /dev/null || npx tsc --version &> /dev/null; then
            if command -v tsc &> /dev/null; then
                tsc --version > "$AUDIT_DIR/typescript-version.txt"
            else
                npx tsc --version > "$AUDIT_DIR/typescript-version.txt"
            fi
        fi
    else
        echo "⚠️  TypeScript not found. Installing..."
        npm install --save-dev typescript @types/node @types/react @types/react-dom || \
        echo "❌ Failed to install TypeScript"
    fi
    
    # Task 2.1.2: Generate comprehensive tsconfig.json if missing or basic
    echo "Task 2.1.2: TypeScript configuration validation"
    
    if [ ! -f "tsconfig.json" ]; then
        echo "Creating comprehensive tsconfig.json..."
        cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noPropertyAccessFromIndexSignature": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": [
    "src/**/*",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": [
    "node_modules",
    "build",
    "dist"
  ]
}
EOF
        echo "✅ Comprehensive tsconfig.json created"
    else
        echo "✅ tsconfig.json exists"
        cp tsconfig.json "$AUDIT_DIR/tsconfig-current.json"
    fi
    
    # Task 2.1.3: Run comprehensive type checking
    echo "Task 2.1.3: TypeScript type checking"
    
    # Count .ts and .tsx files
    TS_FILES=$(find src -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l || echo "0")
    JS_FILES=$(find src -name "*.js" -o -name "*.jsx" 2>/dev/null | wc -l || echo "0")
    
    echo "TypeScript files: $TS_FILES" > "$AUDIT_DIR/typescript-file-count.txt"
    echo "JavaScript files: $JS_FILES" >> "$AUDIT_DIR/typescript-file-count.txt"
    
    if [ "$TS_FILES" -gt 0 ]; then
        echo "Running TypeScript compilation check..."
        if command -v tsc &> /dev/null; then
            tsc --noEmit --strict > "$AUDIT_DIR/typescript-audit.log" 2>&1 || \
            echo "TypeScript errors found (see typescript-audit.log)"
        elif npx tsc --version &> /dev/null; then
            npx tsc --noEmit --strict > "$AUDIT_DIR/typescript-audit.log" 2>&1 || \
            echo "TypeScript errors found (see typescript-audit.log)"
        fi
        echo "✅ TypeScript audit completed"
    else
        echo "⚠️  No TypeScript files found - project uses JavaScript"
        echo "No TypeScript files found" > "$AUDIT_DIR/typescript-audit.log"
    fi
    
    # Task 2.1.4: Type coverage analysis
    echo "Task 2.1.4: Type coverage analysis"
    
    # Calculate type coverage manually
    if [ "$TS_FILES" -gt 0 ]; then
        TOTAL_FILES=$((TS_FILES + JS_FILES))
        if [ "$TOTAL_FILES" -gt 0 ]; then
            TYPE_COVERAGE=$((TS_FILES * 100 / TOTAL_FILES))
            echo "Type Coverage Analysis:" > "$AUDIT_DIR/type-coverage-report.txt"
            echo "TypeScript files: $TS_FILES" >> "$AUDIT_DIR/type-coverage-report.txt"
            echo "JavaScript files: $JS_FILES" >> "$AUDIT_DIR/type-coverage-report.txt"
            echo "Total files: $TOTAL_FILES" >> "$AUDIT_DIR/type-coverage-report.txt"
            echo "Type coverage: ${TYPE_COVERAGE}%" >> "$AUDIT_DIR/type-coverage-report.txt"
            echo "✅ Type coverage: ${TYPE_COVERAGE}%"
        fi
    else
        echo "Type coverage: 0% (No TypeScript files)" > "$AUDIT_DIR/type-coverage-report.txt"
        echo "⚠️  Type coverage: 0%"
    fi
    
else
    echo "⚠️  Frontend directory not found"
fi

echo ""
echo "=== 2.2 Python Type Checking ==="

cd "$PROJECT_ROOT"

# Task 2.2.1: Install Python type checkers
echo "Task 2.2.1: Python type checking tools"

# Check for existing type checkers
PYTHON_TYPE_TOOLS="mypy"
for tool in $PYTHON_TYPE_TOOLS; do
    if pip show "$tool" &> /dev/null; then
        echo "✅ $tool is installed"
    else
        echo "Installing $tool..."
        pip install --user "$tool" || echo "⚠️  Failed to install $tool"
    fi
done

# Task 2.2.2: Configure mypy
echo "Task 2.2.2: MyPy configuration"

if [ ! -f "mypy.ini" ] && [ ! -f ".mypy.ini" ] && [ ! -f "pyproject.toml" ]; then
    echo "Creating mypy.ini configuration..."
    cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
show_error_codes = True

[mypy-flask.*]
ignore_missing_imports = True

[mypy-sqlalchemy.*]
ignore_missing_imports = True

[mypy-pytest.*]
ignore_missing_imports = True
EOF
    echo "✅ mypy.ini created"
else
    echo "✅ MyPy configuration exists"
fi

# Task 2.2.3: Run mypy analysis
echo "Task 2.2.3: MyPy type analysis"

if [ -d "backend/src" ]; then
    if command -v mypy &> /dev/null || pip show mypy &> /dev/null; then
        echo "Running MyPy analysis..."
        mypy backend/src/ > "$AUDIT_DIR/mypy-audit.log" 2>&1 || \
        echo "MyPy analysis completed with issues (see mypy-audit.log)"
        echo "✅ MyPy analysis completed"
    else
        echo "⚠️  MyPy not available"
        echo "MyPy not available" > "$AUDIT_DIR/mypy-audit.log"
    fi
else
    echo "⚠️  Backend source directory not found"
fi

# Task 2.2.4: Generate type annotation coverage
echo "Task 2.2.4: Type annotation coverage analysis"

if [ -d "backend/src" ]; then
    python3 -c "
import ast
import os
import sys

def count_type_annotations(directory):
    total_functions = 0
    typed_functions = 0
    total_files = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                total_files += 1
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                total_functions += 1
                                if (node.returns or 
                                    any(arg.annotation for arg in node.args.args)):
                                    typed_functions += 1
                except Exception as e:
                    print(f'Warning: Could not parse {filepath}: {e}', file=sys.stderr)
    
    coverage = (typed_functions / total_functions * 100) if total_functions > 0 else 0
    
    report = f'''Python Type Annotation Coverage Report
===========================================

Files analyzed: {total_files}
Total functions: {total_functions}
Typed functions: {typed_functions}
Type annotation coverage: {coverage:.2f}%

Recommendation:
- Excellent: 90%+ coverage
- Good: 70-89% coverage  
- Needs improvement: <70% coverage
'''
    
    print(report)
    return coverage, total_functions, typed_functions, total_files

if __name__ == '__main__':
    coverage, total_funcs, typed_funcs, total_files = count_type_annotations('backend/src/')
" > "$AUDIT_DIR/python-type-annotation-coverage.txt" 2>/dev/null || \
echo "Could not analyze Python type annotations" > "$AUDIT_DIR/python-type-annotation-coverage.txt"

    echo "✅ Type annotation coverage analysis completed"
else
    echo "⚠️  Backend source directory not found"
fi

echo ""
echo "=== Type System Validation Summary ==="
echo "📊 Type system audit reports generated in: $AUDIT_DIR"
echo ""
echo "Frontend Type System:"
[ -f "$AUDIT_DIR/typescript-version.txt" ] && echo "  ✅ TypeScript version: $(cat $AUDIT_DIR/typescript-version.txt)"
[ -f "$AUDIT_DIR/type-coverage-report.txt" ] && echo "  📊 Type coverage: $(grep 'Type coverage:' $AUDIT_DIR/type-coverage-report.txt | cut -d':' -f2)"
[ -f "$AUDIT_DIR/typescript-audit.log" ] && echo "  📋 TypeScript audit: typescript-audit.log"

echo ""
echo "Backend Type System:"
[ -f "$AUDIT_DIR/mypy-audit.log" ] && echo "  ✅ MyPy analysis: mypy-audit.log"
[ -f "$AUDIT_DIR/python-type-annotation-coverage.txt" ] && echo "  📊 Type annotation coverage: python-type-annotation-coverage.txt"

echo ""
if [ -f "$AUDIT_DIR/python-type-annotation-coverage.txt" ]; then
    grep "Type annotation coverage:" "$AUDIT_DIR/python-type-annotation-coverage.txt" | head -1
fi

echo ""
echo "✅ Phase 2 Type System Validation Complete"
echo "📋 Next: Run phase3-code-quality-audit.sh for Code Quality Analysis"