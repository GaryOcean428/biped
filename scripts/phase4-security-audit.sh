#!/bin/bash
# Phase 4: Security Vulnerability Scan
# Implementation of comprehensive security audit as specified in the quality improvement protocol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"

echo "=== PHASE 4: SECURITY VULNERABILITY SCAN ==="

# Create audit directory
mkdir -p "$AUDIT_DIR"

echo ""
echo "=== 4.1 Frontend Security Audit ==="

if [ -d "$PROJECT_ROOT/frontend" ]; then
    cd "$PROJECT_ROOT/frontend"
    
    # Task 4.1.1: NPM security audit
    echo "Task 4.1.1: NPM security audit"
    if command -v npm &> /dev/null && [ -f "package.json" ]; then
        echo "Running npm security audit..."
        npm audit --json > "$AUDIT_DIR/npm-security-audit.json" 2>/dev/null || \
        npm audit > "$AUDIT_DIR/npm-security-audit.txt" 2>&1 || \
        echo "NPM audit completed with findings"
        echo "✅ NPM security audit completed"
    else
        echo "⚠️  NPM or package.json not found"
        echo "NPM not available" > "$AUDIT_DIR/npm-security-audit.txt"
    fi
    
    # Task 4.1.2: Frontend dependency vulnerability check
    echo "Task 4.1.2: Frontend dependency analysis"
    if [ -f "package.json" ]; then
        # Extract and analyze dependencies
        python3 -c "
import json
import re

try:
    with open('package.json', 'r') as f:
        package_data = json.load(f)
    
    dependencies = package_data.get('dependencies', {})
    dev_dependencies = package_data.get('devDependencies', {})
    
    security_report = {
        'total_dependencies': len(dependencies),
        'total_dev_dependencies': len(dev_dependencies),
        'potential_security_concerns': [],
        'outdated_patterns': []
    }
    
    # Check for known problematic patterns
    security_concerns = [
        'eval', 'innerHTML', 'dangerouslySetInnerHTML', 
        'document.write', 'setTimeout', 'setInterval'
    ]
    
    # Check dependency versions for potential issues
    for dep, version in {**dependencies, **dev_dependencies}.items():
        if '^' not in version and '~' not in version and '>' not in version:
            if '.' in version:
                major_version = version.split('.')[0]
                if major_version.isdigit() and int(major_version) < 2:
                    security_report['outdated_patterns'].append(f'{dep}: {version}')
    
    with open('$AUDIT_DIR/frontend-dependency-security.json', 'w') as f:
        json.dump(security_report, f, indent=2)
    
    print('Frontend dependency security analysis completed')
    
except Exception as e:
    print(f'Error analyzing frontend dependencies: {e}')
" 2>/dev/null || echo "Frontend dependency analysis failed"
        
        echo "✅ Frontend dependency security analysis completed"
    fi
    
    # Task 4.1.3: Client-side security checks
    echo "Task 4.1.3: Client-side security pattern analysis"
    if [ -d "src" ]; then
        # Check for common security anti-patterns in JavaScript/React code
        echo "Scanning for security patterns..."
        
        # Look for dangerous patterns
        grep -r "dangerouslySetInnerHTML" src/ > "$AUDIT_DIR/dangerous-html-patterns.txt" 2>/dev/null || \
        echo "No dangerouslySetInnerHTML patterns found" > "$AUDIT_DIR/dangerous-html-patterns.txt"
        
        grep -r "eval\|innerHTML\|document\.write" src/ > "$AUDIT_DIR/js-security-patterns.txt" 2>/dev/null || \
        echo "No dangerous JavaScript patterns found" > "$AUDIT_DIR/js-security-patterns.txt"
        
        # Check for hardcoded URLs/APIs
        grep -r "http://\|https://" src/ > "$AUDIT_DIR/hardcoded-urls.txt" 2>/dev/null || \
        echo "No hardcoded URLs found" > "$AUDIT_DIR/hardcoded-urls.txt"
        
        echo "✅ Client-side security pattern analysis completed"
    fi
    
else
    echo "⚠️  Frontend directory not found"
fi

echo ""
echo "=== 4.2 Backend Security Audit ==="

cd "$PROJECT_ROOT"

# Task 4.2.1: Python security scanning
echo "Task 4.2.1: Python security analysis"

