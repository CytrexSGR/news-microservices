# Scraping Service: VPN/Proxy Design

**Datum:** 2026-01-06
**Status:** Geplant (nicht implementiert)
**Autor:** Claude + Andreas

---

## 1. Ausgangssituation

### Ziele
- Rate-Limiting umgehen bei News-Seiten
- IP-Bans vermeiden
- Anonymität beim Scraping
- Geo-Blocking umgehen (Zugriff auf internationale Inhalte)

### Anforderungen
- ~2000 Requests/Tag (Tendenz steigend)
- Keine Störung anderer Services
- Nutzung vorhandener NordVPN-Subscription

### Vorhandene Ressourcen
- NordVPN Unlimited Subscription
- Service Credentials in `/home/cytrex/.env`:
  ```
  nordvpn=e9f2ab3bea4538ad60dfa4dcd8e68aa37213b1c2ba4661b4914e6c0fa8f6dba9
  nordvpn benutzername=MUfpjZKm7Cw8QQGWCU3BgZkQ
  nordvpn passowrt=y91tEx8KDe7Adybb7AQimLsC
  ```

---

## 2. Bestehende Proxy-Infrastruktur im Scraping-Service

Der Scraping-Service hat **bereits vollständige Proxy-Unterstützung** implementiert:

### Dateien
- `app/services/proxy_manager.py` - Proxy Manager mit Rotation, Health Checking
- `app/models/proxy.py` - Datenmodelle (ProxyConfig, ProxyHealth, etc.)
- `app/api/proxy.py` - REST API für Proxy-Management

### Features
| Feature | Beschreibung |
|---------|--------------|
| Proxy-Typen | HTTP, HTTPS, SOCKS5 |
| Rotation | Round-robin, Random, Weighted |
| Health Monitoring | Automatische Verfügbarkeitsprüfung |
| Circuit Breaking | Proxy wird nach X Fehlern deaktiviert |
| Domain Affinity | Gleicher Proxy für gleiche Domain |

### API Endpoints
- `GET /api/v1/proxy/stats` - Pool-Statistiken
- `POST /api/v1/proxy/add` - Proxy hinzufügen
- `POST /api/v1/proxy/add-batch` - Mehrere Proxies hinzufügen
- `GET /api/v1/proxy/for-domain/{domain}` - Besten Proxy für Domain

### Aktivierung
```yaml
# docker-compose.yml
ENABLE_PROXY_ROTATION: "true"
```

---

## 3. Evaluierte Optionen

### Option A: NordVPN SOCKS5 Proxies

**Konzept:** Direkte Nutzung der NordVPN SOCKS5-Server über den bestehenden ProxyManager.

**Server (getestet am 2026-01-06):**

| Server | Status | IP |
|--------|--------|-----|
| us.socks.nordhold.net | ✅ OK | 87.239.255.65 |
| se.socks.nordhold.net | ✅ OK | 185.236.42.49 |
| stockholm.se.socks.nordhold.net | ✅ OK | 185.236.42.35 |
| atlanta.us.socks.nordhold.net | ✅ OK | 196.196.27.164 |
| chicago.us.socks.nordhold.net | ✅ OK | 193.19.206.47 |
| dallas.us.socks.nordhold.net | ✅ OK | 146.70.217.214 |
| new-york.us.socks.nordhold.net | ✅ OK | 185.184.228.130 |
| nl.socks.nordhold.net | ❌ Down | - |
| amsterdam.nl.socks.nordhold.net | ❌ Down | - |
| los-angeles.us.socks.nordhold.net | ❌ Down | - |

**Wichtig:** SOCKS5 läuft auf `*.socks.nordhold.net:1080`, NICHT auf den normalen VPN-Servern!

**Test-Befehl:**
```bash
curl --socks5-hostname us.socks.nordhold.net:1080 \
     --proxy-user "MUfpjZKm7Cw8QQGWCU3BgZkQ:y91tEx8KDe7Adybb7AQimLsC" \
     https://ifconfig.me
```

**Bewertung:**
| Pro | Contra |
|-----|--------|
| Bereits implementiert | Nur ~7-12 Server weltweit |
| Instant Rotation pro Request | Keine deutschen Server (NL down) |
| Einfaches Setup | Datacenter IPs (erkennbar) |

---

### Option B: VPN auf Container-Ebene (Empfohlen)

**Konzept:** Dedizierter VPN-Container, nur Scraping-Service nutzt dessen Netzwerk.

**Architektur:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host                               │
│                                                              │
│  auth-service ─────────────────────► Internet (normal)      │
│  feed-service ─────────────────────► Internet (normal)      │
│  frontend ─────────────────────────► Internet (normal)      │
│  SSH/Terminal ─────────────────────► Lokal (normal)         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  scraping-service ──► vpn-container ──► VPN ──► Web │    │
│  │  (NUR dieser Traffic geht durch VPN)                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Keine Störung anderer Services oder SSH-Verbindungen!**

