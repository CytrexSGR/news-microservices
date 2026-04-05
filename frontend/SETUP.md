# Frontend Setup Guide

**Last Updated:** 2025-10-21

## Prerequisites

### Required Software
- **Node.js:** 18+ (LTS recommended)
- **npm:** 9+ (comes with Node.js)
- **Docker:** 20.10+ (for Docker-based development)
- **Docker Compose:** 2.0+ (for orchestration)

### System Requirements
- **Memory:** Minimum 4GB RAM available
- **Disk Space:** 500MB for node_modules
- **OS:** Linux, macOS, or Windows with WSL2

## Installation

### Method 1: Docker (Recommended for Production-like Development)

**Advantages:**
- Matches production environment
- No local Node.js installation needed
- Easy port management
- Integrated with backend services

**Steps:**

```bash
# 1. Navigate to project root
cd /home/cytrex/news-microservices

# 2. Start frontend with Docker Compose
docker compose up -d frontend

# 3. Check logs
docker compose logs frontend -f

# 4. Access application
# http://localhost:3000
```

**Configuration:**

Environment variables are configured in `docker-compose.yml`:
```yaml
environment:
  VITE_AUTH_API_URL: "http://localhost:8100/api/v1"
  VITE_FEED_API_URL: "http://localhost:8101/api/v1"
  VITE_ANALYSIS_API_URL: "http://localhost:8102/api/v1"
  VITE_ANALYTICS_API_URL: "http://localhost:8107/api/v1"
```

**Volume Mounts:**

Hot-reload is enabled via volume mounts:
```yaml
volumes:
  - ./frontend:/app
  - /app/node_modules  # Prevent host node_modules override
```

Code changes in `frontend/src/` will automatically reload in the browser.

### Method 2: Standalone (Faster for Active Development)

**Advantages:**
- Faster hot-reload (Vite HMR)
- Direct access to dev tools
- Lower resource usage

**Steps:**

```bash
# 1. Navigate to frontend directory
cd /home/cytrex/news-microservices/frontend

# 2. Install dependencies
npm install

# 3. Create environment file
cp .env.local.example .env.local

# 4. Configure API URLs in .env.local
# Edit with your backend service addresses:
VITE_AUTH_API_URL="http://localhost:8100/api/v1"
VITE_FEED_API_URL="http://localhost:8101/api/v1"
VITE_ANALYSIS_API_URL="http://localhost:8102/api/v1"
VITE_ANALYTICS_API_URL="http://localhost:8107/api/v1"

# 5. Start development server
npm run dev

# 6. Access application
# http://localhost:5173
```

**Note:** Backend services must be running separately (Docker or standalone).

## Configuration

### Environment Variables

**CRITICAL:** Vite requires `VITE_` prefix for variables to be exposed to the client.

**Required Variables:**

| Variable | Example | Description |
|----------|---------|-------------|
| `VITE_AUTH_API_URL` | `http://localhost:8100/api/v1` | Auth service endpoint |
| `VITE_FEED_API_URL` | `http://localhost:8101/api/v1` | Feed service endpoint |
| `VITE_ANALYSIS_API_URL` | `http://localhost:8102/api/v1` | Analysis service endpoint |
| `VITE_ANALYTICS_API_URL` | `http://localhost:8107/api/v1` | Analytics service endpoint |

**Optional Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` (Docker) / `5173` (Standalone) | Development server port |
| `VITE_DEV_SERVER_HOST` | `0.0.0.0` | Dev server host (0.0.0.0 for Docker) |

### Backend Services

Ensure all backend services are running before starting frontend:

```bash
# Check service status
docker compose ps

# Expected output:
# - news-auth-service (port 8100)
# - news-feed-service (port 8101)
# - news-content-analysis-service (port 8102)
# - news-analytics-service (port 8107)
```

If services are not running:
```bash
docker compose up -d
```

## Development

### Daily Workflow

```bash
# Start all backend services
cd /home/cytrex/news-microservices
docker compose up -d

# Start frontend (choose one method)

# Method A: Docker
docker compose up -d frontend

