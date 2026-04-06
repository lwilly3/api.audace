# Module Logistique — Guide Complet

**Version**: 0.16.0  
**Statut**: Implémentation Backend complète  
**Couleur**: Purple `#7C3AED`  
**Base URL**: `/api/logistics` ou `/logistics`

---

## 1. Vue d'ensemble

Le module **Logistique** gère la flotte de véhicules, les équipes de chauffeurs, les missions de transport, la consommation de carburant, la maintenance préventive, les pneus, et les documents administratifs pour les trois entreprises : **BAJ (transport pétrolier)**, **Trafric (logistique générale)**, et **AMG (média)**.

### Cas d'usage principaux
- **BAJ**: Citernes pour carburant, capteurs de consommation
- **Trafric**: Grumiers (bois), plateaux (conteneurs), bennes (matériaux)
- **AMG**: Plateaux (équipements média)

---

## 2. Architecture des données

### 2.1 Segmentation par entités

L'architecture logistique couvre **11 tables** avec relations multi-niveaux :

```
VÉHICULES (LogisticsVehicle)
├─ MISSIONS (LogisticsMission)
│  └─ CHECKPOINTS (LogisticsMissionCheckpoint)
├─ FUEL (LogisticsFuelLog)
├─ MAINTENANCE (LogisticsMaintenance)
├─ TIRES (LogisticsTire)
└─ DOCUMENTS (LogisticsDocument)

CONDUCTEURS (LogisticsDriver)
├─ ÉQUIPES (LogisticsTeam)
│  └─ Membres (array de driver_ids)
└─ Missions assignées

PARAMÉTRAGE
├─ OPTIONS CONFIG (LogisticsConfigOption)
│  ├─ Segments véhicules
│  ├─ Statuts véhicules/conducteurs/missions
│  ├─ Types de cargo
│  ├─ Types de maintenance
│  └─ Types de documents
└─ PARAMÈTRES GLOBAUX (LogisticsGlobalSettings)
   ├─ Préfixes références
   ├─ Seuils d'alertes
   └─ Compteurs
```

### 2.2 Récapitulatif des entités

| Entité | Table SQL | Colonnes clés | Relations |
|--------|-----------|---------------|-----------|
| **Véhicule** | `logistics_vehicle` | registration_number, segment, capacity, mileage, status | 1→N missions, fuel, maintenance, tires, documents |
| **Conducteur** | `logistics_driver` | first_name, last_name, role, license_types, status, team_id | 1→N missions, 0..1 team |
| **Équipe** | `logistics_team` | name, leader_id, vehicle_id_assigned, status, segment_preference | N chauffeurs (driver_id FK) |
| **Mission** | `logistics_mission` | vehicle_id, team_id, status, origin, destination, cargo_type | 1 véhicule, 1 équipe, N checkpoints |
| **Checkpoint** | `logistics_mission_checkpoint` | mission_id, type, location, arrival_time, departure_time | 1 mission |
| **Carburant** | `logistics_fuel_log` | vehicle_id, liters, cost, km, consumption_l_per_100km | Alerte surconsommation |
| **Maintenance** | `logistics_maintenance` | vehicle_id, type, description, cost, labor_hours, status | Historique entretien |
| **Pneus** | `logistics_tire` | vehicle_id, position, installed_km, current_km, max_km | Wear % detection |
| **Documents** | `logistics_document` | entity_type, entity_id, doc_type, expiry_date, file_url | Polymorphe (vehicle\|driver\|mission) |
| **Config Option** | `logistics_config_option` | list_type, name, label, description | Listes déroulantes |
| **Paramètres Globaux** | `logistics_global_settings` | reference_prefix_vehicle, fuel_alert_threshold, ... | Singleton de config |

### 2.3 Exemple : Mission avec cargo segment-spécifique

```python
# GRUMIER (bois)
mission_grumier = LogisticsMission(
    vehicle_id=1,
    team_id=1,
    cargo_type="wood",
    wood_species="Teak",  # Spécifique à grumier
    product_name=None,
    container_count=None,
    origin="Forêt Nord",
    destination="Scierie Sud",
    status="in_progress"
)

# CITERNE (carburant)
mission_citerne = LogisticsMission(
    vehicle_id=2,
    team_id=2,
    cargo_type="fuel",
    wood_species=None,
    product_name="Diesel Premium",  # Spécifique à citerne
    container_count=None,
    origin="Dépôt pétrolier",
    destination="Station service",
    status="planned"
)

# PLATEAU (conteneurs)
mission_plateau = LogisticsMission(
    vehicle_id=3,
    team_id=3,
    cargo_type="containers",
    wood_species=None,
    product_name=None,
    container_count=5,  # Spécifique à plateau
    origin="Port",
    destination="Entrepôt",
    status="completed"
)
```

