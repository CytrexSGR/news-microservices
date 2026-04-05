# Git Certificate Cleanup Script - Documentation

## 📋 Overview

**Script:** `cleanup-git-certificates.sh`

**Purpose:** Remove all `.pem` certificate files from Git history while keeping them in the working directory.

**Use Case:** Before publishing repository to GitHub, ensure no private keys are in Git history.

---

## 🚀 Quick Start

### Basic Usage

```bash
# Navigate to project root
cd /home/cytrex/news-microservices

# Run script (interactive mode)
./scripts/cleanup-git-certificates.sh

# Or with auto-push
./scripts/cleanup-git-certificates.sh --auto-push
```

**Duration:** ~5-10 minutes (depending on repository size)

---

## 📖 What It Does

### Phase-by-Phase Breakdown

1. **Pre-flight Checks** ✈️
   - Verifies you're in correct directory
   - Checks for Git repository
   - Installs Java if needed
   - Commits any uncommitted changes
   - Shows what will be removed
   - Asks for confirmation

2. **Backup Creation** 💾
   - Full repository backup
   - Certificates backup
   - Creates restoration script
   - Logs backup locations

3. **BFG Download** ⬇️
   - Downloads BFG Repo-Cleaner (15 MB)
   - Verifies JAR integrity
   - Tests execution

4. **BFG Cleanup** 🧹
   - Removes `*.pem` from ALL commits
   - Rewrites Git history
   - Generates new commit hashes

5. **Git Garbage Collection** 🗑️
   - Expires reflog
   - Runs aggressive GC
   - Optimizes repository

6. **Certificate Restoration** 🔄
   - Restores certificates to working dir
   - Verifies file count
   - Shows restored files

7. **Verification** ✅
   - 7 comprehensive checks
   - Validates cleanup success
   - Tests old commits

8. **Push (Optional)** 🚀
   - Pushes to remote (with confirmation)
   - Force push required
   - Shows command for later

9. **Summary** 📊
   - Shows results
   - Lists backup locations
   - Provides next steps

---

## ⚙️ Command-Line Options

### `--auto-push`

Automatically push to remote after successful cleanup (no confirmation prompt).

```bash
./scripts/cleanup-git-certificates.sh --auto-push
```

**Use when:**
- Running in automated pipeline
- Sure about pushing immediately
- Want unattended execution

### `--help` / `-h`

Show help message and exit.

```bash
./scripts/cleanup-git-certificates.sh --help
```

---

## 🔍 What Gets Removed

### Files Removed from History

- `certs/rabbitmq/ca-key.pem`
- `certs/rabbitmq/ca-cert.pem`
- `certs/rabbitmq/server-key.pem`
- `certs/rabbitmq/server-cert.pem`
- `infrastructure/traefik/certs/cert.pem` (if exists)
- `infrastructure/traefik/certs/key.pem` (if exists)
- Any other `*.pem` files

### What Stays

- All certificates in working directory (restored after cleanup)
- All other files unchanged
- Commit messages unchanged
- Commit order unchanged
- Code unchanged

**Only thing that changes:** Commit hashes (because history is rewritten)

---

## 📊 Output Example

```
═══════════════════════════════════════════════════════════════
  PHASE 0: Pre-flight Checks
═══════════════════════════════════════════════════════════════

✓ Working directory: /home/cytrex/news-microservices
✓ Git repository detected
✓ Java found: openjdk version "11.0.x"
✓ Working directory clean
ℹ Current branch: feature/content-analysis-v2-admin
ℹ Commits in repository: 81
ℹ .pem files in history: 6
ℹ .pem files in working dir: 4

ℹ Files that will be removed from history:
  - certs/rabbitmq/ca-cert.pem
  - certs/rabbitmq/ca-key.pem
  - certs/rabbitmq/server-cert.pem
  - certs/rabbitmq/server-key.pem
  - infrastructure/traefik/certs/cert.pem
  - infrastructure/traefik/certs/key.pem

⚠ This will rewrite Git history!
⚠ All commit hashes will change
⚠ You will need to force-push to remote

? Continue with cleanup? [y/N]: y

═══════════════════════════════════════════════════════════════
  PHASE 1: Creating Backups
═══════════════════════════════════════════════════════════════

ℹ Creating full repository backup...
✓ Repository backup created: /home/cytrex/news-microservices-backup-20251103-120000 (2.8G)
ℹ Creating certificates backup...
✓ Certificates backed up: /home/cytrex/certs-backup-20251103-120000 (4 files)
✓ Restoration script created: /home/cytrex/restore-backup-20251103-120000.sh

[... continues through all phases ...]

═══════════════════════════════════════════════════════════════
  CLEANUP SUMMARY
═══════════════════════════════════════════════════════════════

Results:
  - Commits in repository: 81
  - .pem files in history: 0
  - .pem files locally: 4
  - Repository size: 45M

Backups created:
  - Full backup: /home/cytrex/news-microservices-backup-20251103-120000
  - Certificates: /home/cytrex/certs-backup-20251103-120000
  - Restore script: /home/cytrex/restore-backup-20251103-120000.sh

✓ Cleanup completed successfully!
```