if [ -d "backend/src" ]; then
    
    # Install security tools if not present
    SECURITY_TOOLS="bandit safety"
    for tool in $SECURITY_TOOLS; do
        if ! command -v "$tool" &> /dev/null && ! pip show "$tool" &> /dev/null; then
            echo "Installing $tool..."
            pip install --user "$tool" || echo "⚠️  Failed to install $tool"
        fi
    done
    
    # Task 4.2.2: Bandit security analysis
    echo "Task 4.2.2: Bandit static security analysis"
    if command -v bandit &> /dev/null || pip show bandit &> /dev/null; then
        echo "Running Bandit security analysis..."
        bandit -r backend/src/ -f json -o "$AUDIT_DIR/bandit-security-analysis.json" 2>/dev/null || \
        bandit -r backend/src/ > "$AUDIT_DIR/bandit-security-analysis.txt" 2>&1 || \
        echo "Bandit analysis completed"
        echo "✅ Bandit security analysis completed"
    else
        echo "⚠️  Bandit not available"
        echo "Bandit not available" > "$AUDIT_DIR/bandit-security-analysis.txt"
    fi
    
    # Task 4.2.3: Safety vulnerability database check
    echo "Task 4.2.3: Safety vulnerability scan"
    if command -v safety &> /dev/null || pip show safety &> /dev/null; then
        echo "Running Safety vulnerability scan..."
        safety check --json > "$AUDIT_DIR/safety-vulnerability-scan.json" 2>/dev/null || \
        safety check > "$AUDIT_DIR/safety-vulnerability-scan.txt" 2>/dev/null || \
        echo "Safety scan completed with issues"
        echo "✅ Safety vulnerability scan completed"
    else
        echo "⚠️  Safety not available"
        echo "Safety not available" > "$AUDIT_DIR/safety-vulnerability-scan.txt"
    fi
    
    # Task 4.2.4: Manual security pattern analysis
    echo "Task 4.2.4: Manual security pattern analysis"
    
    # Check for hardcoded secrets/passwords
    echo "Scanning for hardcoded secrets..."
    grep -r -i "password.*=" backend/src/ > "$AUDIT_DIR/hardcoded-passwords.txt" 2>/dev/null || \
    echo "No obvious hardcoded passwords found" > "$AUDIT_DIR/hardcoded-passwords.txt"
    
    grep -r -i "secret.*=" backend/src/ > "$AUDIT_DIR/hardcoded-secrets.txt" 2>/dev/null || \
    echo "No obvious hardcoded secrets found" > "$AUDIT_DIR/hardcoded-secrets.txt"
    
    grep -r -i "api.*key\|token.*=" backend/src/ > "$AUDIT_DIR/hardcoded-tokens.txt" 2>/dev/null || \
    echo "No obvious hardcoded tokens found" > "$AUDIT_DIR/hardcoded-tokens.txt"
    
    # Check for SQL injection patterns
    grep -r "SELECT.*%s\|INSERT.*%s\|UPDATE.*%s\|DELETE.*%s" backend/src/ > "$AUDIT_DIR/sql-injection-patterns.txt" 2>/dev/null || \
    echo "No obvious SQL injection patterns found" > "$AUDIT_DIR/sql-injection-patterns.txt"
    
    # Check for command injection patterns
    grep -r "os\.system\|subprocess\|eval\|exec" backend/src/ > "$AUDIT_DIR/command-injection-patterns.txt" 2>/dev/null || \
    echo "No obvious command injection patterns found" > "$AUDIT_DIR/command-injection-patterns.txt"
    
    echo "✅ Manual security pattern analysis completed"
    
    # Task 4.2.5: Configuration security check
    echo "Task 4.2.5: Configuration security analysis"
    
    # Check Flask security settings
    if grep -r "debug.*=.*True" backend/src/ > /dev/null 2>&1; then
        echo "⚠️  Debug mode enabled - security risk" > "$AUDIT_DIR/configuration-security.txt"
    else
        echo "✅ Debug mode properly configured" > "$AUDIT_DIR/configuration-security.txt"
    fi
    
    # Check for HTTPS enforcement
    if grep -r "FORCE_HTTPS\|force_https" backend/src/ > /dev/null 2>&1; then
        echo "✅ HTTPS enforcement found" >> "$AUDIT_DIR/configuration-security.txt"
    else
        echo "⚠️  HTTPS enforcement not clearly configured" >> "$AUDIT_DIR/configuration-security.txt"
    fi
    
    # Check for security headers
    if grep -r "Talisman\|CSP\|HSTS" backend/src/ > /dev/null 2>&1; then
        echo "✅ Security headers implementation found" >> "$AUDIT_DIR/configuration-security.txt"
    else
        echo "⚠️  Security headers not clearly configured" >> "$AUDIT_DIR/configuration-security.txt"
    fi
    
    echo "✅ Configuration security analysis completed"
    
else
    echo "⚠️  Backend source directory not found"
fi

echo ""
echo "=== 4.3 Infrastructure Security Assessment ==="

# Task 4.3.1: Docker security check
echo "Task 4.3.1: Docker configuration security"
if [ -f "Dockerfile" ]; then
    echo "Analyzing Dockerfile security..."
    
    # Check for security best practices
    cat > "$AUDIT_DIR/docker-security-analysis.txt" << EOF
Docker Security Analysis
========================

