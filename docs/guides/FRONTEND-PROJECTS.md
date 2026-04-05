# Frontend Projects - Critical Distinction

**Last Updated:** 2025-10-21
**Severity:** CRITICAL - Read this before ANY frontend work!

## ⚠️ WARNING: Two Separate Frontend Projects

This system has **TWO DISTINCT FRONTEND PROJECTS**. Confusing them will result in catastrophic data loss.

### Project 1: Production Frontend (Main Application)

**Location:** `/home/cytrex/news-microservices/frontend/`

**Purpose:** Production-ready news aggregation and analytics platform

**Technology Stack:**
- React 19.1.1
- TypeScript 5.9.3
- Vite 7.1.7
- React Router 7.9.4
- React Query 5.90.5
- Zustand 5.0.8
- Tailwind CSS 3.4.18
- shadcn/ui components

**Port:**
- **Docker:** 3000
- **Standalone:** 5173

**Status:** FULLY IMPLEMENTED AND FUNCTIONAL

**Features:**
- ✅ Complete authentication system
- ✅ Feed management (list, detail, edit)
- ✅ Article analysis display
- ✅ Feed source assessment with credibility tiers
- ✅ Real-time analytics settings configuration
- ✅ Health monitoring and metrics

**How to Start:**

```bash
# Method 1: Docker (Recommended)
cd /home/cytrex/news-microservices
docker compose up -d frontend
# Access: http://localhost:3000

# Method 2: Standalone
cd /home/cytrex/news-microservices/frontend
npm install
npm run dev
# Access: http://localhost:5173
```

**Git Status:**
- **CRITICAL:** Previously had nested `.git` repository (removed as of 2025-10-21)
- Now tracked by main repository at `/home/cytrex/news-microservices/.git`
- All changes committed to main repository

**Documentation:**
- `frontend/FEATURES.md` - Complete feature inventory
- `frontend/ARCHITECTURE.md` - Technical architecture
- `frontend/SETUP.md` - Setup and configuration guide

---

### Project 2: Analytics Frontend (Prototype)

**Location:** `/home/cytrex/analytics-frontend/`

**Purpose:** Experimental standalone analytics interface prototype

**Technology Stack:**
- React + Vite
- Minimal configuration
- Standalone development

**Port:**
- **5173** (standalone only, no Docker)

**Status:** PROTOTYPE / EXPERIMENTAL

**Features:**
- ⚠️ Basic analytics dashboard prototyping
- ⚠️ Limited functionality
- ⚠️ Not integrated with main system

**How to Start:**

```bash
cd /home/cytrex/analytics-frontend
PORT=5173 npm run dev
# Access: http://localhost:5173
```

**Git Status:**
- **Separate** git repository
- Located at `/home/cytrex/analytics-frontend/.git`
- **NEVER** copy this to production frontend!

**Use Case:**
- Quick prototyping of analytics features
- Testing new visualization libraries
- Experimental UI components

---

## 🚨 Critical Rules

### 1. NEVER Overwrite Production Frontend

**DO NOT:**
```bash
# ❌ CATASTROPHIC - This destroys production frontend!
cp -r /home/cytrex/analytics-frontend /home/cytrex/news-microservices/frontend

# ❌ CATASTROPHIC - Same result!
mv /home/cytrex/news-microservices/frontend /home/cytrex/news-microservices/frontend.old
mv /home/cytrex/analytics-frontend /home/cytrex/news-microservices/frontend
```

**Consequence:** Complete loss of production frontend, requiring weeks to rebuild.

**What happened on 2025-10-21:**
- Analytics prototype was accidentally copied over production frontend
- All features, components, and configuration were lost
- Recovery took 8+ hours of intensive work
- Incident documented in `POSTMORTEMS.md`

### 2. Always Verify Current Directory

**Before ANY frontend work:**

```bash
pwd
# Expected outputs:
# /home/cytrex/news-microservices/frontend        → Production ✅
# /home/cytrex/analytics-frontend                 → Prototype ⚠️
```

