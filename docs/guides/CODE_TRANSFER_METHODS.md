# Code Transfer Methods - Moving to a New Server

**How to get your code from current server to a new server**

---

## Option 1: Git Repository (Empfohlen ✅)

**Best for:** Production deployments, team collaboration, version control

### Setup GitHub/GitLab Repository

```bash
# On current server (/home/cytrex/news-microservices)
cd /home/cytrex/news-microservices

# Check current git status
git remote -v

# If no remote exists, add one
git remote add origin https://github.com/YOUR_USERNAME/news-microservices.git

# Or if you use SSH:
git remote add origin git@github.com:YOUR_USERNAME/news-microservices.git

# Push all branches
git push -u origin main
git push --all
git push --tags
```

### Clone on New Server

```bash
# On new server
cd /opt/news-microservices

# Clone via HTTPS (requires username/password or token)
git clone https://github.com/YOUR_USERNAME/news-microservices.git .

# Or via SSH (requires SSH key)
git clone git@github.com:YOUR_USERNAME/news-microservices.git .

# Checkout desired branch
git checkout main
```

**Vorteile:**
- ✅ Version Control
- ✅ Easy updates (git pull)
- ✅ Rollback möglich (git checkout)
- ✅ Team collaboration
- ✅ CI/CD Integration

**Nachteile:**
- ❌ Benötigt GitHub/GitLab Account
- ❌ Secrets müssen separat übertragen werden (.env files)

---

## Option 2: Direct Server Transfer (rsync)

**Best for:** Quick migrations, private networks, no git repo

### Using rsync (Recommended for direct transfer)

```bash
# On current server
cd /home/cytrex

# Dry-run first (test without copying)
rsync -avz --dry-run \
  --exclude 'venv/' \
  --exclude 'node_modules/' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  news-microservices/ \
  user@new-server-ip:/opt/news-microservices/

# If dry-run looks good, remove --dry-run
rsync -avz --progress \
  --exclude 'venv/' \
  --exclude 'node_modules/' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  news-microservices/ \
  user@new-server-ip:/opt/news-microservices/
```

**Flags erklärt:**
- `-a`: Archive mode (preserves permissions, timestamps)
- `-v`: Verbose (shows progress)
- `-z`: Compress during transfer
- `--progress`: Shows transfer progress
- `--exclude`: Excludes directories/files (saves time, space)

**Vorteile:**
- ✅ Schnell
- ✅ Direkte Übertragung
- ✅ Nur geänderte Dateien werden übertragen
- ✅ Permissions bleiben erhalten

**Nachteile:**
- ❌ Kein Version Control
- ❌ SSH-Zugang zu beiden Servern benötigt

---

## Option 3: Archive & Transfer (tar + scp)

**Best for:** No direct SSH between servers, air-gapped systems

### Create Archive

```bash
# On current server
cd /home/cytrex

# Create compressed archive (excludes unnecessary files)
tar -czf news-microservices-$(date +%Y%m%d).tar.gz \
  --exclude='news-microservices/venv' \
  --exclude='news-microservices/node_modules' \
  --exclude='news-microservices/__pycache__' \
  --exclude='news-microservices/.git' \
  --exclude='news-microservices/*.pyc' \
  --exclude='news-microservices/.env' \
  news-microservices/

# Check archive size
ls -lh news-microservices-*.tar.gz
```

### Transfer Archive

**Option A: Via SCP**
```bash
# From current server to new server
scp news-microservices-20251204.tar.gz user@new-server-ip:/tmp/
```

**Option B: Via USB/Download**
```bash
# Download from current server
# Then upload to new server manually
```

### Extract on New Server

```bash
# On new server
cd /opt

# Extract archive
tar -xzf /tmp/news-microservices-20251204.tar.gz

# Verify extraction
ls -la news-microservices/
```

**Vorteile:**
- ✅ Simple
- ✅ Works offline
- ✅ Single file to transfer

**Nachteile:**
- ❌ Full copy every time
- ❌ No version control
- ❌ Large file size

---

## Option 4: Docker Registry (Advanced)

**Best for:** Multiple servers, production rollouts, CI/CD

### Push Images to Registry

```bash
# On current server
cd /home/cytrex/news-microservices

# Tag images for registry
docker tag news-auth-service:latest your-registry.com/news-auth-service:v1.0
docker tag news-feed-service:latest your-registry.com/news-feed-service:v1.0
# ... repeat for all services

# Push to registry
docker push your-registry.com/news-auth-service:v1.0
docker push your-registry.com/news-feed-service:v1.0
```

### Pull on New Server

```bash
# On new server
# Transfer only docker-compose.prod.yml and .env files

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

**Vorteile:**
- ✅ Pre-built images (no build time)
- ✅ Consistent deployments
- ✅ Works with CI/CD
- ✅ Multiple servers easily

**Nachteile:**
- ❌ Requires Docker Registry (Docker Hub, Harbor, etc.)
- ❌ Image storage costs
- ❌ More complex setup

---

## Recommended Workflow by Scenario

### Scenario 1: First Production Deployment

```bash
# 1. Push code to Git (one-time setup)
git remote add origin git@github.com:YOUR_USERNAME/news-microservices.git
git push -u origin main

# 2. On new server
git clone git@github.com:YOUR_USERNAME/news-microservices.git /opt/news-microservices

# 3. Transfer secrets separately (manual or encrypted)
scp .env.production user@new-server:/opt/news-microservices/
scp -r certs/ user@new-server:/opt/news-microservices/

# 4. Deploy
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### Scenario 2: Testing/Migration (Same Infrastructure)

