# Makefile for Django Backend Development
# Uses uv for package management and ruff for linting/formatting
# Following clean architecture and modern Python best practices

# Variables
PYTHON_VERSION := 3.11
PROJECT_NAME := brokerage-be
DJANGO_SETTINGS_MODULE := be.settings
MANAGE := uv run python manage.py

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

##@ Development Environment

.PHONY: install
install: ## Install all dependencies using uv
	@echo "$(GREEN)Installing dependencies with uv...$(NC)"
	uv sync --dev
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

.PHONY: install-prod
install-prod: ## Install production dependencies only
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	uv sync --no-dev
	@echo "$(GREEN)Production dependencies installed!$(NC)"

.PHONY: update
update: ## Update all dependencies
	@echo "$(YELLOW)Updating dependencies...$(NC)"
	uv sync --upgrade
	@echo "$(GREEN)Dependencies updated!$(NC)"

.PHONY: venv
venv: ## Create and activate virtual environment
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	uv venv --python $(PYTHON_VERSION)
	@echo "$(GREEN)Virtual environment created!$(NC)"
	@echo "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

##@ Django Management

.PHONY: runserver
runserver: ## Start Django development server
	@echo "$(GREEN)Starting Django development server...$(NC)"
	$(MANAGE) runserver 8000

.PHONY: shell
shell: ## Open Django shell
	@echo "$(GREEN)Opening Django shell...$(NC)"
	$(MANAGE) shell

.PHONY: dbshell
dbshell: ## Open database shell
	@echo "$(GREEN)Opening database shell...$(NC)"
	$(MANAGE) dbshell

.PHONY: createsuperuser
createsuperuser: ## Create Django superuser
	@echo "$(GREEN)Creating superuser...$(NC)"
	$(MANAGE) createsuperuser

##@ Database Management

.PHONY: makemigrations
makemigrations: ## Create new database migrations
	@echo "$(GREEN)Creating migrations...$(NC)"
	$(MANAGE) makemigrations
	@echo "$(GREEN)Migrations created!$(NC)"

.PHONY: migrate
migrate: ## Apply database migrations
	@echo "$(GREEN)Applying migrations...$(NC)"
	$(MANAGE) migrate
	@echo "$(GREEN)Migrations applied!$(NC)"

.PHONY: migrate-zero
migrate-zero: ## Rollback all migrations for an app (usage: make migrate-zero APP=appname)
	@echo "$(YELLOW)Rolling back migrations for $(APP)...$(NC)"
	$(MANAGE) migrate $(APP) zero

.PHONY: showmigrations
showmigrations: ## Show migration status
	@echo "$(GREEN)Showing migration status...$(NC)"
	$(MANAGE) showmigrations

.PHONY: sqlmigrate
sqlmigrate: ## Show SQL for migration (usage: make sqlmigrate APP=appname MIGRATION=0001)
	@echo "$(GREEN)Showing SQL for migration...$(NC)"
	$(MANAGE) sqlmigrate $(APP) $(MIGRATION)

.PHONY: flush
flush: ## Remove all data from database
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel or Enter to continue...$(NC)"
	@read
	$(MANAGE) flush

##@ Code Quality & Formatting

.PHONY: lint
lint: ## Run ruff linting
	@echo "$(GREEN)Running ruff linting...$(NC)"
	uv run ruff check .
	@echo "$(GREEN)Linting complete!$(NC)"

.PHONY: lint-fix
lint-fix: ## Run ruff linting with auto-fix
	@echo "$(GREEN)Running ruff linting with auto-fix...$(NC)"
	uv run ruff check --fix .
	@echo "$(GREEN)Linting with fixes complete!$(NC)"

.PHONY: format
format: ## Format code with ruff
	@echo "$(GREEN)Formatting code with ruff...$(NC)"
	uv run ruff format .
	@echo "$(GREEN)Code formatting complete!$(NC)"

.PHONY: format-check
format-check: ## Check if code is formatted
	@echo "$(GREEN)Checking code formatting...$(NC)"
	uv run ruff format --check .

.PHONY: check
check: format-check lint ## Run all code quality checks
	@echo "$(GREEN)All code quality checks passed!$(NC)"

.PHONY: fix
fix: format lint-fix ## Format and fix all auto-fixable issues
	@echo "$(GREEN)Code formatted and fixed!$(NC)"

.PHONY: mypy
mypy: ## Run mypy type checking
	@echo "$(GREEN)Running mypy type checking...$(NC)"
	uv run mypy .
	@echo "$(GREEN)Type checking complete!$(NC)"

##@ Testing

.PHONY: test
test: ## Run tests with pytest
	@echo "$(GREEN)Running tests...$(NC)"
	$(MANAGE) test --parallel --keepdb
	@echo "$(GREEN)Tests complete!$(NC)"

.PHONY: test-fast
test-fast: ## Run tests without coverage and migrations
	@echo "$(GREEN)Running fast tests...$(NC)"
	uv run pytest --no-cov --reuse-db --nomigrations -x
	@echo "$(GREEN)Fast tests complete!$(NC)"

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	uv run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Tests with coverage complete!$(NC)"
	@echo "$(YELLOW)Coverage report available at htmlcov/index.html$(NC)"

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(NC)"
	uv run pytest-watch

.PHONY: test-unit
test-unit: ## Run only unit tests
	@echo "$(GREEN)Running unit tests...$(NC)"
	uv run pytest -m "unit"

