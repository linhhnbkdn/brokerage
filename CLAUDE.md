# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a full-stack brokerage application with separate frontend and backend:

```
brokerage/
├── fe/           # React Router frontend application
└── be/           # Django backend API
```

## Frontend (fe/)

Built with React Router v7, using TypeScript and TailwindCSS.

### Development Commands

```bash
cd fe/
npm install          # Install dependencies  
npm run dev         # Start development server (http://localhost:5173)
npm run build       # Build for production
npm run typecheck   # Type checking with TypeScript
npm start           # Start production server
```

### Architecture

- **Framework**: React Router v7 with SSR enabled
- **Styling**: TailwindCSS v4 with Vite plugin
- **TypeScript**: Strict mode enabled with path aliases (`~/*` → `./app/*`)
- **Build Tool**: Vite with React Router plugin
- **Entry Point**: `app/root.tsx` - contains Layout component and ErrorBoundary
- **Routes**: File-based routing in `app/routes/`

### Key Configuration Files

- `react-router.config.ts` - React Router configuration (SSR enabled)
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript configuration with strict mode
- `package.json` - Dependencies and scripts

## Backend (be/)

Django 5.2.5 project with SQLite database, configured with modern Python tooling using UV and comprehensive development setup.

### Development Commands

#### Using Makefile (Recommended)
```bash
cd be/
make help                 # Show all available commands
make install             # Install dependencies with uv
make runserver           # Start Django development server (port 8000)
make migrate             # Apply database migrations
make makemigrations      # Create new migrations
make createsuperuser     # Create Django superuser
make test                # Run tests with coverage
make test-fast           # Run tests without coverage
make lint                # Run ruff linting
make format              # Format code with ruff
make check               # Run all code quality checks
make fix                 # Format and fix auto-fixable issues
```

#### Direct Django Management
```bash
cd be/
uv run python manage.py runserver      # Start development server
uv run python manage.py migrate        # Apply database migrations
uv run python manage.py makemigrations # Create new migrations
uv run python manage.py createsuperuser # Create admin user
```

### Architecture  

- **Framework**: Django 5.2.5 with Django REST Framework
- **Database**: SQLite (development), PostgreSQL support configured
- **Package Management**: UV (modern Python package manager)
- **Code Quality**: Ruff for linting and formatting, MyPy for type checking
- **Testing**: Pytest with Django integration, coverage reporting
- **Authentication**: JWT-based authentication flow designed (see design/jwt-authentication-flow.mmd)
- **Project Structure**: Clean architecture pattern for brokerage application
- **Admin Interface**: Available at `/admin/`

### Key Files

- `pyproject.toml` - Modern Python project configuration with comprehensive dev tools
- `Makefile` - Comprehensive development commands and workflows  
- `be/settings.py` - Django configuration
- `be/urls.py` - URL routing (currently only admin)
- `manage.py` - Django management commands
- `design/` - Contains system design documents and authentication flow diagrams

### Code Quality Tools

- **Ruff**: Configured with extensive rule set for linting and formatting (80 char line length)
- **MyPy**: Type checking with Django stubs
- **Pytest**: Test framework with coverage reporting (80% threshold)
- **Pre-commit**: Git hooks for code quality enforcement

## Development Workflow

1. **Frontend Development**: Work in `fe/` directory, use `npm run dev` for hot reload at http://localhost:5173
2. **Backend Development**: Work in `be/` directory, use `make runserver` or `uv run python manage.py runserver` (port 8000)
3. **Code Quality**: 
   - Frontend: Run `npm run typecheck` before commits
   - Backend: Run `make check` for linting and formatting, `make test` for testing
4. **Build**: Use `npm run build` to create production build of frontend
5. **Testing**: 
   - Backend: `make test` for full test suite, `make test-fast` for quick feedback

## Docker Support

Frontend includes Docker support:
- `fe/Dockerfile` - Production Docker image
- Build: `docker build -t my-app .`
- Run: `docker run -p 3000:3000 my-app`

Backend Docker support available via Makefile:
- Build: `make docker-build`
- Run: `make docker-run`

## Project Context

This is a **brokerage application** for stock market and cryptocurrency investment, as outlined in the programming challenge document (`design/Programming Challenge - Backend Developer.pdf`). The system includes:

- User authentication and account management
- Bank account linking for deposits/withdrawals  
- Trading functionality for stocks, bonds, cryptocurrencies
- Portfolio performance tracking
- Exchange integration for instrument data and trade execution

The JWT authentication flow is documented in `design/jwt-authentication-flow.mmd` with comprehensive security considerations including token refresh, logout, and error handling scenarios.