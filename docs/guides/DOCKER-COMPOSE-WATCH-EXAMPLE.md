# Docker Compose Watch Mode - Beispiel & Evaluation

## Status Quo (Aktuell)

**Was wir verwenden:**
```yaml
# docker-compose.yml
frontend:
  volumes:
    - ./frontend/src:/app/src
    - ./frontend/apps:/app/apps
    - ./frontend/packages:/app/packages
```

**Performance:**
- Hot-Reload: < 1 Sekunde ✅
- Funktioniert einwandfrei ✅
- Einfach zu verstehen ✅

---

## Docker Compose Watch (Alternative)

**Moderne Syntax (seit v2.22):**
```yaml
# docker-compose.yml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.dev
  develop:
    watch:
      # Sync: Kopiert Änderungen in Container (kein rebuild)
      - action: sync
        path: ./frontend/src
        target: /app/src
        ignore:
          - "**/*.test.ts"
          - "**/*.test.tsx"

      - action: sync
        path: ./frontend/apps
        target: /app/apps

      - action: sync
        path: ./frontend/packages
        target: /app/packages

      # Rebuild: Bei Dependency-Änderungen
      - action: rebuild
        path: ./frontend/package.json

      - action: rebuild
        path: ./frontend/package-lock.json
```

**Verwendung:**
```bash
# Statt: docker compose up -d
docker compose watch

# Oder kombiniert:
docker compose up --watch
```

---

## Vergleich

| Feature | Volume Mounts (aktuell) | Watch Mode |
|---------|-------------------------|------------|
| **Setup** | Einfach | Mehr Konfiguration |
| **Performance** | < 1 Sek | < 1 Sek (ähnlich) |
| **Selektives Ignore** | Via .dockerignore | Pro Path konfigurierbar |
| **Auto-Rebuild** | Manuell | Automatisch bei package.json |
| **Debugging** | Einfach (Standard Volumes) | Komplexer |
| **Lernkurve** | Niedrig | Mittel |

---

## Vorteile von Watch Mode

### 1. Selektives File-Watching
```yaml
watch:
  - action: sync
    path: ./frontend/src
    ignore:
      - "**/*.test.ts"      # Test-Files nicht syncen
      - "**/__snapshots__"  # Snapshots ignorieren
      - "**/node_modules"   # Explizit excluden
```

**Vorteil:** Weniger I/O, schneller bei großen Projekten.

**Für uns:** Minimal, da Vite bereits effizient ist.

### 2. Intelligentes Rebuilding
```yaml
watch:
  - action: rebuild
    path: ./frontend/package.json  # Rebuild bei Dependencies
```

**Vorteil:** Automatischer Rebuild bei package.json Änderungen.

**Für uns:** Nützlich, aber selten (ändern package.json nicht täglich).

### 3. Verschiedene Actions
```yaml
watch:
  - action: sync       # Nur Datei kopieren
  - action: rebuild    # Container neu bauen
  - action: sync+restart  # Kopieren + Service neu starten
```

**Vorteil:** Granulare Kontrolle über Updates.

**Für uns:** Nice-to-have, nicht kritisch.

---

## Nachteile von Watch Mode

### 1. Komplexität
- Mehr Konfiguration pro Service
- Schwerer zu debuggen bei Problemen
- Team muss neue Syntax lernen

### 2. Overhead
- Docker muss File-Watching managen
- Zusätzlicher Prozess läuft

### 3. Eingeschränkte IDE-Integration
- Nicht alle IDEs verstehen watch mode
- Volume mounts funktionieren mit allen Tools

---

## Kosten-Nutzen-Analyse für UNSER Projekt

### ✅ Was wir haben (Volume Mounts)
```
Performance:      9/10 (< 1 Sek Hot-Reload)
Einfachheit:      10/10 (Jeder versteht es)
Debugging:        10/10 (Standard Docker Volumes)
Tooling Support:  10/10 (IDE, debugger funktionieren)
───────────────────────────────────────────────────
Gesamt:           9.75/10
```

### 🔧 Was wir bekommen würden (Watch Mode)
```
Performance:      9.5/10 (Minimal schneller bei großen Projects)
Einfachheit:      6/10 (Mehr Konfiguration)
Debugging:        7/10 (Komplexer)
Tooling Support:  8/10 (Neuere Syntax)
Features:         10/10 (Auto-rebuild, selektives ignore)
───────────────────────────────────────────────────
Gesamt:           8.1/10
```

---

## Empfehlung

### ❌ NICHT MIGRIEREN (aktuell)

**Gründe:**
1. Unser Hot-Reload ist bereits < 1 Sek ✅
2. Wir haben nur 10 Services (nicht 100) ✅
3. Volume mounts funktionieren perfekt ✅
4. Team kennt aktuelles Setup ✅

**Verbesserung durch watch mode:** ~5-10%
**Aufwand für Migration:** ~2-4 Stunden
**Risiko von Problemen:** Mittel

**Fazit:** Kosten > Nutzen

### ✅ WANN watch mode SINNVOLL WÄRE

1. **> 50 Services** → Intelligentes File-Watching hilft
2. **Sehr große Codebases** (100k+ Files) → Selektives Syncing schneller
3. **Häufige dependency changes** → Auto-rebuild spart Zeit
4. **Performance-Probleme** mit Volume Mounts → Watch mode als Alternative

**Für uns:** Nichts davon trifft zu.

---

## Stattdessen: Production Dockerfiles

**Priorität 1 (SOLLTEN WIR MACHEN):**

```
frontend/
├── Dockerfile.dev    # Development (bind mounts, hot reload)
└── Dockerfile        # Production (optimized build, nginx)
```

**Beispiel Production Dockerfile:**
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Nutzen:**
- CI/CD kann production-ready Images bauen
- Deployment-ready
- Security (keine dev-dependencies)
- Performance (optimized builds)

**Aufwand:** ~1 Stunde
**Nutzen:** HOCH (für Deployment essentiell)

---

## Fazit

### Was wir MACHEN sollten:
1. ✅ **Production Dockerfiles** erstellen (Priorität 1)
2. ✅ **CI/CD Pipeline** für Image-Builds (Priorität 2)
3. ✅ **Deployment-Strategie** definieren (Priorität 2)

### Was wir NICHT machen sollten:
1. ❌ Watch mode migration (minimaler Nutzen)
2. ❌ Tilt / Skaffold (Overkill)
3. ❌ Komplexität hinzufügen ohne klaren Vorteil

### Unser aktuelles Setup:
**Status:** ✅ OPTIMAL für unseren Use-Case

**Performance:** 9.75/10
**Einfachheit:** 10/10
**Maintainability:** 10/10

**Nächster logischer Schritt:** Production Dockerfiles, nicht watch mode.

---

**Datum:** 2025-10-18
**Review:** Bei Performance-Problemen watch mode evaluieren
**Nächste Action:** Production Dockerfile für Frontend erstellen
