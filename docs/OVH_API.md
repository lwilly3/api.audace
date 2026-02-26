# OVH API — Documentation module

Module de consultation des services OVH en lecture seule.
Appels API en temps reel via le SDK Python OVH (pas de cache, pas de stockage BDD).

## Architecture

```
app/config/config.py         # Variables OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY
app/services/ovh_client.py   # Client OVH : get_ovh_client(), _ovh_call(), fonctions metier, gestion d'erreurs
app/schemas/schema_ovh.py    # Schemas Pydantic de reponse
routeur/ovh_route.py         # Endpoints FastAPI sous /ovh/*
```

## Configuration requise

Variables dans `.env` (et `docker-compose.yml`) :
```
OVH_ENDPOINT=ovh-eu
OVH_APPLICATION_KEY=votre_application_key
OVH_APPLICATION_SECRET=votre_application_secret
OVH_CONSUMER_KEY=votre_consumer_key
```

### Generer les credentials

1. Creer l'application : https://eu.api.ovh.com/createApp/
2. Generer un consumer_key en lecture seule :
```python
import ovh
client = ovh.Client(endpoint='ovh-eu', application_key='...', application_secret='...')
ck = client.new_consumer_key_request()
ck.add_rules(ovh.API_READ_ONLY, '/*')
validation = ck.request()
print(validation['consumerKey'], validation['validationUrl'])
```
3. Ouvrir `validationUrl` dans le navigateur et autoriser l'acces.

### Dependance

```
ovh>=1.1.0
```

## Endpoints

### Services

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/services` | `ovh_view_services` | Tous les services avec statut, echeances, displayName. Itere sur tous les types du `SERVICE_TYPE_MAP`. |
| GET | `/ovh/services/types` | `ovh_access_section` | Liste des types de services supportes |
| GET | `/ovh/services/{type}?status=ok` | `ovh_view_services` | Services d'un type avec details (serviceInfos, displayName). Filtre optionnel par statut : `ok`, `expired`, `suspended`, `unPaid`. |
| GET | `/ovh/services/{type}/{name}` | `ovh_view_services` | Detail complet d'un service (appel direct a l'API OVH `/{type}/{name}`) |
| GET | `/ovh/services/{type}/{name}/status` | `ovh_view_services` | serviceInfos : statut, expiration, renouvellement, contacts |

### Dashboard

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/services/dashboard?days=30` | `ovh_view_dashboard` | Tableau de bord : total, par type, expirants, expires, solde, dettes, taches actives |

### Compte

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/account` | `ovh_view_account` | Infos du compte OVH (nichandle, email, organisation) |
| GET | `/ovh/account/balance` | `ovh_view_billing` | Solde, dettes, methodes de paiement |

### Facturation

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/billing/bills?count=20` | `ovh_view_billing` | Dernieres factures triees par date decroissante |
| GET | `/ovh/billing/bills/{bill_id}` | `ovh_view_billing` | Detail d'une facture |

### Email Pro

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/email-pro/{service_name}/accounts` | `ovh_view_services` | Comptes Email Pro avec expiration, quota, usage |

### Monitoring VPS

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/vps/{vps_name}/monitoring?period=lastday` | `ovh_view_services` | CPU, RAM, reseau. Periodes : `lastday`, `lastweek`, `lastmonth`, `lastyear` |

### Taches

| Methode | Endpoint | Permission | Description |
|---------|----------|-----------|-------------|
| GET | `/ovh/tasks` | `ovh_view_services` | Taches actives et recentes sur VPS et serveurs dedies |

## Types de services (SERVICE_TYPE_MAP)

Le parametre `{type}` dans les endpoints correspond aux cles suivantes :

| Cle | Endpoint OVH | Description |
|-----|-------------|-------------|
| `dedicated` | `/dedicated/server` | Serveurs dedies |
| `vps` | `/vps` | Serveurs prives virtuels |
| `domain` | `/domain` | Noms de domaine |
| `hosting` | `/hosting/web` | Hebergements web |
| `cloud` | `/cloud/project` | Projets cloud |
| `ip` | `/ip` | Blocs IP |
| `alldom` | `/allDom` | Packs domaines |
| `email_pro` | `/email/pro` | Email Pro |
| `email_exchange` | `/email/exchange` | Exchange |
| `email_mxplan` | `/email/mxplan` | MXPlan |
| `email_domain` | `/email/domain` | Email domaine |

## Fonctions client (ovh_client.py)

### Fonctions de base

| Fonction | API OVH | Description |
|----------|---------|-------------|
| `get_ovh_client()` | — | Instancie le client SDK OVH avec les credentials |
| `_ovh_call(client, method, path, **kwargs)` | — | Wrapper GET avec gestion d'erreurs (convertit exceptions OVH en HTTPException) |

### Fonctions metier

