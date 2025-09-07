# Course Materials Assistant - Comprehensive Build System
# Complete implementation with testing, quality, and deployment tools

.PHONY: help install install-dev install-playwright setup clean test test-unit test-integration test-e2e test-coverage test-watch quality format lint type-check security-check pre-commit run run-dev run-prod build docs deploy docker-build docker-run reports serve-reports

# Colors for output
BLUE = \033[34m
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
RESET = \033[0m

# Default target
help: ## Show this help message
	@echo "$(BLUE)Course Materials Assistant - Build System$(RESET)"
	@echo "$(GREEN)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(RESET)"
	uv sync --no-dev

install-dev: ## Install development dependencies  
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	uv sync
	uv run pre-commit install

install-playwright: ## Install Playwright browsers
	@echo "$(BLUE)Installing Playwright browsers...$(RESET)"
	uv run playwright install

setup: install-dev install-playwright ## Complete development setup
	@echo "$(GREEN)Development environment setup complete!$(RESET)"
	@echo "Run 'make run' to start the application"

# Cleaning targets
clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(RESET)"
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf reports/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf backend/__pycache__/
	rm -rf tests/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Testing targets
test: test-unit test-integration ## Run all tests
	@echo "$(GREEN)All tests completed!$(RESET)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	uv run pytest tests/ -m "unit" -v --tb=short

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(RESET)"
	uv run pytest tests/ -m "integration" -v --tb=short

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running end-to-end tests...$(RESET)"
	uv run pytest tests/ -m "e2e" -v --tb=short

test-api: ## Run API tests only
	@echo "$(BLUE)Running API tests...$(RESET)"
	uv run pytest tests/test_api_endpoints.py -v

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	mkdir -p reports
	uv run pytest tests/ \
		--cov=backend \
		--cov-report=html:reports/coverage-html \
		--cov-report=term-missing \
		--cov-report=xml:reports/coverage.xml \
		--html=reports/pytest-report.html \
		--self-contained-html \
		-v

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	uv run pytest-watch tests/ -- -v --tb=short

test-playwright: ## Run Playwright tests
	@echo "$(BLUE)Running Playwright tests...$(RESET)"
	uv run playwright test

test-visual: ## Run visual regression tests
	@echo "$(BLUE)Running visual regression tests...$(RESET)"
	uv run playwright test tests/visual-regression.spec.js

# Code quality targets
quality: format lint type-check security-check ## Run all quality checks
	@echo "$(GREEN)All quality checks completed!$(RESET)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(RESET)"
	uv run black backend/ tests/
	uv run isort backend/ tests/

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(RESET)"
	uv run black --check --diff backend/ tests/
	uv run isort --check-only --diff backend/ tests/

lint: ## Run linting with flake8
	@echo "$(BLUE)Running linting...$(RESET)"
	mkdir -p reports
	uv run flake8 backend/ tests/ --max-line-length=88 --extend-ignore=E203,W503 --statistics --output-file=reports/flake8-report.txt

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(RESET)"
	mkdir -p reports
	uv run mypy backend/ --html-report reports/mypy-report

security-check: ## Run security scanning
	@echo "$(BLUE)Running security checks...$(RESET)"
	mkdir -p reports
	if command -v uv run bandit >/dev/null 2>&1; then \
		uv run bandit -r backend/ -f json -o reports/security-report.json; \
	else \
		echo "$(YELLOW)Bandit not installed. Skipping security check.$(RESET)"; \
	fi

pre-commit: ## Run pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(RESET)"
	uv run pre-commit run --all-files

# Application targets
run: ## Run application in development mode
	@echo "$(BLUE)Starting development server...$(RESET)"
	@echo "$(GREEN)Application will be available at http://localhost:8000$(RESET)"
	cd backend && uv run uvicorn app:app --reload --port 8000

run-prod: ## Run application in production mode
	@echo "$(BLUE)Starting production server...$(RESET)"
	cd backend && uv run uvicorn app:app --host 0.0.0.0 --port 8000

run-background: ## Run application in background
	@echo "$(BLUE)Starting application in background...$(RESET)"
	cd backend && nohup uv run uvicorn app:app --reload --port 8000 > ../logs/app.log 2>&1 &
	@echo "$(GREEN)Application started in background. Check logs/app.log$(RESET)"

stop: ## Stop background application
	@echo "$(BLUE)Stopping background application...$(RESET)"
	pkill -f "uvicorn app:app" || echo "No running application found"

# Build and deployment targets
build: quality test ## Build and validate entire project
	@echo "$(GREEN)Build completed successfully!$(RESET)"

build-docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(RESET)"
	mkdir -p docs/build
	# Add documentation build commands here

# Docker targets
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(RESET)"
	docker build -t course-materials-assistant .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(RESET)"
	docker run -p 8000:8000 -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} course-materials-assistant

# Report targets
reports: test-coverage ## Generate all reports
	@echo "$(GREEN)All reports generated in ./reports/ directory$(RESET)"

serve-reports: ## Serve reports on local server
	@echo "$(BLUE)Serving reports at http://localhost:8080$(RESET)"
	cd reports && python -m http.server 8080

open-coverage: ## Open coverage report in browser
	@if [ -f reports/coverage-html/index.html ]; then \
		open reports/coverage-html/index.html; \
	else \
		echo "$(RED)Coverage report not found. Run 'make test-coverage' first.$(RESET)"; \
	fi

open-pytest: ## Open pytest report in browser  
	@if [ -f reports/pytest-report.html ]; then \
		open reports/pytest-report.html; \
	else \
		echo "$(RED)Pytest report not found. Run 'make test-coverage' first.$(RESET)"; \
	fi

# CI/CD targets
ci-test: ## Run tests for CI environment
	@echo "$(BLUE)Running CI tests...$(RESET)"
	uv run pytest tests/ \
		--cov=backend \
		--cov-report=xml:reports/coverage.xml \
		--junitxml=reports/junit.xml \
		--tb=short \
		-v

ci-quality: ## Run quality checks for CI
	@echo "$(BLUE)Running CI quality checks...$(RESET)"
	./scripts/quality-check.sh

ci: ci-quality ci-test ## Run complete CI pipeline
	@echo "$(GREEN)CI pipeline completed successfully!$(RESET)"

# Development shortcuts
dev: setup run ## Complete development setup and run

quick-test: ## Run quick tests (unit only)
	@echo "$(BLUE)Running quick tests...$(RESET)"
	uv run pytest tests/test_api_endpoints.py -v --tb=short

fix: format lint ## Fix common code issues
	@echo "$(GREEN)Code fixes applied!$(RESET)"

# Status and info targets
status: ## Show project status
	@echo "$(BLUE)Project Status:$(RESET)"
	@echo "Python version: $(shell python --version)"
	@echo "UV version: $(shell uv --version)"
	@echo "Dependencies: $(shell uv pip list | wc -l) packages installed"
	@if [ -d reports ]; then \
		echo "Reports available: $(shell ls reports/ | wc -l) files"; \
	fi

requirements: ## Show requirements and dependencies
	@echo "$(BLUE)Project Requirements:$(RESET)"
	@echo "• Python 3.11+"
	@echo "• UV package manager"
	@echo "• Anthropic API key in .env file"
	@echo "• For development: Playwright, pre-commit"

# Log targets
logs: ## Show application logs
	@if [ -f logs/app.log ]; then \
		tail -f logs/app.log; \
	else \
		echo "$(RED)No log file found. Start app with 'make run-background' first.$(RESET)"; \
	fi

# Backup and maintenance
backup: ## Create project backup
	@echo "$(BLUE)Creating project backup...$(RESET)"
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='.git' \
		--exclude='node_modules' \
		--exclude='.venv' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='reports' \
		.
	@echo "$(GREEN)Backup created successfully!$(RESET)"

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(RESET)"
	uv lock --upgrade
	uv sync

# Database targets (if needed)
db-reset: ## Reset database
	@echo "$(BLUE)Resetting database...$(RESET)"
	rm -rf backend/chroma_db/
	@echo "$(GREEN)Database reset complete. Restart app to rebuild.$(RESET)"

# Performance targets
benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(RESET)"
	uv run pytest tests/ -m "slow" --benchmark-only -v

profile: ## Profile application performance
	@echo "$(BLUE)Profiling application...$(RESET)"
	# Add profiling commands here

# Validation targets
validate: format-check lint type-check test-unit ## Validate code without modifications
	@echo "$(GREEN)Validation completed successfully!$(RESET)"

# Git hooks and workflow
hooks: ## Install and setup git hooks
	uv run pre-commit install --hook-type pre-commit
	uv run pre-commit install --hook-type pre-push
	@echo "$(GREEN)Git hooks installed successfully!$(RESET)"

# Health check
health: ## Check application health
	@echo "$(BLUE)Checking application health...$(RESET)"
	@curl -f http://localhost:8000/ > /dev/null 2>&1 && \
		echo "$(GREEN)Application is healthy!$(RESET)" || \
		echo "$(RED)Application is not responding$(RESET)"

# Clean install
fresh-install: clean setup ## Clean install from scratch
	@echo "$(GREEN)Fresh installation completed!$(RESET)"