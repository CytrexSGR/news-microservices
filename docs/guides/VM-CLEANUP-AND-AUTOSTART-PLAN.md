# VM Cleanup & Auto-Start Configuration Plan

**Datum:** 2025-10-24
**Ziel:** Aufgeräumtes System mit automatischem Anwendungsstart bei VM-Neustart
**Geschätzte Dauer:** 45-60 Minuten
**Geschätzte Speicherersparnis:** ~1.5GB

---

## 📊 System-Analyse Ergebnisse

### Disk Usage
```
Gesamtkapazität: 62GB
Verwendet: 30GB (52%)
Verfügbar: 29GB
```

### Größte Verzeichnisse
```
3.2GB  news-microservices (davon ~900MB venvs)
688MB  backups (alte Backups konsolidieren)
```

### Docker Status
```
Images: 17 (6.8GB total)
Container: 17 (16 running, 1 restart-loop)
Volumes: 5 (403MB total)
Build Cache: 1.098GB ← Aufräumen!
```

### Zu bereinigende Dateien/Verzeichnisse
```
2,351 Dateien/Verzeichnisse:
  - venv/ (Python virtual environments)
  - node_modules/ (NPM packages)
  - __pycache__/ (Python bytecode)
  - *.pyc (Python compiled files)
```

### Identifizierte Probleme
```
⚠️  news-search-service     → Restart-Loop (Exit 3)
⚠️  news-notification-service → Unhealthy
⚠️  news-analytics-celery-beat → Unhealthy
```

---

## 🎯 Aufräumplan (7 Phasen)

### Phase 1: Service-Probleme Beheben ⚠️  **KRITISCH**

**Ziel:** Alle Services gesund vor Backup

#### 1.1 Search-Service Debug
```bash
# Logs analysieren
docker logs news-search-service --tail 100

# Container stoppen und neu starten
docker compose stop search-service
docker compose up -d search-service

# Falls nicht behoben: Service temporär deaktivieren
# (in docker-compose.yml kommentieren)
```

**Erwartetes Ergebnis:** Service läuft healthy ODER ist dokumentiert deaktiviert

#### 1.2 Notification-Service Health Check
```bash
# Health-Endpoint prüfen
docker exec news-notification-service curl -f http://localhost:8105/health || echo "Failed"

# Logs prüfen
docker logs news-notification-service --tail 50

# Restart
docker compose restart notification-service
```

#### 1.3 Analytics-Celery-Beat Health Check
```bash
# Logs prüfen
docker logs news-analytics-celery-beat --tail 50

# Restart
docker compose restart analytics-celery-beat
```

**Zeit:** 10 Minuten
**Kritikalität:** HOCH - Backup nur von gesundem System!

---

### Phase 2: Docker Build Cache Cleanup 🧹

**Ziel:** 1.098GB Build Cache freigeben

```bash
# Anzeigen was gelöscht würde (Dry Run)
docker builder prune --filter "until=24h" --dry-run

# Tatsächlich löschen (alles älter als 24h)
docker builder prune --filter "until=24h" -f

# ODER: Komplette Build-Cache Löschung (aggressiv)
docker builder prune -af
```

**Geschätzte Ersparnis:** ~1.098GB
**Zeit:** 2 Minuten
**Risiko:** NIEDRIG (Cache wird bei nächstem Build neu erstellt)

---

### Phase 3: Alte Backups Konsolidieren 📦

**Ziel:** Backup-Verzeichnis aufräumen und konsolidieren

#### 3.1 Backup-Inventar
```bash
# Zeige alle Backups mit Datum und Größe
ls -lh /home/cytrex/backups/

# Aktuell:
# - analytics-frontend-backup-20251021.tar.gz (40MB)
# - news-ms-20251021.tar.gz (323MB)
# - news-ms-$(date +%Y%m%d-%H%M%S).tar.gz (323MB - fehlerhafter Name!)
# - news-microservices-code-backup-20251022_183511.tar.gz (1.9MB)
# - frontend-git-backup-20251021/ (Directory)
```

#### 3.2 Alte Backups Archivieren
```bash
# Erstelle Archiv-Verzeichnis
mkdir -p /home/cytrex/backups/archive-2025-10

# Verschiebe alle Backups älter als 3 Tage
find /home/cytrex/backups -maxdepth 1 -type f -mtime +3 -exec mv {} /home/cytrex/backups/archive-2025-10/ \;

# Komprimiere Archiv
cd /home/cytrex/backups
tar -czf archive-2025-10.tar.gz archive-2025-10/
rm -rf archive-2025-10/
```

**Geschätzte Ersparnis:** ~400MB
**Zeit:** 3 Minuten

---