**Check which project you're in:**

```bash
# Production frontend has:
ls -la src/pages/
# Should show: DashboardListPage.tsx, FeedListPage.tsx, ArticleDetailPage.tsx, etc.

# Analytics frontend has:
ls -la src/
# Minimal structure, experimental code
```

### 3. Use Correct npm Commands

**Production Frontend:**
```bash
cd /home/cytrex/news-microservices/frontend
npm install <package>
# ALWAYS commit package.json changes!
git add package.json package-lock.json
git commit -m "chore: add dependency <package>"
```

**Analytics Frontend:**
```bash
cd /home/cytrex/analytics-frontend
npm install <package>
# Separate package.json, separate dependencies
```

### 4. Port Awareness

**Port 3000:** Production frontend (Docker)
**Port 5173:** Production frontend (standalone) OR Analytics prototype

**If you see port 5173, verify which project:**

```bash
# Check running processes
lsof -ti:5173

# Check current directory
pwd

# Check for production indicators
ls src/features/  # Production has: feeds/, overview/, admin/, market/
```

### 5. Docker Compose Caution

**ONLY production frontend is in docker-compose.yml:**

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend  # ← This is PRODUCTION frontend
    ports:
      - "3000:3000"
```

**Analytics frontend is NOT in Docker and should NEVER be added to docker-compose.yml.**

### 6. Git Repository Isolation

**Production Frontend:**
- No nested `.git` directory (removed 2025-10-21)
- Tracked by main repository
- All commits go to `/home/cytrex/news-microservices/.git`

**Analytics Frontend:**
- Separate `.git` directory
- Independent version control
- Located at `/home/cytrex/analytics-frontend/.git`

**Verify:**

```bash
# Production frontend should NOT have .git
ls -la /home/cytrex/news-microservices/frontend/.git
# Expected: No such file or directory ✅

# Analytics frontend SHOULD have .git
ls -la /home/cytrex/analytics-frontend/.git
# Expected: Directory listing ✅
```

---

## 📋 Pre-Work Checklist

**Before starting ANY frontend work, verify:**

- [ ] `pwd` shows correct directory
- [ ] `ls src/pages/` shows expected files
- [ ] Check `package.json` name field
  - Production: `"name": "news-frontend"` or similar
  - Analytics: `"name": "analytics-frontend"` or similar
- [ ] Backup created if making destructive changes
  ```bash
  cd /home/cytrex
  tar -czf backups/frontend-$(date +%Y%m%d-%H%M%S).tar.gz news-microservices/frontend/
  ```

---

## 🔄 Feature Integration Workflow

**If you prototype a feature in analytics-frontend and want to move it to production:**

### ❌ WRONG:

```bash
# NEVER copy entire directories!
cp -r analytics-frontend news-microservices/frontend
```

### ✅ CORRECT:

```bash
# 1. Copy specific component files
cp /home/cytrex/analytics-frontend/src/components/NewWidget.tsx \
   /home/cytrex/news-microservices/frontend/src/components/

# 2. Adapt imports for production structure
# Edit NewWidget.tsx:
#   - Fix import paths
#   - Integrate with production API layer
#   - Use production types

# 3. Add dependencies to production package.json
cd /home/cytrex/news-microservices/frontend
npm install <new-dependency>

# 4. Test in production environment
npm run dev

# 5. Commit changes
git add src/components/NewWidget.tsx package.json package-lock.json
git commit -m "feat: add NewWidget component from analytics prototype"
```

**Key Principle:** Copy individual components, never entire projects!

---

## 🛡️ Protection Mechanisms

### Automated Validation

**Pre-commit hook** (`.git/hooks/pre-commit`):
- Prevents commits if frontend/.git exists
- Validates package.json is tracked
- Ensures critical files are documented

**Validation script** (`scripts/validate-frontend.sh`):
```bash
# Run before major changes
./scripts/validate-frontend.sh

