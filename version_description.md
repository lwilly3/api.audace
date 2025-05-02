# Version 1.1.0

Date : 2 mai 2025

## Nouvelles fonctionnalités

- Ajout des routes DELETE `/shows/all` et `/shows/allofuser/{user_id}` pour la suppression en masse des shows.

## Corrections et améliorations

- Gestion des suppressions en cascade dans `crud_show.py` pour éviter les violations de clés étrangères :
  - Suppression des entrées `ShowPresenter`, `SegmentGuest` et `Segment` avant suppression des `Show`.
- Mise à jour des routes dans `show_route.py` pour intégrer ces suppressions.
- Documentation mise à jour :
  - `frontend_routes_documentation.md` et `description_prompt.md` reflètent ces nouveaux endpoints.

---

*Cette description de version est publiée en parallèle du document principal de fonctionnalités.*