# Method B: Standalone
cd frontend
npm run dev
```

### Hot Module Replacement (HMR)

Vite provides instant hot-reload:

- **Edit `.tsx` files** → Browser updates immediately
- **Edit `.css` files** → Styles update without reload
- **Edit `vite.config.ts`** → Requires dev server restart

### Code Changes

1. **Component Changes:**
   - Edit files in `src/components/`, `src/pages/`, or `src/features/`
   - Browser auto-reloads

2. **API Changes:**
   - Edit files in `src/api/` or `src/features/*/api/`
   - Browser auto-reloads

3. **Dependency Changes:**
   ```bash
   # Docker method
   docker exec news-frontend npm install <package>
   docker compose restart frontend

   # Standalone method
   npm install <package>
   # Dev server auto-restarts
   ```

4. **Environment Variable Changes:**
   ```bash
   # Docker method
   # 1. Edit docker-compose.yml
   # 2. Stop and restart (restart alone won't reload env!)
   docker compose stop frontend
   docker compose up -d frontend

   # Standalone method
   # 1. Edit .env.local
   # 2. Restart dev server (Ctrl+C, then npm run dev)
   ```

### Development Tools

**React Query Devtools:**
- Automatically enabled in development
- Access via floating icon in bottom-left corner
- Inspect queries, mutations, cache state

**Browser DevTools:**
- Chrome/Firefox DevTools work normally
- React DevTools extension recommended
- Redux DevTools not needed (using Zustand)

## Building for Production

### Build Process

```bash
# Navigate to frontend directory
cd /home/cytrex/news-microservices/frontend

# Install dependencies (if not already done)
npm install

# Build for production
npm run build

# Output: frontend/dist/
```

**Build Output:**
- `dist/` directory contains optimized static files
- HTML, CSS, JavaScript are minified
- Assets are hashed for cache busting
- Source maps are excluded in production

### Preview Production Build

```bash
# Build first
npm run build

# Preview locally
npm run preview

# Access: http://localhost:4173
```

### Deployment

**Docker Production:**

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d frontend

# Frontend served via nginx from dist/
```

**Static Hosting:**

Upload `dist/` directory to:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Any static file host

**Important:** Configure environment variables at build time or use runtime configuration.

## Troubleshooting

### Port Already in Use

**Error:** `EADDRINUSE: address already in use :::3000`

**Fix:**
```bash
# Find process using port
sudo lsof -ti:3000

# Kill process
sudo lsof -ti:3000 | xargs kill -9

# Or change port
PORT=3001 npm run dev
```

### Cannot Find Module Errors

**Error:** `Cannot find module '@/components/ui/Button'`

**Fix:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### API Connection Errors

**Error:** `Network Error` or `CORS Error`

**Checks:**
1. Backend services running?
   ```bash
   docker compose ps
   ```

2. Correct API URLs in `.env.local` or `docker-compose.yml`?
   ```bash
   # Should match actual backend service addresses
   VITE_FEED_API_URL="http://localhost:8101/api/v1"
   ```

3. Check backend logs:
   ```bash
   docker compose logs feed-service --tail 50
   ```

### Docker Volume Issues

**Error:** Code changes not reflected in browser

**Fix:**
```bash
# Restart with rebuild
docker compose up -d --build frontend

# Or force recreate
docker compose stop frontend
docker compose rm -f frontend
docker compose up -d frontend
```

### Build Failures

**Error:** `Build failed with errors`

**Fix:**
```bash
# Check TypeScript errors
npm run type-check

# Fix type errors before building
# Then retry
npm run build
```

### Missing Dependencies

**Error:** `Module not found: Can't resolve 'some-package'`

**Fix:**
```bash
# Install missing package
npm install some-package

# Commit package.json and package-lock.json!
git add package.json package-lock.json
git commit -m "chore: add missing dependency some-package"
```

## Common Tasks

### Adding New Dependencies

```bash
# Docker method
docker exec news-frontend npm install package-name
docker compose restart frontend

# Standalone method
npm install package-name

# CRITICAL: Always commit changes!
git add package.json package-lock.json
git commit -m "chore: add dependency package-name"
```

### Adding shadcn/ui Components

```bash
# Example: Add Dialog component
npx shadcn-ui@latest add dialog

# Component added to src/components/ui/
# Can now import: import { Dialog } from '@/components/ui/Dialog'
```

### Type Checking

```bash
# Check TypeScript types without building
npm run type-check

# Watch mode
npm run type-check -- --watch
```

### Linting

```bash
# Run ESLint
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix
```

## Project Structure Quick Reference

```
frontend/
├── src/
│   ├── api/                 # Axios instances (authApi, feedApi, analysisApi, analyticsApi)
│   ├── components/          # Shared components
│   │   ├── layout/         # MainLayout
│   │   └── ui/             # shadcn/ui components
│   ├── features/            # Feature modules
│   │   ├── dashboards/     # Dashboard feature
│   │   ├── feeds/          # Feed management feature
│   │   ├── overview/       # Overview feature
│   │   └── reports/        # Reports feature
│   ├── pages/              # Route pages
│   ├── store/              # Zustand stores (authStore)
│   ├── lib/                # Utilities
│   ├── App.tsx             # Root component + routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                  # Static assets
├── package.json            # Dependencies
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind configuration
└── tsconfig.json           # TypeScript configuration
```

## Authentication

### Test User Credentials

**IMPORTANT:** Use the documented system user only!

- **Username:** `andreas`
- **Password:** `Aug2012#`
- **Email:** `andreas@test.com`

**Do NOT create new test users during development!**

### Login Flow

1. Navigate to `http://localhost:3000/login` (or `:5173` for standalone)
2. Enter credentials (andreas / Aug2012#)
3. Click "Login"
4. JWT token stored in Zustand authStore
5. Auto-redirect to home page
6. All subsequent API requests include `Authorization: Bearer <token>` header

### Logout

Click "Logout" button in sidebar → Tokens cleared → Redirect to `/login`

## Performance Tips

### Development

- Use standalone mode for faster HMR during active development
- Use Docker mode when testing integration with backend services
- React Query DevTools can slow down with many queries - disable if needed

### Production

- Always run `npm run build` before deployment
- Test production build locally with `npm run preview`
- Ensure environment variables are correctly set at build time

## Further Reading

- **FEATURES.md** - Complete feature inventory
- **ARCHITECTURE.md** - Technical architecture details
- **Vite Documentation:** https://vitejs.dev/
- **React Documentation:** https://react.dev/
- **Tailwind CSS:** https://tailwindcss.com/
- **shadcn/ui:** https://ui.shadcn.com/

## Support

If stuck for 15+ minutes:
1. Check logs: `docker compose logs frontend --tail 50`
2. Review this guide's troubleshooting section
3. Check ARCHITECTURE.md for technical details
4. Consult POSTMORTEMS.md for known issues