---

## 🔧 Troubleshooting

### Problem: "Java not found"

**Error:**
```
bash: java: command not found
```

**Solution:**
Script will offer to install automatically, or:
```bash
sudo apt update
sudo apt install -y default-jre
java -version  # Verify
```

---

### Problem: "Uncommitted changes"

**Error:**
```
⚠ You have uncommitted changes
```

**Solution:**
Script will offer to commit them, or commit manually:
```bash
git add -A
git commit -m "chore: prepare for cleanup"
```

---

### Problem: "Not in project root"

**Error:**
```
✗ Not in project root! Expected: /home/cytrex/news-microservices
```

**Solution:**
```bash
cd /home/cytrex/news-microservices
./scripts/cleanup-git-certificates.sh
```

---

### Problem: "BFG download failed"

**Error:**
```
✗ Failed to download BFG
```

**Solution:**

1. **Check internet connection**
2. **Download manually:**
   ```bash
   wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O /tmp/bfg-1.14.0.jar
   ```
3. **Or from GitHub:**
   ```bash
   wget https://github.com/rtyley/bfg-repo-cleaner/releases/download/v1.14.0/bfg-1.14.0.jar -O /tmp/bfg-1.14.0.jar
   ```

---

### Problem: "Protected commits" error

**Error:**
```
Error: current HEAD contains *.pem files
```

**Solution:**
Script should handle this automatically by committing changes first. If it persists:
```bash
git rm --cached certs/rabbitmq/*.pem
git commit -m "chore: remove pem from HEAD"
./scripts/cleanup-git-certificates.sh
```

---

### Problem: Verification check fails

**Error:**
```
✗ Found X .pem files still in history!
```

**Solution:**

1. **Check which files:**
   ```bash
   git log --all --pretty=format: --name-only | grep '\.pem$' | sort | uniq
   ```