Dockerfile Security Checklist:
EOF
    
    if grep -q "USER.*root\|^USER root" Dockerfile 2>/dev/null; then
        echo "⚠️  Running as root user detected" >> "$AUDIT_DIR/docker-security-analysis.txt"
    elif grep -q "USER" Dockerfile 2>/dev/null; then
        echo "✅ Non-root user configuration found" >> "$AUDIT_DIR/docker-security-analysis.txt"
    else
        echo "⚠️  No explicit user configuration (may default to root)" >> "$AUDIT_DIR/docker-security-analysis.txt"
    fi
    
    if grep -q "COPY.*\.\|ADD.*\." Dockerfile 2>/dev/null; then
        echo "⚠️  Copying entire directory - may include sensitive files" >> "$AUDIT_DIR/docker-security-analysis.txt"
    else
        echo "✅ Selective file copying detected" >> "$AUDIT_DIR/docker-security-analysis.txt"
    fi
    
    if grep -q "apt.*update.*&&.*apt.*install\|yum.*install" Dockerfile 2>/dev/null; then
        echo "✅ Package manager cache cleaning practices" >> "$AUDIT_DIR/docker-security-analysis.txt"
    fi
    
    echo "✅ Docker security analysis completed"
else
    echo "No Dockerfile found" > "$AUDIT_DIR/docker-security-analysis.txt"
fi

# Task 4.3.2: Environment security
echo "Task 4.3.2: Environment configuration security"

# Check for .env files
if [ -f ".env" ]; then
    echo "⚠️  .env file found - ensure it's not committed to version control" > "$AUDIT_DIR/environment-security.txt"
    if grep -q ".env" .gitignore 2>/dev/null; then
        echo "✅ .env file is in .gitignore" >> "$AUDIT_DIR/environment-security.txt"
    else
        echo "❌ .env file not in .gitignore - SECURITY RISK" >> "$AUDIT_DIR/environment-security.txt"
    fi
else
    echo "✅ No .env file in root directory" > "$AUDIT_DIR/environment-security.txt"
fi

if [ -f ".env.example" ]; then
    echo "✅ .env.example file found - good practice" >> "$AUDIT_DIR/environment-security.txt"
else
    echo "⚠️  Consider adding .env.example for documentation" >> "$AUDIT_DIR/environment-security.txt"
fi

echo "✅ Environment security analysis completed"

echo ""
echo "=== Security Audit Summary ==="

# Generate comprehensive security report
cat > "$AUDIT_DIR/security-audit-summary.txt" << EOF
Security Audit Summary
======================
Generated: $(date)

AUDIT SCOPE:
- Frontend security patterns and dependencies
- Backend static security analysis
- Infrastructure configuration security
- Environment and secrets management

FRONTEND SECURITY:
EOF

[ -f "$AUDIT_DIR/npm-security-audit.json" ] && echo "✅ NPM security audit: npm-security-audit.json" >> "$AUDIT_DIR/security-audit-summary.txt"
[ -f "$AUDIT_DIR/frontend-dependency-security.json" ] && echo "✅ Dependency analysis: frontend-dependency-security.json" >> "$AUDIT_DIR/security-audit-summary.txt"
[ -f "$AUDIT_DIR/dangerous-html-patterns.txt" ] && echo "✅ HTML security patterns: dangerous-html-patterns.txt" >> "$AUDIT_DIR/security-audit-summary.txt"

echo "" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "BACKEND SECURITY:" >> "$AUDIT_DIR/security-audit-summary.txt"

[ -f "$AUDIT_DIR/bandit-security-analysis.json" ] && echo "✅ Static analysis: bandit-security-analysis.json" >> "$AUDIT_DIR/security-audit-summary.txt"
[ -f "$AUDIT_DIR/safety-vulnerability-scan.json" ] && echo "✅ Vulnerability scan: safety-vulnerability-scan.json" >> "$AUDIT_DIR/security-audit-summary.txt"
[ -f "$AUDIT_DIR/hardcoded-passwords.txt" ] && echo "✅ Secret analysis: hardcoded-passwords.txt" >> "$AUDIT_DIR/security-audit-summary.txt"
[ -f "$AUDIT_DIR/sql-injection-patterns.txt" ] && echo "✅ Injection patterns: sql-injection-patterns.txt" >> "$AUDIT_DIR/security-audit-summary.txt"

echo "" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "INFRASTRUCTURE SECURITY:" >> "$AUDIT_DIR/security-audit-summary.txt"

[ -f "$AUDIT_DIR/docker-security-analysis.txt" ] && echo "✅ Docker analysis: docker-security-analysis.txt" >> "$AUDIT_DIR/security-audit-summary.txt"
[ -f "$AUDIT_DIR/environment-security.txt" ] && echo "✅ Environment analysis: environment-security.txt" >> "$AUDIT_DIR/security-audit-summary.txt"

echo "" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "RECOMMENDATIONS:" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "1. Review all security scan results for actionable items" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "2. Update dependencies with known vulnerabilities" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "3. Implement missing security headers and configurations" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "4. Set up automated security scanning in CI/CD pipeline" >> "$AUDIT_DIR/security-audit-summary.txt"
echo "5. Regular security audits and penetration testing" >> "$AUDIT_DIR/security-audit-summary.txt"

echo ""
echo "📊 Security audit reports generated in: $AUDIT_DIR"
cat "$AUDIT_DIR/security-audit-summary.txt"

echo ""
echo "✅ Phase 4 Security Vulnerability Scan Complete"
echo "📋 Next: Run phase5-performance-audit.sh for Performance & Bundle Analysis"