---

## 3. API REST — Routes et Endpoints

### 3.1 Véhicules

```http
# PRÉVISUALISATION / GÉNÉRATION DE RÉFÉRENCES
GET    /logistics/vehicles/reference/peek          → { "next_reference": "LOG-0001" }
GET    /logistics/vehicles/reference/next          → { "next_reference": "LOG-0001" } (incrémente)

# CRUD VÉHICULES
POST   /logistics/vehicles                         → VehicleResponse
GET    /logistics/vehicles                         → VehicleListResponse (avec pagination)
GET    /logistics/vehicles/{vehicle_id}           → VehicleResponse
PUT    /logistics/vehicles/{vehicle_id}           → VehicleResponse
POST   /logistics/vehicles/{vehicle_id}/archive   → VehicleResponse (soft-archive)
DELETE /logistics/vehicles/{vehicle_id}           → { "message": "..." } (soft-delete)
```

**Exemple de requête `POST /logistics/vehicles`** :
```json
{
  "company_id": 1,
  "registration_number": "AM-5234-BJ",
  "internal_reference": "LOG-0001",
  "segment": "grumier",
  "model": "HOWO A7",
  "year": 2020,
  "capacity_tons": 18,
  "fuel_type": "diesel",
  "current_mileage": 45000,
  "acquisition_date": "2020-03-15",
  "status": "active"
}
```

**Filtres possibles** :
- `company_id` : Filtrer par entreprise
- `search` : Chercher par registration_number ou model
- `segment` : Filtrer par type (grumier, citerne, etc.)
- `status` : Filtrer par statut (active, maintenance, etc.)
- `is_archived` : Afficher les archives (défaut: false)
- `skip`, `limit` : Pagination

### 3.2 Conducteurs

```http
# CRUD CONDUCTEURS
POST   /logistics/drivers                         → DriverResponse
GET    /logistics/drivers                         → DriverListResponse
GET    /logistics/drivers/{driver_id}            → DriverResponse
PUT    /logistics/drivers/{driver_id}            → DriverResponse
DELETE /logistics/drivers/{driver_id}            → { "message": "..." }
```

**Exemple de requête `POST /logistics/drivers`** :
```json
{
  "company_id": 1,
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@example.com",
  "phone": "+242123456789",
  "role": "driver",
  "license_number": "BJ-123456789",
  "license_expiry": "2025-12-31",
  "license_types": ["HE", "HC", "HD"],
  "status": "active",
  "team_id": null
}
```

**Filtres** :
- `company_id` : Par entreprise
- `role` : driver ou motor_boy
- `status` : active, on_leave, etc.
- `search` : Par nom ou email

### 3.3 Équipes

```http
# CRUD ÉQUIPES
POST   /logistics/teams                           → TeamResponse
GET    /logistics/teams                           → TeamListResponse
GET    /logistics/teams/{team_id}                 → TeamDetailResponse (incl. membres)
PUT    /logistics/teams/{team_id}                 → TeamResponse
DELETE /logistics/teams/{team_id}                 → { "message": "..." }
```

**Exemple de requête `POST /logistics/teams`** :
```json
{
  "company_id": 1,
  "name": "Équipe Grumier Nord",
  "leader_id": 5,
  "member_ids": [5, 6, 7],
  "vehicle_id_assigned": null,
  "segment_preference": "grumier",
  "status": "active"
}
```