```bash
# Direct rsync transfer
rsync -avz --progress \
  --exclude 'venv/' --exclude 'node_modules/' --exclude '.git/' \
  /home/cytrex/news-microservices/ \
  user@new-server:/opt/news-microservices/

# Transfer secrets
scp .env.production user@new-server:/opt/news-microservices/
```

### Scenario 3: Air-Gapped/Offline Server

```bash
# 1. Create archive
tar -czf news-microservices.tar.gz news-microservices/

# 2. Transfer via USB/secure channel

# 3. Extract on new server
tar -xzf news-microservices.tar.gz -C /opt/

# 4. Manually configure .env files
```

---

## Secrets & Configuration Transfer

**WICHTIG:** `.env` files und Secrets NICHT in Git committen!

### Safe Transfer Methods

**Option 1: Manual Copy (Most Secure)**
```bash
# Copy from current server
scp .env.production user@new-server:/opt/news-microservices/

# Or edit directly on new server
ssh user@new-server
nano /opt/news-microservices/.env.production
```

**Option 2: Encrypted Transfer**
```bash
# Encrypt .env file
gpg -c .env.production
# Creates: .env.production.gpg

# Transfer encrypted file
scp .env.production.gpg user@new-server:/opt/news-microservices/

# Decrypt on new server
gpg -d .env.production.gpg > .env.production
rm .env.production.gpg
```

**Option 3: Secrets Management (Production)**
- Use **Vault** (HashiCorp)
- Use **AWS Secrets Manager**
- Use **Azure Key Vault**
- Use **Kubernetes Secrets**

---

## Verification After Transfer

```bash
# On new server, verify transfer
cd /opt/news-microservices

# Check critical files exist
ls -la docker-compose.prod.yml
ls -la services/*/Dockerfile
ls -la frontend/package.json

# Check secrets exist (but don't print!)
test -f .env.production && echo "✅ .env.production exists" || echo "❌ Missing!"

# Count services
ls -d services/*/ | wc -l
# Expected: 16+ directories

# Check git status (if using git)
git status
git log -1
```

---

## Quick Reference Table

| Method | Speed | Security | Version Control | Best For |
|--------|-------|----------|-----------------|----------|
| **Git Clone** | Medium | High (SSH keys) | ✅ Yes | Production, Teams |
| **rsync** | Fast | Medium (SSH) | ❌ No | Quick migrations |
| **tar + scp** | Medium | Medium (SSH) | ❌ No | Simple transfers |
| **Docker Registry** | Medium | High | ✅ Images only | CI/CD, Multiple servers |

---

## Complete Example: Current → New Server

```bash
# ============================================================================
# On CURRENT server (cytrex@current-server)
# ============================================================================

# 1. Prepare git repository
cd /home/cytrex/news-microservices
git add .
git commit -m "prepare for production deployment"
git push origin main

# 2. Export secrets (encrypted)
gpg -c .env.production
# Password: <YOUR_PASSWORD>

# 3. Transfer secrets to new server
scp .env.production.gpg user@new-server:/tmp/

# ============================================================================
# On NEW server (user@new-server)
# ============================================================================

# 1. Install prerequisites
sudo apt update && sudo apt install -y git docker.io docker-compose-v2
sudo usermod -aG docker $USER
sudo reboot

# 2. Clone repository
sudo mkdir -p /opt/news-microservices
sudo chown $USER:$USER /opt/news-microservices
cd /opt/news-microservices
git clone git@github.com:YOUR_USERNAME/news-microservices.git .

# 3. Restore secrets
gpg -d /tmp/.env.production.gpg > .env.production
rm /tmp/.env.production.gpg

# 4. Verify
ls -la .env.production
ls -la docker-compose.prod.yml

# 5. Deploy
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# 6. Verify deployment
./scripts/health_check.sh
```

---

## Troubleshooting

### Problem: Permission Denied (SSH)

```bash
# On current server, generate SSH key if needed
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key to new server
ssh-copy-id user@new-server

# Test connection
ssh user@new-server "echo Connection successful"
```

### Problem: Git Authentication Failed

```bash
# Option 1: Use personal access token (GitHub)
git clone https://USERNAME:TOKEN@github.com/YOUR_USERNAME/news-microservices.git

# Option 2: Use SSH (recommended)
ssh-keygen -t ed25519
cat ~/.ssh/id_ed25519.pub
# Add to GitHub: Settings → SSH and GPG keys → New SSH key
git clone git@github.com:YOUR_USERNAME/news-microservices.git
```

### Problem: Large Transfer Size

```bash
# Check what's taking space
du -sh news-microservices/*
du -sh news-microservices/.*

# Common culprits:
rm -rf news-microservices/venv/
rm -rf news-microservices/node_modules/
rm -rf news-microservices/.git/  # Only if not using git method!
```

---

## Best Practice Recommendations

1. **Use Git for Production** ✅
   - Enables version control
   - Easy rollbacks
   - Team collaboration

2. **Never commit secrets** ❌
   - Use `.gitignore`
   - Transfer .env files separately
   - Use secrets management tools

3. **Test transfer before deploying**
   - Verify all files present
   - Check file permissions
   - Run health checks

4. **Document your method**
   - Note which method you used
   - Document any custom scripts
   - Keep transfer logs

5. **Backup before migrating**
   - Backup current server data
   - Keep old server running during migration
   - Test new server thoroughly before shutting down old one

---

**Next Steps:**
1. Choose transfer method based on your scenario
2. Follow the guide: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
3. Use checklist: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
