#!/bin/bash
# Comprehensive quality check script

set -e

echo "🔍 Running comprehensive code quality checks..."

# Create reports directory
mkdir -p reports

echo "1️⃣ Running Black (code formatting)..."
uv run black --check --diff backend/ tests/ || {
    echo "❌ Black formatting issues found. Run 'uv run black backend/ tests/' to fix."
    exit 1
}

echo "2️⃣ Running isort (import sorting)..."
uv run isort --check-only --diff backend/ tests/ || {
    echo "❌ Import sorting issues found. Run 'uv run isort backend/ tests/' to fix."
    exit 1
}

echo "3️⃣ Running flake8 (linting)..."
uv run flake8 backend/ tests/ --max-line-length=88 --extend-ignore=E203,W503 --statistics --output-file=reports/flake8-report.txt || {
    echo "❌ Linting issues found. Check reports/flake8-report.txt"
    exit 1
}

echo "4️⃣ Running mypy (type checking)..."
uv run mypy backend/ --html-report reports/mypy-report || {
    echo "❌ Type checking issues found. Check reports/mypy-report/"
    exit 1
}

echo "5️⃣ Running pytest with coverage..."
uv run pytest tests/ \
    --cov=backend \
    --cov-report=html:reports/coverage-html \
    --cov-report=term-missing \
    --cov-report=xml:reports/coverage.xml \
    --html=reports/pytest-report.html \
    --self-contained-html \
    --junitxml=reports/junit.xml \
    -v || {
    echo "❌ Tests failed. Check reports/pytest-report.html"
    exit 1
}

echo "6️⃣ Running security checks..."
if command -v uv run bandit >/dev/null 2>&1; then
    uv run bandit -r backend/ -f json -o reports/security-report.json || {
        echo "⚠️  Security issues found. Check reports/security-report.json"
    }
else
    echo "⚠️  Bandit not installed. Skipping security check."
fi

echo "✅ All quality checks passed!"
echo "📊 Reports generated in ./reports/ directory"
echo "   - Code coverage: reports/coverage-html/index.html"
echo "   - Test results: reports/pytest-report.html"
echo "   - Type checking: reports/mypy-report/index.html"
echo "   - Linting: reports/flake8-report.txt"