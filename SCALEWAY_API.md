# Scaleway Dedibox API — Documentation module

Module de consultation des services Scaleway Dedibox (Online.net) en lecture seule.
Appels API REST en temps reel via httpx (pas de cache, pas de stockage BDD).

## Architecture

```
app/config/config.py              # Variable SCW_SECRET_KEY
app/services/scaleway_client.py   # Client Dedibox : _dedibox_get(), fonctions metier, gestion d'erreurs
app/schemas/schema_scaleway.py    # Schemas Pydantic de reponse
routeur/scaleway_route.py         # Endpoints FastAPI sous /scaleway/*
```

## Configuration requise

Variable dans `.env` (et `docker-compose.yml`) :
```
SCW_SECRET_KEY=votre_token_prive_dedibox
```

### Obtenir le token

1. Se connecter sur https://console.online.net/en/api/access
2. Generer un token prive (Bearer token)
3. Copier le token dans `SCW_SECRET_KEY`

### Dependance

```
httpx
```

## API externe

- **Base URL** : `https://api.online.net/api/v1`
- **Authentification** : `Authorization: Bearer {SCW_SECRET_KEY}`
- **Methode** : GET uniquement (lecture seule)
- **Timeout** : 30 secondes
- **Redirections** : `follow_redirects=True` (gere les 301 type `/domain` -> `/domain/`)

## Endpoints

### Compte

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/scaleway/account` | `scw_view_account` | Infos utilisateur (id, login, email, nom, societe) |

### Serveurs dedies

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/scaleway/servers` | `scw_view_instances` | Liste des serveurs avec enrichissement automatique (hostname, offer, IPs) |
| GET | `/scaleway/servers/{server_id}` | `scw_view_instances` | Detail complet d'un serveur |
| GET | `/scaleway/servers/{server_id}/status` | `scw_view_instances` | Statut hardware (disques, reseau) |

### Hebergements web

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/scaleway/hosting` | `scw_view_billing` | Liste des hebergements avec enrichissement |
| GET | `/scaleway/hosting/{hosting_id}` | `scw_view_billing` | Detail d'un hebergement |

### Domaines

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/scaleway/domains` | `scw_view_domains` | Liste des domaines avec enrichissement (details via `/domain/{id}`) |
| GET | `/scaleway/domains/{domain_id}` | `scw_view_domains` | Detail d'un domaine |

### Reseau

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/scaleway/failover` | `scw_view_instances` | IPs failover |

### Dashboard

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/scaleway/dashboard` | `scw_view_dashboard` | Tableau de bord synthetique (serveurs, hebergements, domaines, failover, user) |

## Fonctions client (scaleway_client.py)

### Fonctions de base

| Fonction | Description |
|----------|-------------|
| `_get_headers()` | Retourne les headers Bearer. Leve 503 si `SCW_SECRET_KEY` absent. |
| `_dedibox_get(path, params)` | Appel GET avec httpx, `follow_redirects=True`, gestion d'erreurs complete. |

### Fonctions metier

| Fonction | API Dedibox | Description |
|----------|-------------|-------------|
| `get_user_info()` | `GET /user` | Infos du compte |
| `get_servers()` | `GET /server` + `GET /server/{id}` | Liste enrichie : si les champs essentiels (hostname, offer) sont absents, appel au detail. |
| `get_server_detail(id)` | `GET /server/{id}` | Detail complet d'un serveur |
| `get_server_status(id)` | `GET /server/{id}/status` | Statut hardware |
| `get_hostings()` | `GET /hosting` + `GET /hosting/{id}` | Liste enrichie : si hostname/fqdn absents, appel au detail. |
| `get_hosting_detail(id)` | `GET /hosting/{id}` | Detail d'un hebergement |
| `get_domains()` | `GET /domain` + `GET /domain/{id}` | Liste enrichie : toujours appel au detail pour chaque domaine (nom, dates). |
| `get_domain_detail(id)` | `GET /domain/{id}` | Detail d'un domaine |
| `get_failover_ips()` | `GET /server/failover` | IPs failover |
| `get_dashboard()` | agrege toutes les fonctions | Dashboard synthetique |

### Strategie d'enrichissement

L'API Dedibox retourne souvent des objets minimaux (juste l'id ou quelques champs).
Les fonctions `get_servers()`, `get_hostings()`, `get_domains()` enrichissent chaque element :

1. Appel a la liste (`/server`, `/hosting`, `/domain`)
2. Pour chaque element, verification des champs essentiels
3. Si incomplet, appel au detail (`/server/{id}`, etc.)
4. En cas d'erreur sur le detail, conservation de l'element minimal

## Schemas Pydantic (schema_scaleway.py)

Tous les schemas utilisent `extra="allow"` pour accepter les champs supplementaires de l'API.

| Schema | Champs principaux |
|--------|-------------------|
| `DediboxUser` | id, login, email, first_name, last_name, company |
| `DediboxServer` | id, offer, hostname, location, boot_mode, last_reboot, power_status, abuse, os, contacts, disks, network, ip, service_expiration, status |
| `DediboxServerLocation` | datacenter, room, bay, block, position |
| `DediboxServerIp` | address, type, reverse, mac |
| `DediboxHosting` | id, offer, hostname, fqdn, status, platform, disk, contacts |
| `DediboxDomain` | id, name, dns_zone_status, status, contacts, expiration_date, creation_date |
| `DediboxFailoverIp` | address, type, reverse, server_id, destination |
| `DediboxDashboard` | total_servers, servers_by_status, active_count, total_hostings, total_domains, failover_ips_count, user |

