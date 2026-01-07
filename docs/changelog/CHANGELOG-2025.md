# Changelog 2025

Archive des versions publiées en 2025.

Retour au [CHANGELOG principal](../../CHANGELOG.md)

---

## [1.1.0] - 2025-05-02

### Ajouté
- Routes DELETE `/shows/all` et `/shows/allofuser/{user_id}` pour suppression en masse des shows

### Modifié
- Gestion des suppressions en cascade dans `crud_show.py`
  - Suppression automatique des `ShowPresenter`, `SegmentGuest` et `Segment` avant suppression des `Show`
  - Prévention des violations de clés étrangères
- Routes dans `show_route.py` pour intégrer les suppressions en cascade

### Documentation
- Mise à jour de `frontend_routes_documentation.md`
- Mise à jour de `description_prompt.md`

---

_Archive créée le 07 janvier 2026_