| Fonction | API OVH | Description |
|----------|---------|-------------|
| `get_account_info()` | `GET /me` | Infos du compte |
| `get_all_services()` | `GET /{type}` + `GET /{type}/{name}/serviceInfos` | Itere sur tous les types, recupere serviceInfos et displayName pour chaque service. Pour Email Pro, ajoute les comptes individuels. Pour Email Domain, filtre ceux sans comptes. |
| `get_services_by_type(type, status_filter)` | `GET /{type}` + `GET /{type}/{name}/serviceInfos` | Services d'un type avec details. Filtre optionnel par statut. |
| `get_service_detail(type, name)` | `GET /{type}/{name}` | Detail brut d'un service |
| `get_service_info(type, name)` | `GET /{type}/{name}/serviceInfos` | Infos d'echeance et renouvellement |
| `get_email_pro_accounts(service_name)` | `GET /email/pro/{name}/account` + detail par compte | Comptes Email Pro tries par expiration |
| `get_bills(count)` | `GET /me/bill` + detail par facture | Factures triees par date decroissante |
| `get_bill_detail(bill_id)` | `GET /me/bill/{id}` | Detail d'une facture |
| `get_account_balance()` | `GET /me/balance`, `/me/debtAccount`, `/me/payment/method` | Solde, dettes, methodes de paiement |
| `get_vps_monitoring(vps_name, period)` | `GET /vps/{name}/monitoring` | CPU, RAM, reseau, IPs, modele VPS |
| `get_active_tasks()` | `GET /vps/{name}/tasks` + `GET /dedicated/server/{name}/task` | Taches actives sur tous les VPS et serveurs |
| `get_services_dashboard(days)` | agrege `get_all_services()` + `get_account_balance()` + `get_active_tasks()` | Dashboard synthetique complet |

## Schemas Pydantic (schema_ovh.py)

| Schema | Champs principaux |
|--------|-------------------|
| `OvhAccountInfo` | nichandle, firstname, name, email, country, organisation, phone, currency |
| `OvhRenewInfo` | automatic, deleteAtExpiration, forced, manualPayment, period |
| `OvhServiceInfo` | serviceId, status, creation, expiration, renew, contacts, domain, canDeleteAtExpiration |
| `OvhServiceSummary` | serviceId, resource, route, status, expiration, creation, renew, contacts |
| `OvhBill` | billId, date, orderId, pdfUrl, priceWithTax, priceWithoutTax, tax, url |
| `OvhExpiringService` | serviceId, resource, status, expiration, days_remaining |
| `OvhEmailProAccount` | email, displayName, firstName, lastName, domain, state, expirationDate, renewPeriod, quota, currentUsage, spamDetected |
| `OvhDashboard` | total_services, services_by_type, expiring_soon, expired, active_count, suspended_count |

## Permissions RBAC

6 permissions dediees. Toutes les routes verifient `ovh_access_section` en prerequis :

| Permission | Usage |
|---|---|
| `ovh_access_section` | Prerequis pour acceder au module OVH |
| `ovh_view_services` | Consulter les services, monitoring, taches |
| `ovh_view_dashboard` | Voir le dashboard synthetique |
| `ovh_view_billing` | Consulter les factures, solde, paiement |
| `ovh_view_account` | Voir les infos du compte OVH |
| `ovh_manage` | Reserve pour futures evolutions (ecriture) |

Pattern de verification (double check) :
```python
def _check_ovh_permission(db, user_id, permission_name):
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
    if not perms or not perms.ovh_access_section:
        raise HTTPException(403, "Permission 'ovh_access_section' requise")
    if not getattr(perms, permission_name, False):
        raise HTTPException(403, f"Permission '{permission_name}' requise")
```

## Gestion d'erreurs

Le wrapper `_ovh_call()` convertit les exceptions du SDK OVH en HTTPException :

| Exception OVH | Code HTTP | Signification |
|---|---|---|
| Credentials absents dans `.env` | 503 | API non configuree |
| `NotCredential` | 502 | Credentials invalides |
| `NotGrantedCall` | 502 | Droits insuffisants sur le consumer_key |
| `ResourceNotFoundError` | 404 | Ressource OVH introuvable |
| `BadParametersError` | 400 | Parametres invalides |
| `APIError` (generique) | 502 | Erreur API OVH |

## Donnees disponibles par type de service

| Type | Expiration | Statut | Renouvellement | Facturation |
|------|-----------|--------|----------------|-------------|
| Serveurs dedies | Oui (serviceInfos) | Oui | Oui | Oui (/me/bill) |
| VPS | Oui | Oui | Oui | Oui |
| Domaines | Oui | Oui (ok/expired) | Oui | Oui |
| Hebergements web | Oui | Oui | Oui | Oui |
| Email Pro | Oui (par compte) | Oui | Oui | Oui |
| Email Domain | Oui | Oui | Oui | Oui |
| Projets cloud | Oui | Oui | Oui | Oui |

## Ajout d'un nouveau type de service

1. Ajouter l'entree dans `SERVICE_TYPE_MAP` (`ovh_client.py`)
2. Le type sera automatiquement pris en charge par `get_all_services()`, `get_services_by_type()`, `get_service_detail()`, `get_service_info()`
3. Si le type necessite un traitement special (comme Email Pro avec ses sous-comptes), ajouter la logique dans `get_all_services()`

## Ajout d'un nouvel endpoint

1. Ajouter la fonction metier dans `ovh_client.py`
2. Ajouter le schema Pydantic dans `schema_ovh.py` si necessaire
3. Ajouter la route dans `routeur/ovh_route.py` avec `_check_ovh_permission()`
4. Logger l'action avec `log_action(db, user_id, "read", "ovh_xxx", 0)`