**Réponse `GET /logistics/teams/{team_id}` (TeamDetailResponse)** :
```json
{
  "id": 1,
  "company_id": 1,
  "name": "Équipe Grumier Nord",
  "leader_id": 5,
  "member_ids": [5, 6, 7],
  "members": [
    { "id": 5, "first_name": "Jean", "last_name": "Dupont", "role": "driver", "status": "active" },
    { "id": 6, "first_name": "Paul", "last_name": "Martin", "role": "motor_boy", "status": "active" },
    { "id": 7, "first_name": "Marc", "last_name": "Bernard", "role": "motor_boy", "status": "active" }
  ],
  "vehicle_id_assigned": null,
  "segment_preference": "grumier",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### 3.4 Dashboard

```http
GET    /logistics/dashboard                       → LogisticsDashboardResponse
```

**Réponse** :
```json
{
  "stats": {
    "total_vehicles": 12,
    "vehicles_active": 10,
    "vehicles_in_maintenance": 2,
    "total_drivers": 25,
    "total_teams": 10,
    "missions_in_progress": 3,
    "alerts_count": 5
  },
  "alerts": [
    { "type": "document_expiry", "entity_id": 1, "entity_type": "vehicle", "message": "Assurance expire dans 7 jours" },
    { "type": "maintenance_due", "entity_id": 2, "entity_type": "vehicle", "message": "Maintenance prévue demain" },
    ...
  ]
}
```

---

## 4. Permissions (granulaires)

Le module logistique utilise **50+ permissions** stockées en booléens dans la table `user_permissions` :

### Catégories de permissions

| Catégorie | Permission | Description |
|-----------|-----------|-------------|
| **Accès module** | `logistics_view` | Accès basique au module |
| | `logistics_view_all_companies` | Voir tous les véhicules/conducteurs (bypass company_id) |
| **Véhicules** | `logistics_vehicles_view` | Voir la liste des véhicules |
| | `logistics_vehicles_create` | Créer un véhicule |
| | `logistics_vehicles_edit` | Modifier / archiver un véhicule |
| | `logistics_vehicles_delete` | Supprimer définitivement un véhicule |
| **Conducteurs** | `logistics_drivers_view` | Voir la liste des conducteurs |
| | `logistics_drivers_create` | Créer un conducteur |
| | `logistics_drivers_edit` | Modifier un conducteur |
| | `logistics_drivers_delete` | Supprimer un conducteur |
| **Équipes** | `logistics_teams_view` | Voir la liste des équipes |
| | `logistics_teams_create` | Créer une équipe |
| | `logistics_teams_edit` | Modifier une équipe |
| | `logistics_teams_delete` | Supprimer une équipe |
| **Missions** | `logistics_missions_view` | Voir les missions |
| | `logistics_missions_create` | Créer une mission |
| | `logistics_missions_edit` | Modifier une mission |
| ... | ... (carburant, maintenance, pneus, documents, financier, rapports) | ... |

### Exemple d'utilisation en code

```python
# Dans une route FastAPI
@router.get("/logistics/vehicles")
def list_vehicles(current_user: User = Depends(oauth2.get_current_user)):
    if not current_user.permissions.logistics_vehicles_view:
        raise HTTPException(status_code=403, detail="Permission denied")
    # ...
```

---

## 5. Intégration multi-entreprises

Chaque enregistrement est scopé par `company_id`. Les utilisateurs ne peuvent voir que les données de leur entreprise sauf s'ils ont la permission `logistics_view_all_companies` (super_admin).

```python
# Dans les routes :
if not current_user.permissions.logistics_view_all_companies:
    if hasattr(current_user, 'company_id'):
        company_id = current_user.company_id  # Force le filtre
```

### Entreprises supportées

- **BAJ** (ID: 1) — Transport pétrolier
- **Trafric** (ID: 2) — Logistique générale
- **AMG** (ID: 3) — Média

---

## 6. Évènements et notifications

Le module peut émettre des événements via `eventBus` pour notifier d'autres modules :

```python
from shared.core.eventBus import eventBus