### Phase 4: Python VENVs & Node Modules Cleanup 🐍

**Ziel:** Temporäre Build-Artefakte entfernen (werden in Docker nicht benötigt)

#### 4.1 VENVs Entfernen (außer development)
```bash
# Liste alle venv Verzeichnisse
find /home/cytrex/news-microservices -name "venv" -type d

# Entferne Service-VENVs (werden in Docker nicht benötigt)
rm -rf /home/cytrex/news-microservices/services/*/venv

# Behalte nur Root-VENV für lokale Entwicklung
# /home/cytrex/news-microservices/venv (BEHALTEN)
```

**Geschätzte Ersparnis:** ~900MB
**Risiko:** NIEDRIG (VENVs nur für lokale Entwicklung, nicht für Docker)

#### 4.2 Node Modules Prüfen
```bash
# Finde node_modules
find /home/cytrex/news-microservices -name "node_modules" -type d

# Frontend node_modules wird für Standalone-Betrieb benötigt
# → NICHT LÖSCHEN
```

#### 4.3 Python Cache Cleanup
```bash
# Entferne __pycache__ und .pyc
find /home/cytrex/news-microservices -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /home/cytrex/news-microservices -type f -name "*.pyc" -delete
```

**Geschätzte Ersparnis:** ~50MB
**Zeit:** 5 Minuten

---

### Phase 5: Vollständiges Backup Erstellen 💾

**Ziel:** Komplettes Backup OHNE venvs, node_modules, caches

#### 5.1 Backup-Strategie

**Was wird gesichert:**
```
✅ Alle Source-Code Dateien (.py, .tsx, .ts, .js, .md)
✅ Konfigurationsdateien (.env, .yml, Dockerfile)
✅ Datenbank-Schemas (database/models/)
✅ Dokumentation (docs/)
✅ Tests (tests/)
✅ Scripts (scripts/)
✅ Git-Repository (.git/)
```

**Was wird AUSGESCHLOSSEN:**
```
❌ venv/ (Python virtual environments)
❌ node_modules/ (NPM packages)
❌ __pycache__/ (Python bytecode cache)
❌ *.pyc, *.pyo (Python compiled files)
❌ .pytest_cache/ (Pytest cache)
❌ .coverage (Coverage reports)
❌ *.log (Log files)
❌ dist/, build/ (Build artifacts)
❌ .DS_Store (macOS files)
```

#### 5.2 Backup-Script

**Datei:** `/home/cytrex/news-microservices/scripts/create-clean-backup.sh`

```bash
#!/bin/bash
# VM Clean Backup Script - Exclusions für optimale Backup-Größe

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="news-ms-clean-backup-${BACKUP_DATE}"
BACKUP_DIR="/home/cytrex/backups"
SOURCE_DIR="/home/cytrex/news-microservices"

echo "🔍 Creating clean backup: ${BACKUP_NAME}"
echo "📁 Source: ${SOURCE_DIR}"
echo "💾 Destination: ${BACKUP_DIR}"

# Erstelle Backup mit Exclusions
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='.pytest_cache' \
  --exclude='.coverage' \
  --exclude='*.log' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.DS_Store' \
  --exclude='*.sqlite' \
  --exclude='*.db' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  -C /home/cytrex news-microservices

# Backup-Statistiken
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
echo ""
echo "✅ Backup completed successfully!"
echo "📦 File: ${BACKUP_NAME}.tar.gz"
echo "💾 Size: ${BACKUP_SIZE}"
echo ""

# Erstelle Backup-Report
cat > "${BACKUP_DIR}/${BACKUP_NAME}-report.txt" <<EOF
Backup Report
=============
Date: $(date)
Source: ${SOURCE_DIR}
Backup File: ${BACKUP_NAME}.tar.gz
Size: ${BACKUP_SIZE}

Contents:
---------
$(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | head -50)
...

File Count:
-----------
$(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | wc -l) files

Exclusions:
-----------
- venv/
- node_modules/
- __pycache__/
- *.pyc, *.pyo
- .pytest_cache/
- .coverage
- *.log
- dist/, build/
- .DS_Store
EOF

echo "📄 Backup report: ${BACKUP_NAME}-report.txt"
echo ""
echo "🔍 Backup verification:"
tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | grep -c "\.py$" || true
echo " Python files backed up"
```

#### 5.3 Backup Execution
```bash
# Script ausführbar machen
chmod +x /home/cytrex/news-microservices/scripts/create-clean-backup.sh

# Backup erstellen
/home/cytrex/news-microservices/scripts/create-clean-backup.sh
```

**Geschätzte Backup-Größe:** ~100-150MB (statt 3.2GB!)
**Zeit:** 5 Minuten