# Checks:
# - No nested .git in frontend/
# - package.json exists and is committed
# - FEATURES.md, ARCHITECTURE.md, SETUP.md exist
# - All shadcn/ui components documented
```

### Backup Strategy

**Automated backups** (`scripts/backup.sh`):
```bash
# Create backup before destructive operations
./scripts/backup.sh

# Creates: backups/news-ms-YYYYMMDD-HHMMSS.tar.gz
# Excludes: node_modules, venv, .git, dist, build
```

**Manual backup:**
```bash
cd /home/cytrex
tar -czf backups/frontend-manual-$(date +%Y%m%d-%H%M%S).tar.gz \
  --exclude=node_modules \
  --exclude=dist \
  --exclude=.vite \
  news-microservices/frontend/
```

### Recovery Tags

**Git tags for stable states:**
```bash
# List recovery points
git tag | grep frontend

# Expected tags:
# frontend-recovered-20251021
# v1.0-frontend-secured
```

**Restore from tag:**
```bash
# If disaster strikes
git checkout frontend-recovered-20251021 -- frontend/

# Or restore from backup
cd /home/cytrex
tar -xzf backups/frontend-20251021.tar.gz
```

---

## 📚 Documentation Requirements

**When modifying production frontend, update:**

1. **frontend/FEATURES.md** - Add new features, pages, components
2. **frontend/ARCHITECTURE.md** - Document architectural changes
3. **frontend/SETUP.md** - Update setup steps if dependencies change
4. **This file** - If integration workflow changes

**When prototyping in analytics-frontend:**
- Document in analytics-frontend/README.md
- Note: "This is a prototype, not production code"

---

## 🆘 Disaster Recovery

**If production frontend is accidentally overwritten:**

1. **STOP immediately** - Do not commit, do not continue working

2. **Check for backup:**
   ```bash
   ls -lh /home/cytrex/backups/ | grep frontend
   ```

3. **Restore from backup:**
   ```bash
   cd /home/cytrex/news-microservices
   rm -rf frontend/
   tar -xzf /home/cytrex/backups/frontend-YYYYMMDD-HHMMSS.tar.gz
   ```

4. **Or restore from Git tag:**
   ```bash
   git checkout frontend-recovered-20251021 -- frontend/
   ```

5. **Verify restoration:**
   ```bash
   cd frontend
   ls src/pages/  # Should show all production pages
   npm install
   npm run dev
   ```

6. **Document incident in POSTMORTEMS.md**

---

## 📖 Related Documentation

- `frontend/FEATURES.md` - What exists in production frontend
- `frontend/ARCHITECTURE.md` - How production frontend is structured
- `frontend/SETUP.md` - How to set up and run production frontend
- `POSTMORTEMS.md` - Lessons learned from incidents
- `CLAUDE.md` - Overall development guidelines

---

## ✅ Quick Reference

| Aspect | Production Frontend | Analytics Frontend |
|--------|-------------------|-------------------|
| **Location** | `/home/cytrex/news-microservices/frontend/` | `/home/cytrex/analytics-frontend/` |
| **Purpose** | Production application | Experimental prototype |
| **Status** | Fully functional | Experimental |
| **Port (Docker)** | 3000 | N/A (not Dockerized) |
| **Port (Standalone)** | 5173 | 5173 |
| **Git Repository** | Main repo (no nested .git) | Separate .git |
| **Documentation** | FEATURES.md, ARCHITECTURE.md, SETUP.md | README.md |
| **Features** | Complete system | Basic prototype |
| **Can be overwritten?** | ❌ NEVER! | ⚠️ Yes (it's a prototype) |

---

**Last Incident:** 2025-10-21 - Analytics frontend accidentally copied over production frontend, complete loss, 8+ hours recovery time.

**Prevention:** Documentation, backups, pre-commit hooks, validation scripts, awareness.

**Remember:** When in doubt, check `pwd` and verify with `ls src/pages/`. 5 seconds of verification prevents hours of recovery.