eventBus.emit('logistics:vehicle:archived', {
    'vehicle_id': vehicle_id,
    'company_id': company_id,
    'timestamp': datetime.utcnow()
})
```

### Événements disponibles (prévus pour v1.0)

- `logistics:vehicle:created`
- `logistics:vehicle:updated`
- `logistics:vehicle:archived`
- `logistics:mission:completed`
- `logistics:fuel:alert_threshold_exceeded`
- `logistics:maintenance:due`
- `logistics:document:expiring_soon`

---

## 7. Configuration et déploiement

### 7.1 Variables d'environnement

```bash
# Dans .env
LOGISTICS_FUEL_ALERT_L_PER_100KM=8.0
LOGISTICS_MAINTENANCE_ALERT_DAYS=30
LOGISTICS_DOCUMENT_EXPIRY_ALERT_DAYS=30
LOGISTICS_TIRE_WEAR_PERCENT_ALERT=20
```

### 7.2 Migrants Alembic

Les tables logistique sont créées via migration auto-générée :

```bash
# Sur le serveur Docker
docker exec -it audace_api alembic revision --autogenerate -m "Add logistics module tables"
docker exec -it audace_api alembic upgrade head
```

### 7.3 Initialisation au démarrage

La fonction `initialize_logistics_config()` est appelée dans le lifespan du maintest.py et :
- Crée les options de configuration (segments, statuts, etc.)
- Initialise les paramètres globaux
- Est **idempotente** (safe de réexécuter)

---

## 8. Types de données Pydantic

Voir `app/schemas/schema_logistics.py` pour les modèles complets.

### Modèles de requête (Create/Update)

- `VehicleCreate` — Créer un véhicule
- `VehicleUpdate` — Modifier un véhicule (tous champs optionnels)
- `DriverCreate` — Créer un conducteur
- `DriverUpdate` — Modifier un conducteur
- `TeamCreate` — Créer une équipe
- `TeamUpdate` — Modifier une équipe

### Modèles de réponse

- `VehicleResponse` — Véhicule (détail complet)
- `VehicleListResponse` — Liste paginée de véhicules
- `DriverResponse` — Conducteur (détail complet)
- `DriverListResponse` — Liste paginée de conducteurs
- `TeamDetailResponse` — Équipe avec membres embedés
- `LogisticsDashboardResponse` — Statistiques +  alertes
- `NextReferenceResponse` — Prochaine référence générée

---

## 9. Exemple d'utilisation côté frontend (React)

```typescript
import axios from 'axios';

// Créer un véhicule
async function createVehicle(vehicleData: VehicleCreate) {
  const response = await axios.post('/api/logistics/vehicles', vehicleData);
  return response.data as VehicleResponse;
}

// Lister les véhicules avec filtre
async function listVehicles(filters: { segment?: string; status?: string }) {
  const response = await axios.get('/api/logistics/vehicles', { params: filters });
  return response.data as VehicleListResponse;
}

// Obtenir le dashboard
async function getDashboard() {
  const response = await axios.get('/api/logistics/dashboard');
  return response.data as LogisticsDashboardResponse;
}
```

---

## 10. Flux de travail typique

### Cas: Créer une mission et suivre son exécution

1. **Préparer l'équipe** → Créer une équipe avec conducteurs
2. **Assigner véhicule** → Lier équipe à un véhicule
3. **Créer la mission** → Définir origin, destination, cargo_type
4. **Ajouter checkpoints** → Chargement, déchargement, arrêts
5. **Mettre à jour status** → planned → in_progress → completed
6. **Enregistrer carburant** → LogisticsFuelLog
7. **Enregistrer maintenance** → Si besoin
8. **Générer rapport** → Via dashboard ou export

---

## 11. Roadmap v1.0+

- [ ] **Missions avancées**
  - [ ] Planification d'itinéraires (intégration Google Maps)
  - [ ] Real-time GPS tracking des véhicules
  - [ ] Notifications push pour les checkpoints
  
- [ ] **Rapports et Analytics**
  - [ ] Export Excel missions / carburant / maintenance
  - [ ] KPIs : consommation moyenne, temps moyen par trajet, rentabilité
  - [ ] Comparaison par conducteur / équipe / véhicule
  
- [ ] **Maintenance prédictive**
  - [ ] Alertes basées sur l'état général (mileage, age)
  - [ ] Intégration historique maintenance pour prédiction
  
- [ ] **Intégration OBD**
  - [ ] Lecture capteurs véhicules (consommation real-time, température moteur)
  - [ ] Alertes instantanées surconsommation

---

## 12. Support et FAQ

**Q: Comment copier la configuration d'une entreprise à une autre?**  
A: Les options de configuration sont globales (pas de company_id). Tous les véhicules/conducteurs partagent la même liste de segments, statuts, etc.

**Q: Peut-on modifier les segments/statuts pour une seule entreprise?**  
A: Non, ce sont des listes globales. Solution: ajouter un champ `company_id` à `LogisticsConfigOption` (future amélioration).

**Q: Comment gérer les pneus (changement, usure)?**  
A: Voir table `LogisticsTire` : colonne `current_km` + `max_km` = wear %. Chaque changement crée un enregistrement avec `installed_km` réinitialisé.

---

**Auteur**: Audace API Team  
**Dernière mise à jour**: 2024-01-20  
**Licence**: Propriétaire