.PHONY: test-integration
test-integration: ## Run only integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	uv run pytest -m "integration"

##@ Django Utilities

.PHONY: collectstatic
collectstatic: ## Collect static files
	@echo "$(GREEN)Collecting static files...$(NC)"
	$(MANAGE) collectstatic --noinput

.PHONY: startapp
startapp: ## Create new Django app (usage: make startapp APP=appname)
	@echo "$(GREEN)Creating new app: $(APP)...$(NC)"
	$(MANAGE) startapp $(APP)
	@echo "$(GREEN)App $(APP) created!$(NC)"

##@ API Documentation

.PHONY: gen-openapi
gen-openapi: ## Generate OpenAPI schema file
	@echo "$(GREEN)Generating OpenAPI schema...$(NC)"
	$(MANAGE) spectacular --color --file schema.yml
	@echo "$(GREEN)OpenAPI schema generated: schema.yml$(NC)"

.PHONY: gen-openapi-json
gen-openapi-json: ## Generate OpenAPI schema in JSON format
	@echo "$(GREEN)Generating OpenAPI schema (JSON)...$(NC)"
	$(MANAGE) spectacular --color --file schema.json --format openapi-json
	@echo "$(GREEN)OpenAPI schema generated: schema.json$(NC)"

.PHONY: serve-docs
serve-docs: ## Start development server and open API docs
	@echo "$(GREEN)Starting server and opening API documentation...$(NC)"
	@echo "$(YELLOW)API Documentation will be available at:$(NC)"
	@echo "  - Swagger UI: http://localhost:8000/api/docs/"
	@echo "  - ReDoc: http://localhost:8000/api/redoc/"
	@echo "  - Schema: http://localhost:8000/api/schema/"
	$(MAKE) runserver

.PHONY: check-deploy
check-deploy: ## Check deployment readiness
	@echo "$(GREEN)Checking deployment readiness...$(NC)"
	$(MANAGE) check --deploy

.PHONY: loaddata
loaddata: ## Load fixture data (usage: make loaddata FIXTURE=filename)
	@echo "$(GREEN)Loading fixture: $(FIXTURE)...$(NC)"
	$(MANAGE) loaddata $(FIXTURE)

.PHONY: dumpdata
dumpdata: ## Dump data to fixture (usage: make dumpdata APP=appname MODEL=modelname)
	@echo "$(GREEN)Dumping data...$(NC)"
	$(MANAGE) dumpdata $(APP).$(MODEL) --indent 2 > fixtures/$(APP)_$(MODEL).json

##@ Development Workflow

.PHONY: dev-setup
dev-setup: venv install migrate createsuperuser ## Complete development setup
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Activate virtual environment: source .venv/bin/activate"
	@echo "  2. Start development server: make runserver"

.PHONY: reset-db
reset-db: flush migrate ## Reset database (remove all data and re-run migrations)
	@echo "$(GREEN)Database reset complete!$(NC)"

.PHONY: fresh-start
fresh-start: ## Fresh start - clean and reinstall everything
	@echo "$(RED)This will remove virtual environment and reinstall everything!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel or Enter to continue...$(NC)"
	@read
	rm -rf .venv
	$(MAKE) venv install migrate
	@echo "$(GREEN)Fresh start complete!$(NC)"

.PHONY: backup-db
backup-db: ## Backup database to file
	@echo "$(GREEN)Creating database backup...$(NC)"
	$(MANAGE) dumpdata --natural-foreign --natural-primary \
		--exclude contenttypes --exclude auth.permission \
		--indent 2 > backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "$(GREEN)Database backup created!$(NC)"

##@ Clean Up

.PHONY: clean
clean: ## Clean up temporary files
	@echo "$(GREEN)Cleaning up temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -name "*.orig" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)Cleanup complete!$(NC)"

.PHONY: clean-migrations
clean-migrations: ## Remove all migration files (dangerous!)
	@echo "$(RED)WARNING: This will remove all migration files!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel or Enter to continue...$(NC)"
	@read
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	@echo "$(RED)Migration files removed!$(NC)"

##@ Pre-commit & Git Hooks

.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	uv run pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"

.PHONY: pre-commit-run
pre-commit-run: ## Run pre-commit on all files
	@echo "$(GREEN)Running pre-commit on all files...$(NC)"
	uv run pre-commit run --all-files

##@ Production & Deployment

.PHONY: build
build: ## Build production package
	@echo "$(GREEN)Building production package...$(NC)"
	uv build
	@echo "$(GREEN)Build complete!$(NC)"

.PHONY: security-check
security-check: ## Run security checks
	@echo "$(GREEN)Running security checks...$(NC)"
	uv run ruff check --select S .
	$(MANAGE) check --deploy
	@echo "$(GREEN)Security checks complete!$(NC)"

##@ Docker (if using containers)

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(PROJECT_NAME) .

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -p 8000:8000 $(PROJECT_NAME)

##@ Help

.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1m$(PROJECT_NAME) Makefile\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: version
version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Python: $(PYTHON_VERSION)"
	@uv --version
	@$(MANAGE) --version

.PHONY: deps-info
deps-info: ## Show dependency information
	@echo "$(GREEN)Dependency Information:$(NC)"
	@uv tree

# Ensure commands fail fast
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Help with colored output
.PHONY: help-colored
help-colored: ## Display colored help (alias for help)
	$(MAKE) help