# 🚀 Quick Start: Certificate Cleanup

## One-Command Execution

```bash
cd /home/cytrex/news-microservices
./scripts/cleanup-git-certificates.sh
```

**Duration:** 5-10 minutes
**Interactive:** Yes (asks for confirmation before critical steps)

---

## What Happens

1. ✅ Checks prerequisites (Git, Java)
2. 💾 Creates backups (repo + certificates)
3. ⬇️ Downloads BFG Repo-Cleaner
4. 🧹 Removes `*.pem` from Git history
5. 🗑️ Runs garbage collection
6. 🔄 Restores certificates locally
7. ✓ Verifies cleanup success
8. 🚀 Optionally pushes to GitHub

---

## Common Usage

### Basic (with prompts)
```bash
./scripts/cleanup-git-certificates.sh
```

### With auto-push
```bash
./scripts/cleanup-git-certificates.sh --auto-push
```

### Show help
```bash
./scripts/cleanup-git-certificates.sh --help
```

---

## After Script Completes

### 1. Verify RabbitMQ
```bash
docker compose up -d rabbitmq
docker compose logs rabbitmq | grep -i certificate
```

### 2. Push other branches
```bash
git push -f origin feature/feed-service-api-fix
git push -f origin feature/feed-service-fix
```

### 3. Check results
```bash
# No .pem in history
git log --all --pretty=format: --name-only | grep '\.pem$'
# (should be empty)

# Certificates exist locally
ls -lh certs/rabbitmq/*.pem
# (should show 4 files)
```

---

## If Something Goes Wrong

### Restore backup
```bash
bash /home/cytrex/restore-backup-YYYYMMDD-HHMMSS.sh
```

### Or manually
```bash
rm -rf /home/cytrex/news-microservices
cp -r /home/cytrex/news-microservices-backup-YYYYMMDD-HHMMSS /home/cytrex/news-microservices
```

---

## Files Created

- `cleanup-git-certs-YYYYMMDD-HHMMSS.log` - Detailed log
- `/home/cytrex/news-microservices-backup-YYYYMMDD-HHMMSS/` - Full backup
- `/home/cytrex/certs-backup-YYYYMMDD-HHMMSS/` - Certificate backup
- `/home/cytrex/restore-backup-YYYYMMDD-HHMMSS.sh` - Restoration script

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Java not found | Script will install it automatically |
| Uncommitted changes | Script will commit them for you |
| BFG download fails | Check internet connection |
| Push fails | Run manually: `git push -f origin <branch>` |
| Certs missing | Restore: `cp -r /home/cytrex/certs-backup-*/rabbitmq/* certs/rabbitmq/` |

---

## Need More Details?

📚 **Full Documentation:** `scripts/README.cleanup-git-certificates.md`

---

**Quick Checklist:**
- [ ] Run script
- [ ] Test RabbitMQ
- [ ] Push to GitHub
- [ ] Keep backups for 1-2 days
- [ ] Delete backups when done

**That's it!** 🎉