**Docker Compose Beispiel:**
```yaml
services:
  vpn:
    image: ghcr.io/bubuntux/nordvpn
    container_name: news-vpn
    cap_add:
      - NET_ADMIN
      - NET_RAW
    sysctls:
      - net.ipv6.conf.all.disable_ipv6=1
    environment:
      - TOKEN=${NORDVPN_TOKEN}
      - CONNECT=Germany
      - TECHNOLOGY=NordLynx  # oder OpenVPN
      - NETWORK=localhost/24  # Lokales Netz whitelist
    ports:
      - "8105:8000"  # Scraping-Service Port
    restart: unless-stopped

  scraping-service:
    build: ./services/scraping-service
    network_mode: "service:vpn"  # Teilt Netzwerk mit VPN
    depends_on:
      vpn:
        condition: service_healthy
    environment:
      # ... normale env vars
```

**Server-Auswahl:**
- 5000+ Server verfügbar
- Kann periodisch gewechselt werden
- Deutsche Server verfügbar (de1184.nordvpn.com, etc.)

**Port-Test (2026-01-06):**
- Port 443 (TCP): ✅ Funktioniert
- Port 1194 (UDP): ❌ Timeout (evtl. ISP-Blocking)
- Port 1080 (SOCKS5): ❌ Timeout auf VPN-Servern (nur auf nordhold.net)

**Bewertung:**
| Pro | Contra |
|-----|--------|
| 5000+ Server | Komplexeres Setup |
| Deutsche Server verfügbar | Kein Instant-Wechsel (~5-10s Reconnect) |
| Vollständige Verschlüsselung | Braucht NET_ADMIN capability |
| Isoliert (stört nichts anderes) | |

---

### Option C: Kommerzielle Proxy-Provider

**Anbieter:** Brightdata, Smartproxy, Oxylabs, etc.

**Kosten:** ~$10-15/GB oder ~$300-500/Monat

**Bewertung:** Overkill für aktuellen Use-Case. Sinnvoll wenn:
- NordVPN nicht mehr ausreicht
- Residential IPs benötigt werden
- Sehr hohes Volumen (>10.000 Req/Tag)

---

## 4. Empfehlung

### Primär: Option B (VPN-Container)

**Gründe:**
1. 5000+ Server vs. nur 7 SOCKS5-Server
2. Deutsche Server verfügbar (wichtig für deutsche News)
3. Vollständige Verschlüsselung
4. Keine Störung anderer Services durch Docker-Isolation
5. NordVPN-Subscription bereits vorhanden (keine Extrakosten)

### Fallback: Option A (SOCKS5)

Falls VPN-Container Probleme macht, kann SOCKS5 als schnelle Alternative genutzt werden. Die Infrastruktur im Scraping-Service ist bereits vorhanden.

---

## 5. Implementierungsschritte (wenn gewünscht)

### Phase 1: VPN-Container Setup (~1-2h)
1. [ ] VPN-Container zu docker-compose.yml hinzufügen
2. [ ] Environment Variables konfigurieren (Token, Server)
3. [ ] Scraping-Service `network_mode: service:vpn` setzen
4. [ ] Health-Check für VPN-Container einrichten
5. [ ] Testen: IP-Check durch Scraping-Service

### Phase 2: Automatische Rotation (optional, ~1h)
1. [ ] Cron/Script für periodischen Server-Wechsel
2. [ ] Monitoring der aktuellen VPN-IP
3. [ ] Alerting bei VPN-Disconnect

### Phase 3: Fallback auf SOCKS5 (optional, ~30min)
1. [ ] SOCKS5-Server als Backup konfigurieren
2. [ ] Automatischer Fallback wenn VPN down

---

## 6. Offene Fragen

1. **Server-Rotation:** Wie oft soll der VPN-Server gewechselt werden?
   - Alle 30 Min = 48 IPs/Tag
   - Alle 60 Min = 24 IPs/Tag
   - Nur bei Ban = weniger Overhead

2. **Server-Auswahl:** Welche Länder priorisieren?
   - Deutschland (für deutsche News)
   - USA (für internationale News)
   - Niederlande (neutral, schnell)

3. **Monitoring:** Brauchen wir Alerts wenn VPN disconnected?

---

## 7. Testbefehle

### SOCKS5 Proxy testen
```bash
# Funktioniert:
curl --socks5-hostname us.socks.nordhold.net:1080 \
     --proxy-user "USER:PASS" \
     https://ifconfig.me

# Alle Server testen:
for server in us.socks.nordhold.net se.socks.nordhold.net stockholm.se.socks.nordhold.net; do
    echo -n "$server: "
    curl -s --socks5-hostname "$server:1080" \
         --proxy-user "USER:PASS" \
         https://ifconfig.me --max-time 5
    echo ""
done
```

### VPN-Container IP prüfen
```bash
# Wenn VPN-Container läuft:
docker exec news-scraping-service curl -s https://ifconfig.me
```

### Port-Erreichbarkeit prüfen
```bash
nc -zv de1184.nordvpn.com 443 -w 5   # OpenVPN TCP
nc -zv us.socks.nordhold.net 1080 -w 5  # SOCKS5
```

---

## 8. Referenzen

- [NordVPN SOCKS5 Support](https://support.nordvpn.com/hc/en-us/sections/24555410533905-SOCKS5-Proxy)
- [NordVPN Docker (bubuntux)](https://github.com/bubuntux/nordvpn)
- [Scraping-Service Proxy-Code](../services/scraping-service/app/services/proxy_manager.py)

---

**Nächster Schritt:** Entscheidung ob/wann Implementierung erfolgen soll.
