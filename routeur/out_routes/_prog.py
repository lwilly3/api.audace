



# from fastapi import APIRouter, Query, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import or_
# from typing import List
# import app.models as models
# import app.schemas.schemas_media as schemas_media
# from app.db.database import get_db
# import app.auth.oauth2 as oauth2

# # Création d'un routeur pour gérer les endpoints liés aux programmes
# router = APIRouter(
#     prefix="/programmes",  # Préfixe pour tous les endpoints de ce routeur
#     tags=['PROGRAMMES']  # Catégorie utilisée pour la documentation automatique
# )

# # 1. Endpoint pour obtenir la liste des programmes avec pagination, tri, filtres et recherche
# @router.get("/", response_model=schemas_media.PaginatedResponse)
# def get_programmes(
#     db: Session = Depends(get_db),  # Dépendance pour obtenir une session de base de données
#     theme: str = Query(None, alias="filter_theme"),  # Filtrer les programmes par thème
#     search: str = Query(None, min_length=3),  # Recherche par mot-clé (nom ou description)
#     limit: int = Query(10, ge=1, le=100),  # Pagination : limite des résultats (min 1, max 100)
#     offset: int = Query(0, ge=0),  # Pagination : décalage des résultats (ne peut pas être négatif)
#     sort_by: str = Query("broadcast_date", enum=["name", "broadcast_date"]),  # Tri : par nom ou date
#     presenter_id: int = Query(None),  # Filtrer par ID du présentateur
#     broadcast_date: str = Query(None),  # Filtrer par date de diffusion
#     current_user: int = Depends(oauth2.get_current_user)  # Vérification de l'utilisateur connecté
# ):
#     # Initialisation de la requête de base
#     query = db.query(models.Programme)

#     # Ajout des filtres dynamiques si les paramètres sont fournis
#     filters = {
#         "theme": theme,
#         "presenter_id": presenter_id,
#         "broadcast_date": broadcast_date,
#     }
#     for key, value in filters.items():
#         if value is not None:
#             query = query.filter(getattr(models.Programme, key) == value)

#     # Ajout du filtre de recherche (nom ou description contenant le mot-clé)
#     if search:
#         query = query.filter(
#             or_(
#                 models.Programme.name.ilike(f"%{search}%"),
#                 models.Programme.description.ilike(f"%{search}%")
#             )
#         )

#     # Tri des résultats selon le paramètre `sort_by`
#     if sort_by == "name":
#         query = query.order_by(models.Programme.name)
#     else:
#         query = query.order_by(models.Programme.broadcast_date)

#     # Pagination : comptage total et limitation des résultats
#     total_items = query.count()
#     programmes = query.offset(offset).limit(limit).all()

#     # Si aucun programme n'est trouvé, lever une erreur
#     if not programmes:
#         raise HTTPException(status_code=404, detail="Aucun programme trouvé")

#     # Retour des données paginées
#     return {
#         "total": total_items,
#         "limit": limit,
#         "offset": offset,
#         "data": programmes,
#     }


# # 2. Endpoint pour créer un nouveau programme
# @router.post("/", response_model=schemas_media.ProgrammeResponse)
# def create_programme(
#     programme: schemas_media.ProgrammeCreate,  # Données du programme à créer
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)  # Vérification de l'utilisateur connecté
# ):
#     # Vérification des permissions : seuls les administrateurs peuvent créer des programmes
#     # if current_user.role != "admin":
#     #     raise HTTPException(status_code=403, detail="Action non autorisée")

#     # Création et enregistrement du nouveau programme
#     new_programme = models.Programme(**programme.model_dump())
#     db.add(new_programme)
#     db.commit()
#     db.refresh(new_programme)
#     return new_programme


# # 3. Endpoint pour mettre à jour un programme existant
# @router.put("/update/{programme_id}", response_model=schemas_media.ProgrammeResponse)
# def update_programme(
#     programme_id: int,  # ID du programme à mettre à jour
#     programme: schemas_media.ProgrammeUpdate,  # Données mises à jour
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     # Recherche du programme dans la base de données
#     db_programme = db.query(models.Programme).filter(models.Programme.id == programme_id).first()

#     # Si le programme n'existe pas, lever une erreur
#     if not db_programme:
#         raise HTTPException(status_code=404, detail="Programme non trouvé")

#     # Mise à jour des champs fournis
#     for key, value in programme.model_dump(exclude_unset=True).items():
#         setattr(db_programme, key, value)

#     # Sauvegarde des modifications
#     db.commit()
#     db.refresh(db_programme)
#     return db_programme


# # 4. Endpoint pour supprimer un programme
# @router.delete("/{programme_id}", response_model=schemas_media.ProgrammeResponse)
# def delete_programme(
#     programme_id: int,
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     # Vérification des permissions : seuls les administrateurs peuvent supprimer des programmes
#     # if current_user.role != "admin":
#     #     raise HTTPException(status_code=403, detail="Action non autorisée")

#     # Recherche du programme
#     db_programme = db.query(models.Programme).filter(models.Programme.id == programme_id).first()

#     # Si le programme n'existe pas, lever une erreur
#     if not db_programme:
#         raise HTTPException(status_code=404, detail="Programme non trouvé")

#     # Suppression du programme
#     db.delete(db_programme)
#     db.commit()
#     return db_programme


# # 5. Endpoint pour obtenir les détails d'un programme spécifique
# @router.get("/one/{programme_id}", response_model=schemas_media.ProgrammeResponse)
# def get_programme(programme_id: int, db: Session = Depends(get_db)):
#     # Recherche du programme dans la base de données
#     db_programme = db.query(models.Programme).filter(models.Programme.id == programme_id).first()

#     # Si le programme n'existe pas, lever une erreur
#     if not db_programme:
#         raise HTTPException(status_code=404, detail="Programme non trouvé")
#     return db_programme


# # 6. Fonction pour assigner un présentateur à un programme
# def assign_presenter_to_programme(db: Session, programme_id: int, presenter_id: int):
#     # Recherche du programme et du présentateur
#     programme = db.query(models.Programme).filter(models.Programme.id == programme_id).first()
#     if not programme:
#         raise HTTPException(status_code=404, detail="Programme non trouvé")

#     presenter = db.query(models.Presenter).filter(models.Presenter.id == presenter_id).first()
#     if not presenter:
#         raise HTTPException(status_code=404, detail="Présentateur non trouvé")

#     # Assignation du présentateur
#     programme.presenter_id = presenter_id
#     db.commit()
#     db.refresh(programme)
#     return {"message": f"Présentateur {presenter.name} assigné avec succès à {programme.name}"}


# # 7. Fonction pour désassigner un présentateur d'un programme
# def unassign_presenter_from_programme(db: Session, programme_id: int):
#     # Recherche du programme
#     programme = db.query(models.Programme).filter(models.Programme.id == programme_id).first()
#     if not programme:
#         raise HTTPException(status_code=404, detail="Programme non trouvé")

#     # Désassignation du présentateur
#     programme.presenter_id = None
#     db.commit()
#     db.refresh(programme)
#     return {"message": "Présentateur désassigné avec succès"}


# # 8. Endpoint pour assigner un présentateur
# @router.put("/{programme_id}/assign_presenter")
# async def assign_presenter(programme_id: int, presenter_id: int, db: Session = Depends(get_db)):
#     return assign_presenter_to_programme(db, programme_id, presenter_id)


# # 9. Endpoint pour désassigner un présentateur
# @router.put("/{programme_id}/unassign_presenter")
# async def unassign_presenter(programme_id: int, db: Session = Depends(get_db)):
#     return unassign_presenter_from_programme(db, programme_id)