---

### Phase 6: Auto-Start Konfiguration 🚀

**Ziel:** Docker Compose startet automatisch beim VM-Boot

#### 6.1 Systemd Service Erstellen

**Datei:** `/etc/systemd/system/news-microservices.service`

```ini
[Unit]
Description=News Microservices Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/cytrex/news-microservices
User=cytrex
Group=cytrex

# Environment variables
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Start command
ExecStart=/usr/bin/docker compose up -d

# Stop command
ExecStop=/usr/bin/docker compose down

# Restart policy
Restart=on-failure
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 6.2 Service Installation
```bash
# Erstelle Service-Datei
sudo tee /etc/systemd/system/news-microservices.service > /dev/null <<'EOF'
[Unit]
Description=News Microservices Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/cytrex/news-microservices
User=cytrex
Group=cytrex
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Service aktivieren (Auto-Start beim Boot)
sudo systemctl enable news-microservices.service

# Service Status prüfen
sudo systemctl status news-microservices.service
```

#### 6.3 Service Testing
```bash
# Test 1: Manueller Start
sudo systemctl start news-microservices.service
docker ps  # Alle Container sollten laufen

# Test 2: Manueller Stop
sudo systemctl stop news-microservices.service
docker ps  # Keine news-* Container

# Test 3: Erneuter Start
sudo systemctl start news-microservices.service
docker ps  # Container wieder da

# Test 4: Status und Logs
sudo systemctl status news-microservices.service
sudo journalctl -u news-microservices.service -n 50
```

**Zeit:** 10 Minuten

---

### Phase 7: Validierung & Testing 🧪

**Ziel:** Vollständige Funktionsprüfung vor Reboot

#### 7.1 Service Health Checks
```bash
# Warte bis alle Container hochgefahren sind
sleep 30

# Prüfe alle Services
for service in auth feed content-analysis research osint notification search analytics scheduler scraping; do
  echo "Checking $service..."
  docker ps --filter "name=news-$service" --format "{{.Names}}\t{{.Status}}"
done

# Detaillierter Health-Check
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

#### 7.2 API Endpoints Testen
```bash
# Auth Service
curl -f http://localhost:8100/health || echo "❌ Auth failed"

# Feed Service
curl -f http://localhost:8101/health || echo "❌ Feed failed"

# Content Analysis
curl -f http://localhost:8102/health || echo "❌ Analysis failed"

# Frontend
curl -f http://localhost:3000 || echo "❌ Frontend failed"
```

#### 7.3 Datenbank Connectivity
```bash
# PostgreSQL
docker exec postgres psql -U news_user -d news_mcp -c "SELECT 1;" || echo "❌ DB failed"

# Redis
docker exec redis redis-cli ping || echo "❌ Redis failed"

# RabbitMQ
curl -f http://localhost:15672 || echo "❌ RabbitMQ failed"
```

#### 7.4 Auto-Start Simulation
```bash
# Stoppe alle Container
sudo systemctl stop news-microservices.service

# Warte 5 Sekunden
sleep 5

# Starte via systemd (simuliert Reboot)
sudo systemctl start news-microservices.service

# Warte auf Container-Start
sleep 30

# Validiere dass alles hochgefahren ist
docker ps | grep -c "news-" | grep 14  # 14 news-* Container erwartet
```

**Zeit:** 10 Minuten

---

## 📝 Execution Checklist

### Pre-Flight Checks
```
[ ] Alle Services laufen aktuell
[ ] Keine wichtigen Daten in Bearbeitung
[ ] Mindestens 30GB freier Speicherplatz
[ ] Backup-Verzeichnis existiert: /home/cytrex/backups
[ ] User hat sudo-Rechte
```

### Phase 1: Service-Probleme Beheben
```
[ ] Search-Service geprüft und repariert
[ ] Notification-Service healthy
[ ] Analytics-Celery-Beat healthy
[ ] Alle Container im Status "Up" (außer Search falls deaktiviert)
```

### Phase 2: Docker Cleanup
```
[ ] Build Cache Größe geprüft: docker system df
[ ] Build Cache gelöscht: docker builder prune -af
[ ] Speicherersparnis verifiziert: ~1.1GB
```

### Phase 3: Backup Konsolidierung
```
[ ] Alte Backups identifiziert
[ ] Archiv-Verzeichnis erstellt
[ ] Alte Backups archiviert
[ ] Speicherersparnis verifiziert: ~400MB
```

### Phase 4: VENVs & Cache Cleanup
```
[ ] Service-VENVs gelöscht (außer Root-VENV)
[ ] __pycache__ Verzeichnisse gelöscht
[ ] *.pyc Dateien gelöscht
[ ] Speicherersparnis verifiziert: ~950MB
```