## Permissions RBAC

7 permissions dediees. Toutes les routes verifient `scw_access_section` en prerequis :

| Permission | Usage |
|---|---|
| `scw_access_section` | Prerequis pour acceder au module Scaleway |
| `scw_view_instances` | Consulter les serveurs et IPs failover |
| `scw_view_dashboard` | Voir le dashboard synthetique |
| `scw_view_billing` | Consulter les hebergements |
| `scw_view_domains` | Consulter les domaines |
| `scw_view_account` | Voir les infos du compte |
| `scw_manage` | Reserve pour futures evolutions (ecriture) |

Pattern de verification (double check) :
```python
def _check_scw_permission(db, user_id, permission_name):
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.scw_access_section:
        raise HTTPException(403, "Permission 'scw_access_section' requise")
    if not getattr(perms, permission_name, False):
        raise HTTPException(403, f"Permission '{permission_name}' requise")
```

## Gestion d'erreurs

Le wrapper `_dedibox_get()` convertit les codes HTTP en HTTPException :

| Code HTTP Dedibox | Code HTTP retourne | Signification |
|---|---|---|
| `SCW_SECRET_KEY` absent | 503 | API non configuree |
| 401 | 502 | Token invalide |
| 403 | 502 | Acces non autorise |
| 404 | 404 | Ressource introuvable |
| Timeout | 504 | Timeout (30s) |
| Erreur reseau | 502 | Erreur de connexion |
| Autre code | 502 | Erreur API generique |

Logging : chaque erreur est loggee avec `logger.error()` et `print()` (pour docker logs).

## Donnees disponibles par type de ressource

| Ressource | Disponible | Expiration | Statut | Details |
|-----------|-----------|-----------|--------|---------|
| **Serveurs** | Oui | `service_expiration` (dans le detail) | power_status, abuse | hostname, offer, IPs, OS, disques, reseau |
| **Hebergements** | Oui | **Non disponible** (limitation API) | status (active, locked, etc.) | offer, domain_name, php_version, web_server |
| **Domaines** | Oui | **Non disponible** (limitation API) | external (bool) | name, dnssec, zone DNS |
| **IPs failover** | Oui | N/A | N/A | address, type, reverse, server_id |

### Limitations connues de l'API Dedibox

- **Pas de dates d'expiration** pour les hebergements et domaines. L'endpoint `/service` (qui contient `expiration_date`, `subscription_date`, `auto_renew`) retourne **403 Permission denied** avec le token prive.
- **Pas de facturation** : aucun endpoint `/billing`, `/invoice`, `/order` n'existe dans l'API.
- **Pas de scopes granulaires** pour le token prive : pas possible de demander l'acces a `/service`.
- L'OAuth2 disponible ne propose pas de scope pour hosting/service/billing.

### Ce que retourne reellement l'API

**Hosting** (`GET /hosting/{id}`) :
```json
{
  "id": 332247,
  "offer": "PRO Hosting",
  "domain_name": "exemple.com",
  "php_version": "7.3",
  "web_server": "pf41-web.online.net",
  "contacts": {"owner": "login", "tech": "login"},
  "status": "active"
}
```

**Domain** (`GET /domain/{id}`) :
```json
{
  "id": 61970,
  "name": "exemple.com",
  "dnssec": false,
  "external": true,
  "versions": {"$ref": "/api/v1/domain/exemple.com/version"},
  "zone": {"$ref": "/api/v1/domain/exemple.com/zone"}
}
```

## Ajout d'un nouvel endpoint

1. Ajouter la fonction metier dans `scaleway_client.py` (utiliser `_dedibox_get()`)
2. Ajouter le schema Pydantic dans `schema_scaleway.py` avec `extra="allow"`
3. Ajouter la route dans `routeur/scaleway_route.py` avec `_check_scw_permission()`
4. Logger l'action avec `log_action(db, user_id, "read", "scaleway_xxx", 0)`

## Endpoints API Dedibox disponibles (reference)

Endpoints accessibles avec le token actuel :

| Endpoint | Status | Usage |
|----------|--------|-------|
| `/user` | OK | Infos compte |
| `/server` | OK | Liste serveurs (actuellement 0) |
| `/server/{id}` | OK | Detail serveur |
| `/server/{id}/status` | OK | Statut hardware |
| `/server/failover` | OK | IPs failover |
| `/hosting` | OK | Liste hebergements |
| `/hosting/{id}` | OK | Detail hebergement |
| `/domain` | OK | Liste domaines (9 domaines) |
| `/domain/{id}` | OK | Detail domaine |
| `/service` | **403** | Dates d'expiration, abonnements |
| `/subscription` | **403** | Webhooks abonnements |

Endpoints non disponibles dans l'API : `/billing`, `/invoice`, `/order`, `/payment`.