2. **Run BFG again manually:**
   ```bash
   cd /home/cytrex
   java -jar /tmp/bfg-1.14.0.jar --delete-files '*.pem' news-microservices
   cd news-microservices
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

---

### Problem: Certificates missing after cleanup

**Error:**
```
ls: cannot access 'certs/rabbitmq/*.pem': No such file or directory
```

**Solution:**

1. **Restore from backup:**
   ```bash
   cp -r /home/cytrex/certs-backup-YYYYMMDD-HHMMSS/rabbitmq/* certs/rabbitmq/
   ```

2. **Verify:**
   ```bash
   ls -lh certs/rabbitmq/*.pem
   ```

---

### Problem: Push fails

**Error:**
```
✗ Push failed
```

**Solutions:**

1. **Check authentication:**
   ```bash
   git remote -v
   # If using token: update .env and retry
   ```

2. **Push manually:**
   ```bash
   git push -f origin feature/content-analysis-v2-admin
   ```

3. **If remote ahead:**
   ```bash
   # This is expected after history rewrite
   git push -f origin feature/content-analysis-v2-admin
   ```

---

## 🔄 Recovery / Rollback

### If Something Goes Wrong

The script creates automatic backups. To restore:

```bash
# Option 1: Use auto-generated restoration script
bash /home/cytrex/restore-backup-YYYYMMDD-HHMMSS.sh

# Option 2: Manual restoration
cd /home/cytrex
rm -rf news-microservices
cp -r news-microservices-backup-YYYYMMDD-HHMMSS news-microservices
cd news-microservices
```

### Verify Restoration

```bash
git log --oneline -5  # Check commits
ls certs/rabbitmq/*.pem  # Check certificates
git status  # Check clean state
```

---

## 📝 What to Do After Cleanup

### 1. Verify RabbitMQ Still Works

```bash
docker compose up -d rabbitmq
docker compose logs rabbitmq | grep -i "ssl\|tls\|certificate"
# Should show: "Starting TLS listeners"
```

### 2. Push All Branches

```bash
# Current branch (already pushed if used --auto-push)
git push -f origin feature/content-analysis-v2-admin

# Other branches
git push -f origin feature/feed-service-api-fix
git push -f origin feature/feed-service-fix
git push -f origin feature/scheduler-phase2-monitoring

# Or push all at once
git push -f --all origin
```

### 3. Clean Master Worktree

```bash
cd /home/cytrex/news-microservices-main

# Option A: Also clean master
../news-microservices/scripts/cleanup-git-certificates.sh

# Option B: Pull from cleaned branch
git fetch origin feature/content-analysis-v2-admin
git merge origin/feature/content-analysis-v2-admin
```

### 4. Update .gitignore (if not done)

Ensure `.gitignore` contains:
```gitignore
# Certificates
certs/
*.pem
```

Verify:
```bash
git check-ignore certs/rabbitmq/ca-key.pem
# Should output: certs/rabbitmq/ca-key.pem
```

### 5. Cleanup Old Backups

**After 1-2 days** (when confident everything works):

```bash
# List backups
ls -lh /home/cytrex/news-microservices-backup-*
ls -lh /home/cytrex/certs-backup-*

# Delete when no longer needed
sudo rm -rf /home/cytrex/news-microservices-backup-YYYYMMDD-HHMMSS
rm -rf /home/cytrex/certs-backup-YYYYMMDD-HHMMSS
rm /home/cytrex/restore-backup-YYYYMMDD-HHMMSS.sh
```

---

## 🔒 Security Notes

### What This Script Does for Security

✅ **Removes private keys from Git history**
✅ **Creates secure backups**
✅ **Prevents future commits via .gitignore**
✅ **Keeps keys functional locally**

### What This Script Does NOT Do

❌ Does not rotate/regenerate keys (keys stay the same)
❌ Does not encrypt backups (they're plain copies)
❌ Does not delete keys from GitHub if already pushed (you need to push -f)

### Best Practices After Cleanup

1. **Verify .gitignore:** Ensure future protection
2. **Document key locations:** Update README/docs
3. **Limit repo access:** Keep private
4. **Monitor access:** Check GitHub access logs
5. **Consider key rotation:** If keys were public, rotate them

---

## 📊 Technical Details

### How BFG Works

1. **Scans all commits** in repository
2. **Identifies matching files** (*.pem)
3. **Removes files from each commit**
4. **Writes new commits** (new hashes)
5. **Preserves commit messages and order**
6. **Protects current HEAD** (files stay in working dir)

### Why Force Push Required

- Git history is **immutable** by design
- Rewriting = creating **new commits** with new hashes
- Remote still has **old commits** with old hashes
- Force push **replaces** remote history with new history

### Repository Size Impact

Typical size reduction:
- Small certs (4 KB each): ~20-30 KB total reduction
- After GC compression: ~10-15 KB net reduction
- `.git` folder: Slightly smaller
- Working directory: Unchanged

Not dramatic because:
- Certs are small (3-4 KB each)
- Git compresses efficiently
- Most space is code/dependencies

---

## 🧪 Testing the Script

### Dry-Run Test (Safe)

Create a test repository:
```bash
# Create test repo
cd /tmp
git clone /home/cytrex/news-microservices test-cleanup
cd test-cleanup

# Run cleanup (won't affect original)
./scripts/cleanup-git-certificates.sh
```

### Verify Script Logic

```bash
# Check script syntax
bash -n scripts/cleanup-git-certificates.sh

# Run with debug
bash -x scripts/cleanup-git-certificates.sh 2>&1 | tee cleanup-debug.log
```

---

## 📞 Support

### Log Files

Script creates detailed log: `cleanup-git-certs-YYYYMMDD-HHMMSS.log`

Contains:
- All commands executed
- Full output from BFG
- Verification results
- Error messages

### If You Need Help

1. **Check log file** first
2. **Review troubleshooting section** above
3. **Check backups exist:**
   ```bash
   ls -lh /home/cytrex/news-microservices-backup-*
   ```
4. **Review BFG docs:** https://rtyley.github.io/bfg-repo-cleaner/

---

## 📚 Additional Resources

- **BFG Repo-Cleaner:** https://rtyley.github.io/bfg-repo-cleaner/
- **Git History Rewriting:** https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
- **Force Push Safely:** https://git-scm.com/docs/git-push#Documentation/git-push.txt---force
- **Git Reflog:** https://git-scm.com/docs/git-reflog
- **Garbage Collection:** https://git-scm.com/docs/git-gc

---

## ✅ Checklist: Before Running

- [ ] Committed all changes
- [ ] Verified backups will be created
- [ ] Understood force-push requirement
- [ ] Checked no one else is working on repo
- [ ] Java installed (or allow script to install)
- [ ] Internet connection (for BFG download)
- [ ] Read this documentation

## ✅ Checklist: After Running

- [ ] Verified certificates restored locally
- [ ] Verified no .pem in Git history
- [ ] Tested RabbitMQ with certificates
- [ ] Force-pushed to GitHub
- [ ] Updated other branches if needed
- [ ] Kept backups for 1-2 days
- [ ] Updated documentation
- [ ] Verified .gitignore working

---

**Last Updated:** 2025-11-03
**Script Version:** 1.0.0
**Tested With:** Git 2.34+, Java 11+, BFG 1.14.0