### Phase 5: Vollständiges Backup
```
[ ] Backup-Script erstellt: create-clean-backup.sh
[ ] Backup-Script ausführbar: chmod +x
[ ] Backup erfolgreich erstellt
[ ] Backup-Größe geprüft: ~100-150MB
[ ] Backup-Report generiert
[ ] Backup-Integrität geprüft: tar -tzf
```

### Phase 6: Auto-Start Konfiguration
```
[ ] Systemd Service-Datei erstellt
[ ] Service installiert und enabled
[ ] Service manuell getestet (start/stop)
[ ] Service-Logs geprüft: journalctl
```

### Phase 7: Validierung
```
[ ] Alle Container laufen healthy
[ ] API Endpoints erreichbar
[ ] Datenbank-Connectivity OK
[ ] Auto-Start Simulation erfolgreich
[ ] System bereit für Reboot-Test
```

---

## 🔄 Reboot-Test Procedure

**Nachdem alle Phasen abgeschlossen sind:**

```bash
# 1. Finaler Status-Check
docker ps
sudo systemctl status news-microservices.service

# 2. System neu starten
sudo reboot

# 3. Nach Reboot (SSH reconnect nach ~2 Minuten):
# Warte auf vollständigen Boot
sleep 60

# 4. Validiere Auto-Start
docker ps --format "table {{.Names}}\t{{.Status}}"

# Erwartetes Ergebnis:
# - Alle 17 Container laufen
# - Alle healthy Services sind healthy
# - Frontend unter http://localhost:3000 erreichbar

# 5. Service-Status prüfen
sudo systemctl status news-microservices.service

# Erwartetes Ergebnis:
# ● news-microservices.service - News Microservices Application
#    Loaded: loaded (/etc/systemd/system/news-microservices.service; enabled)
#    Active: active (exited)
```

---

## 📊 Erwartete Ergebnisse

### Speicherersparnis
```
Docker Build Cache:    -1,098 MB
VENVs:                   -900 MB
Python Cache:             -50 MB
Alte Backups:            -400 MB
──────────────────────────────────
GESAMT:                -2,448 MB (~2.4GB)
```

### Neues Backup
```
Vorher: 3.2GB (mit venvs, node_modules)
Nachher: ~150MB (nur Source-Code, Config, Docs)
──────────────────────────────────
Kompression: 95.3% kleiner!
```

### System-Status
```
✅ Docker Auto-Start: Aktiviert
✅ Application Auto-Start: Aktiviert (via systemd)
✅ Alle Services: Healthy
✅ Backup: Aktuell und kompakt
✅ Disk Usage: <45% (vorher 52%)
```

---

## 🚨 Rollback-Plan

Falls etwas schief geht:

### Rollback Phase 6 (Auto-Start)
```bash
# Service deaktivieren
sudo systemctl disable news-microservices.service
sudo systemctl stop news-microservices.service

# Service-Datei entfernen
sudo rm /etc/systemd/system/news-microservices.service
sudo systemctl daemon-reload

# Manuell starten
cd /home/cytrex/news-microservices
docker compose up -d
```

### Rollback Phase 5 (Backup wiederherstellen)
```bash
# Neuestes Backup finden
ls -lth /home/cytrex/backups/*.tar.gz | head -1

# Backup extrahieren (VORSICHT: Überschreibt aktuellen Code!)
cd /home/cytrex
tar -xzf backups/news-ms-clean-backup-YYYYMMDD_HHMMSS.tar.gz
```

### Rollback Phase 4 (VENVs neu erstellen)
```bash
# Für jeden Service
cd /home/cytrex/news-microservices/services/auth-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 Support

Bei Problemen während der Ausführung:

1. **Logs prüfen:**
   ```bash
   sudo journalctl -u news-microservices.service -n 100
   docker compose logs --tail 100
   ```

2. **Status prüfen:**
   ```bash
   sudo systemctl status news-microservices.service
   docker ps -a
   ```

3. **Rollback durchführen** (siehe oben)

---

## ✅ Final Checklist

Nach vollständiger Ausführung:

```
[ ] System neu gestartet
[ ] Alle Container starten automatisch
[ ] Alle Services healthy
[ ] Frontend erreichbar
[ ] APIs funktionsfähig
[ ] Backup erstellt und verifiziert
[ ] ~2.4GB Speicher freigegeben
[ ] Auto-Start funktioniert nach Reboot
[ ] Dokumentation aktualisiert
```

**Status:** BEREIT FÜR AUSFÜHRUNG
**Geschätzte Gesamtdauer:** 45-60 Minuten
**Risiko:** NIEDRIG (mit Rollback-Plan)
