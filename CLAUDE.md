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

Django 5.2.5 project with SQLite database.

### Development Commands

```bash
cd be/
python manage.py runserver      # Start development server
python manage.py migrate        # Apply database migrations
python manage.py makemigrations # Create new migrations
python manage.py createsuperuser # Create admin user
```

### Architecture  

- **Framework**: Django 5.2.5
- **Database**: SQLite (default Django setup)
- **Project Structure**: Standard Django project layout
- **Settings**: Development settings with DEBUG=True
- **Admin Interface**: Available at `/admin/`

### Key Files

- `be/settings.py` - Django configuration
- `be/urls.py` - URL routing (currently only admin)
- `manage.py` - Django management commands

## Development Workflow

1. **Frontend Development**: Work in `fe/` directory, use `npm run dev` for hot reload
2. **Backend Development**: Work in `be/` directory, use `python manage.py runserver`
3. **Type Checking**: Run `npm run typecheck` in frontend before commits
4. **Build**: Use `npm run build` to create production build of frontend

## Docker Support

Frontend includes Docker support:
- `fe/Dockerfile` - Production Docker image
- Build: `docker build -t my-app .`
- Run: `docker run -p 3000:3000 my-app`