# Optimisation et Amélioration de la Route Dashboard

Ce document décrit les améliorations possibles pour l’endpoint `/dashbord/` (méthode `GET /dashbord/`) et détaille les étapes de mise en œuvre pour chaque suggestion.

## 1. Objectifs
- Améliorer les performances et la scalabilité
- Rendre l’API plus flexible (filtrage temporel, pagination)
- Centraliser la logique métier pour faciliter la maintenance et les tests
- Sécuriser et documenter clairement la réponse

---

## 2. Schéma de réponse recommandé
```python
class DashboardStats(BaseModel):
    emissions_du_jour: int
    en_direct_et_a_venir: int
    emissions_planifiees: int
    membres_equipe: int
    heures_direct: int
    programme_du_jour: List[ShowDetail]

class ShowDetail(BaseModel):
    id: int
    emission_id: int
    title: str
    broadcast_date: datetime
    status: str
    animateur: str
    segments: List[SegmentDetail]

class SegmentDetail(BaseModel):
    id: int
    title: str
    duration: int
    guests: List[GuestDetail]

class GuestDetail(BaseModel):
    id: int
    name: str
```

---

## 3. Étapes d’implémentation

1. **Séparer la logique métier**
   - Créer un service `dashboard_service.py` dans `app/services/`.
   - Implémenter une fonction `compute_dashboard(db: Session, from_date: date, to_date: date) -> DashboardStats`.

2. **Optimiser les requêtes SQL**
   - Utiliser `func.count()`, `func.sum()` et `func.date()` pour calculs en base.
   - Ajouter des `Index` sur `Show.broadcast_date`, `Show.status` et `User.is_active`.

3. **Supporter les filtres temporels**
   - Dans `dashbord_route.py`, ajouter deux query params facultatifs : `from_date` et `to_date`.
   - Parser ces dates (`datetime.fromisoformat`) et transmettre au service.

4. **Mise en cache**
   - Installer et configurer Redis (ex. `aioredis`).
   - Avant d’appeler le service : vérifier si la clé `dashboard:YYYY-MM-DD` existe.
   - Si non, calculer, stocker dans Redis avec TTL (ex. 60s).

5. **Documentation OpenAPI**
   - Ajouter le `response_model=DashboardStats` et un `summary`/`description` clair.
   - Fournir un exemple de réponse JSON dans la documentation (`examples` parameter).

6. **Tests unitaires**
   - Créer `tests/test_dashboard_filters.py` pour couvrir :
     - Appel sans filtre (calcul par défaut pour la journée)
     - Appel avec intervalle personnalisé
     - Mise en cache (simuler Redis)

7. **Monitoring et alerting**
   - Mesurer la latence via `prometheus_client` (Middlewares FastAPI).
   - Configurer des alertes si le temps de calcul > seuil (ex. 200 ms).

---

## 4. Exemple de route mise à jour
```python
@router.get(
    "/",
    response_model=DashboardStats,
    summary="Statistiques globales et programme du jour",
)
def get_dashboard_route(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(oauth2.get_current_user),
):
    cache_key = f"dashboard:{from_date or date.today()}:{to_date or date.today()}"
    if cache.exists(cache_key):
        return cache.get(cache_key)

    stats = compute_dashboard(db, from_date, to_date)
    cache.set(cache_key, stats.json(), ex=60)
    return stats
```

---

## 5. Bénéfices attendus
- Réduction de la charge serveur (cache + agrégats côté base)
- Flexibilité accrue grâce aux filtres
- Code plus clair, testé et maintenable
- Surveillance proactive des performances
