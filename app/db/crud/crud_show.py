from sqlalchemy.orm import joinedload, aliased
from typing import List, Dict
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc
from app.models import Show, Segment,Presenter, Guest, ShowPresenter, SegmentGuest
from sqlalchemy.orm import Session
from app.schemas import ShowCreateWithDetail, ShowUpdate ,ShowCreate,ShowBase_jsonShow # Schémas de validation pour Show
from fastapi import HTTPException
from starlette import status
from datetime import datetime


#============ update show status


def update_show_status(db: Session, show_id: int, status: str):
    """
    Met à jour le statut d'un show dans la base de données.

    Args:
        - db (Session): Session de base de données.
        - show_id (int): ID du show à mettre à jour.
        - status (str): Nouveau statut à appliquer.

    Returns:
        - dict: ID du show et son statut mis à jour.
    """
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with ID {show_id} not found."
        )
    show.status = status
    db.commit()
    db.refresh(show)
    return {"id": show.id, "status": show.status}

# ==================  create show details ========================

def create_show_with_elements_from_json(
    db: Session,
    shows_data: List[ShowBase_jsonShow],
    curent_user_id: int
):
    try:
        for show_data in shows_data:
            # Création de l'émission
            new_show = Show(
                title=show_data.title,
                type=show_data.type,
                broadcast_date=show_data.broadcast_date,
                duration=show_data.duration,
                frequency=show_data.frequency,
                description=show_data.description,
                status=show_data.status,
                emission_id=show_data.emission_id,
                created_by=curent_user_id,
            )
            db.add(new_show)
            db.flush()  # Sauvegarde partielle pour récupérer l'ID de l'émission

            # Ajout des segments et des invités spécifiques à chaque segment
            for segment_data in show_data.segments:
                # Création du segment
                new_segment = Segment(
                    title=segment_data.title,
                    type=segment_data.type,
                    duration=segment_data.duration,
                    description=segment_data.description,
                    technical_notes=segment_data.technical_notes,
                    position=segment_data.position,
                    startTime=segment_data.startTime,
                    show_id=new_show.id,
                )
                db.add(new_segment)
                db.flush()  # Sauvegarde partielle pour récupérer l'ID du segment

                # Association des invités à ce segment
                guest_ids = segment_data.guests  # Récupère les invités spécifiques pour ce segment
                for guest_id in guest_ids:
                    guest = db.query(Guest).filter(Guest.id == guest_id).one_or_none()
                    if guest:
                        new_segment.guests.append(guest)

            # Ajout des présentateurs à l'émission
            for presenter_data in show_data.presenters:
                presenter = db.query(Presenter).filter(Presenter.id == presenter_data.id).one_or_none()
                if presenter:
                    # L'ajout du présentateur à l'émission
                    new_show.presenters.append(presenter)

                    # Gérer le rôle (si nécessaire, ici on peut vérifier 'isMainPresenter' par exemple)
                    if presenter_data.isMainPresenter:
                        # Faire quelque chose si c'est le présentateur principal (par exemple, modifier un champ 'role')
                        pass

            db.commit()

        return new_show  # Retourner la dernière émission créée
    except IntegrityError as e:
        print(e)
        db.rollback()
        raise ValueError(f"Une erreur s'est produite : {str(e)}")
    except Exception as e:
        print(e)    
        db.rollback()
        raise ValueError(f"Une erreur inattendue s'est produite : {str(e)}")






#=================== end create show details ========================





# ==================  get show details ========================


# Requête pour récupérer les émissions avec leurs segments, invités, et présentateurs
def get_show_details_all(db: Session):
    # Récupérer toutes les émissions avec les segments, invités et présentateurs associés
    shows = db.query(Show).options(
        joinedload(Show.emission),  # Charger les détails de l'émission associée
        joinedload(Show.presenters),  # Charger les présentateurs associés à chaque émission
        joinedload(Show.segments).joinedload(Segment.guests),  # Charger les segments avec leurs invités
    ).all()
   
    show_details = []

    for show in shows:
        show_info = {
            "id": show.id,
            "emission": show.emission.title if show.emission else "No Emission Linked",
            "emission_id": show.emission_id,
            "title": show.title,
            "type": show.type,
            "broadcast_date": show.broadcast_date,
            "duration": show.duration,
            "frequency": show.frequency,
            "description": show.description,
            "status": show.status,
            "presenters": [],
            "segments": []
        }

        # Récupérer les présentateurs associés
        for presenter in show.presenters:
            show_info["presenters"].append({
                "id": presenter.id,
                "name": presenter.name,
                "contact_info": presenter.contact_info,
                "biography": presenter.biography,
                "isMainPresenter": presenter.isMainPresenter,
            })
        
        # Récupérer et trier les segments associés par la position
        sorted_segments = sorted(show.segments, key=lambda x: x.position)
        
        for segment in sorted_segments:
            segment_info = {
                "id": segment.id,
                "title": segment.title,
                "type": segment.type,
                "duration": segment.duration,
                "description": segment.description,
                "startTime": segment.startTime,
                "position": segment.position,
                "technical_notes": segment.technical_notes,
                "guests": []
            }
            
            # Récupérer les invités associés à ce segment
            for guest in segment.guests:
                segment_info["guests"].append({
                    "id": guest.id,
                    "name": guest.name,
                    "contact_info": guest.contact_info,
                    "biography": guest.biography,
                    "role": guest.role,
                    "avatar": guest.avatar,
                })
            
            show_info["segments"].append(segment_info)
        
        show_details.append(show_info)

    return show_details


#=================== end get show details ========================


# ==================  get show details filtred (whitout satus termine, preparation archive) ========================

def get_production_show_details(db: Session):
    # Récupérer toutes les émissions avec les segments, invités et présentateurs associés,
    # en excluant les émissions avec les statuts "Terminée" ou "En préparation"
    shows = db.query(Show).options(
        joinedload(Show.emission),  # Charger les détails de l'émission associée
        joinedload(Show.presenters),  # Charger les présentateurs associés à chaque émission
        joinedload(Show.segments).joinedload(Segment.guests),  # Charger les segments avec leurs invités
    ).filter(
        Show.status.not_in(["preparation", "termine", "archive"])  # Exclure les émissions avec ces statuts
    ).all()
   
    show_details = []

    for show in shows:
        show_info = {
            "id": show.id,
            "emission": show.emission.title if show.emission else "No Emission Linked",
            "emission_id": show.emission_id,
            "title": show.title,
            "type": show.type,
            "broadcast_date": show.broadcast_date,
            "duration": show.duration,
            "frequency": show.frequency,
            "description": show.description,
            "status": show.status,
            "presenters": [],
            "segments": []
        }

        # Récupérer les présentateurs associés
        for presenter in show.presenters:
            show_info["presenters"].append({
                "id": presenter.id,
                "name": presenter.name,
                "contact_info": presenter.contact_info,
                "biography": presenter.biography,
                "isMainPresenter": presenter.isMainPresenter,
            })
        
        # Récupérer et trier les segments associés par la position
        sorted_segments = sorted(show.segments, key=lambda x: x.position)
        
        for segment in sorted_segments:
            segment_info = {
                "id": segment.id,
                "title": segment.title,
                "type": segment.type,
                "duration": segment.duration,
                "description": segment.description,
                "startTime": segment.startTime,
                "position": segment.position,
                "technical_notes": segment.technical_notes,
                "guests": []
            }
            
            # Récupérer les invités associés à ce segment
            for guest in segment.guests:
                segment_info["guests"].append({
                    "id": guest.id,
                    "name": guest.name,
                    "contact_info": guest.contact_info,
                    "biography": guest.biography,
                    "role": guest.role,
                    "avatar": guest.avatar,
                })
            
            show_info["segments"].append(segment_info)
        
        show_details.append(show_info)

    return show_details

#=================== end get show details filtred ========================
# ==================  get show details filtred (whitout satus termine, preparation archive) ========================



# ==================  get show details filtred By user owner ========================

def get_show_details_owned(db: Session, user_id: int):
    # Récupérer toutes les émissions créées par un utilisateur spécifique avec les segments, invités et présentateurs associés,
    # en excluant les émissions avec les statuts "Terminée" ou "En préparation"
    shows = db.query(Show).options(
        joinedload(Show.emission),  # Charger les détails de l'émission associée
        joinedload(Show.presenters),  # Charger les présentateurs associés à chaque émission
        joinedload(Show.segments).joinedload(Segment.guests),  # Charger les segments avec leurs invités
    ).filter(
        Show.created_by == user_id,  # Filtrer par l'ID de l'utilisateur créateur
        Show.status.not_in(["archive",])  # Exclure les statuts spécifiques
    ).all()
   
    show_details = []

    for show in shows:
        show_info = {
            "id": show.id,
            "emission": show.emission.title if show.emission else "No Emission Linked",
            "emission_id": show.emission_id,
            "title": show.title,
            "type": show.type,
            "broadcast_date": show.broadcast_date,
            "duration": show.duration,
            "frequency": show.frequency,
            "description": show.description,
            "status": show.status,
            "presenters": [],
            "segments": []
        }

        # Récupérer les présentateurs associés
        for presenter in show.presenters:
            show_info["presenters"].append({
                "id": presenter.id,
                "name": presenter.name,
                "contact_info": presenter.contact_info,
                "biography": presenter.biography,
                "isMainPresenter": presenter.isMainPresenter,
            })
        
        # Récupérer et trier les segments associés par la position
        sorted_segments = sorted(show.segments, key=lambda x: x.position)
        
        for segment in sorted_segments:
            segment_info = {
                "id": segment.id,
                "title": segment.title,
                "type": segment.type,
                "duration": segment.duration,
                "description": segment.description,
                "startTime": segment.startTime,
                "position": segment.position,
                "technical_notes": segment.technical_notes,
                "guests": []
            }
            
            # Récupérer les invités associés à ce segment
            for guest in segment.guests:
                segment_info["guests"].append({
                    "id": guest.id,
                    "name": guest.name,
                    "contact_info": guest.contact_info,
                    "biography": guest.biography,
                    "role": guest.role,
                    "avatar": guest.avatar,
                })
            
            show_info["segments"].append(segment_info)
        
        show_details.append(show_info)

    return show_details






#=================== end get show details filtred by user owne ========================

# ==================  get show details by id ========================
# from sqlalchemy.orm import joinedload
# from datetime import datetime

# Requête pour récupérer une émission particulière par ID avec ses segments, invités et présentateurs
def get_show_details_by_id(db:Session, show_id:int):
    print("/////////////////////////// {show_id}")
    print(show_id)
    # Récupérer une seule émission par son ID avec les segments, invités et présentateurs associés
    show = db.query(Show).options(
        joinedload(Show.presenters),  # Charger les présentateurs associés à l'émission
        joinedload(Show.segments).joinedload(Segment.guests),  # Charger les segments avec leurs invités
    ).filter(Show.id == show_id).first()
    print(show)

    if not show:
        return None  # Aucun show trouvé avec l'ID donné

    show_info = {
        "title": show.title,
        "type": show.type,
        "broadcast_date": show.broadcast_date,
        "duration": show.duration,
        "frequency": show.frequency,
        "description": show.description,
        "status": show.status,
        "presenters": [],
        "segments": []
    }

    # Récupérer les présentateurs associés
    for presenter in show.presenters:
        show_info["presenters"].append({
            "name": presenter.name,
            "contact_info": presenter.contact_info,
            "biography": presenter.biography,
            "isMainPresenter": presenter.isMainPresenter,
        })
    
    # Récupérer les segments associés
    for segment in show.segments:
        segment_info = {
            "title": segment.title,
            "type": segment.type,
            "duration": segment.duration,
            "description": segment.description,
            "startTime": segment.startTime,
            "position": segment.position,
            "guests": []
        }
        
        # Récupérer les invités associés à ce segment
        for guest in segment.guests:
            segment_info["guests"].append({
                "name": guest.name,
                "contact_info": guest.contact_info,
                "biography": guest.biography,
                "role": guest.role,
                "avatar": guest.avatar,
            })
        
        show_info["segments"].append(segment_info)

    return show_info


# //----------------=---------------------------------------=---------------
# 
# 
# 
# 



#//////////////////// show + details invite, presentateurs et segment /////////

def create_show_with_details(db: Session, show_data: ShowCreateWithDetail,curent_user_id:int):
    """
    Crée un show avec ses présentateurs, segments et invités en fonction des IDs envoyés par le frontend.

    Parameters:
    - db: Session de la base de données SQLAlchemy
    - show_data: Schéma contenant les données pour le show, avec les IDs des présentateurs et invités.

    Returns:
    - Le show créé avec ses relations.
    """
    try:
        # Étape 1 : Créer le show principal
        db_show = Show(
            title=show_data.title,
            type=show_data.type,
            broadcast_date=show_data.broadcast_date,
            duration=show_data.duration,
            frequency=show_data.frequency,
            description=show_data.description,
            status=show_data.status,
            emission_id=show_data.emission_id,
            created_by =curent_user_id,
        )
        db.add(db_show)
        db.commit()
        db.refresh(db_show)
        print("////////////////////////// Étape 1 : Créer le show principal")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du show : {str(e)}"
        )

    try:
        # Étape 2 : Associer les présentateurs via leurs IDs
        if show_data.presenter_ids:
            presenters = db.query(Presenter).filter(Presenter.id.in_(show_data.presenter_ids)).all()
            if len(presenters) != len(show_data.presenter_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un ou plusieurs IDs de présentateurs sont invalides."
                )
            db_show.presenters = presenters
            print("////////////////////////////////Étape 2 : Associer les présentateurs via leurs IDs")

        # Étape 3 : Créer les segments et associer les invités
        if show_data.segments:
            for segment_data in show_data.segments:
                try:
                    # Créer le segment
                    segment = Segment(
                        title=segment_data.title,
                        type=segment_data.type,
                        position=segment_data.position,
                        duration=segment_data.duration,
                        description=segment_data.description,
                        show_id=db_show.id,
                    )
                    db.add(segment)
                    db.commit()
                    db.refresh(segment)
                    print("/////////////////////////////////Étape 3 : Créer les segments et associer les invités")

                    # Associer les invités au segment
                    if segment_data.guest_ids:
                        guests = db.query(Guest).filter(Guest.id.in_(segment_data.guest_ids)).all()
                        if len(guests) != len(segment_data.guest_ids):
                            raise ValueError(
                                f"Un ou plusieurs IDs d'invités sont invalides pour le segment '{segment.title}'."
                            )
                        segment.guests = guests
                        print("/////////////////////////////////add guest to segment")


                except ValueError as ve:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(ve)
                    )
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Erreur lors de la création d'un segment ou de l'association des invités : {str(e)}"
                    )

        # Étape 4 : Validation finale des modifications
        db.commit()
        db.refresh(db_show)
        print(db_show)
        print("/////////////////////////////////Étape 4 : Validation finale des modifications")

        return db_show

    except HTTPException as http_exc:
        raise http_exc  # Relève les erreurs prévues avec des codes spécifiques
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur inattendue lors de la création du show avec ses détails : {str(e)}"
        )



# ----------------------exemple requette frontend--------------
# {
#     "title": "Evening Talk Show",
#     "type": "Talk Show",
#     "broadcast_date": "2024-12-19T20:00:00",
#     "duration": 120,
#     "frequency": "Daily",
#     "description": "An engaging evening talk show.",
#     "status": "active",
#     "emission_id": 1,
#     "presenter_ids": [1, 2],  // IDs des présentateurs
#     "segments": [
#         {
#             "title": "Opening Remarks",
#             "type": "Introduction",
#             "position": 1,
#             "duration": 10,
#             "description": "Welcome and introduction.",
#             "guest_ids": []  // Aucun invité pour ce segment
#         },
#         {
#             "title": "Expert Discussion",
#             "type": "Panel",
#             "position": 2,
#             "duration": 90,
#             "description": "Discussion with invited experts.",
#             "guest_ids": [3, 4]  // IDs des invités
#         }
#     ]
# }






# /////////////////  fin show create avec details/////////////////




# //////////////////// update shw avec details////////////


def update_show_with_details(db: Session, show_id: int, show_data: dict):
    """
    Met à jour un show avec ses segments, présentateurs et invités.

    Args:
        - db (Session): La session de base de données.
        - show_id (int): L'ID du show à mettre à jour.
        - show_data (dict): Les nouvelles données pour le show.

    Returns:
        - dict: Les détails du show mis à jour.
    """
    try:
        # Récupérer le show existant
        show = db.query(Show).filter(Show.id == show_id).first()
        if not show:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Show with ID {show_id} not found."
            )
        
        # Mettre à jour les champs du show
        for key, value in show_data.items():
            if hasattr(show, key) and key not in ["segments", "presenter_ids"]:
                setattr(show, key, value)

        # Mettre à jour les présentateurs (relation plusieurs-à-plusieurs)
        if "presenter_ids" in show_data:
            presenters = db.query(Presenter).filter(Presenter.id.in_(show_data["presenter_ids"])).all()
            if len(presenters) != len(show_data["presenter_ids"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more presenter IDs are invalid."
                )
            show.presenters = presenters

        # Mettre à jour les segments
        if "segments" in show_data:
            for segment_data in show_data["segments"]:
                segment_id = segment_data.get("id")
                if segment_id:  # Segment existant à mettre à jour
                    segment = db.query(Segment).filter(Segment.id == segment_id, Segment.show_id == show_id).first()
                    if not segment:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Segment with ID {segment_id} not found for this show."
                        )
                    # Mettre à jour les champs du segment
                    for key, value in segment_data.items():
                        if hasattr(segment, key) and key != "guest_ids":
                            setattr(segment, key, value)
                    
                    # Mettre à jour les invités du segment
                    if "guest_ids" in segment_data:
                        guests = db.query(Guest).filter(Guest.id.in_(segment_data["guest_ids"])).all()
                        if len(guests) != len(segment_data["guest_ids"]):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"One or more guest IDs are invalid for segment '{segment.title}'."
                            )
                        segment.guests = guests
                else:  # Nouveau segment à ajouter
                    new_segment = Segment(
                        title=segment_data["title"],
                        type=segment_data["type"],
                        position=segment_data["position"],
                        duration=segment_data["duration"],
                        description=segment_data.get("description"),
                        show_id=show.id
                    )
                    db.add(new_segment)
                    db.flush()  # Générer un ID pour le nouveau segment

                    # Ajouter les invités au nouveau segment
                    if "guest_ids" in segment_data:
                        guests = db.query(Guest).filter(Guest.id.in_(segment_data["guest_ids"])).all()
                        if len(guests) != len(segment_data["guest_ids"]):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"One or more guest IDs are invalid for new segment '{new_segment.title}'."
                            )
                        new_segment.guests = guests

        # Valider les changements dans la base de données
        db.commit()
        db.refresh(show)
        return show

    except HTTPException as http_exc:
        # Remonter les erreurs spécifiques levées
        raise http_exc

    except Exception as e:
        # Gestion des erreurs inattendues
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )



# ////////////////////// fin update show avec details /////////////////


# /////////////////////// get show with details///////////


def get_show_details(session: Session, show_id: int):
    # Alias pour les invités et les présentateurs
    guest_alias = aliased(Guest)
    presenter_alias = aliased(Presenter)
    
    # Requête pour récupérer les informations du show, segments, invités et présentateurs
    query = session.query(
        Show,
        Segment,
        guest_alias,
        presenter_alias
    ).join(Segment, Show.id == Segment.show_id) \
    .join(SegmentGuest, Segment.id == SegmentGuest.segment_id) \
    .join(guest_alias, SegmentGuest.guest_id == guest_alias.id) \
    .join(ShowPresenter, Show.id == ShowPresenter.show_id) \
    .join(presenter_alias, ShowPresenter.presenter_id == presenter_alias.id) \
    .filter(Show.id == show_id)
    
    result = query.all()
    
    # Retourner les résultats sous une forme plus facile à utiliser
    show_details = []
    for show, segment, guest, presenter in result:
        show_details.append({
            'show': {
                'id': show.id,
                'title': show.title,
                'type': show.type,
                'broadcast_date': show.broadcast_date,
                'description': show.description,
                'status': show.status,
            },
            'segment': {
                'id': segment.id,
                'title': segment.title,
                'type': segment.type,
                'duration': segment.duration,
            },
            'guest': {
                'id': guest.id,
                'name': guest.name,
                'contact_info': guest.contact_info,
            },
            'presenter': {
                'id': presenter.id,
                'name': presenter.name,
                'contact_info': presenter.contact_info,
            }
        })
    
    return show_details





# ////////////////// get show with details //////////
def get_show_with_details(db: Session, show_id):
    """
    Récupère tous les détails d'un conducteur (émission) avec ses présentateurs, segments (triés par position), et invités.
    """
    # Requête principale avec chargement des relations
    show = (
        db.query(Show)
        .options(
            joinedload(Show.presenters),  # Charge les présentateurs
            joinedload(Show.segments).joinedload(Segment.guests)  # Charge les segments et leurs invités
        )
        .filter(Show.id == show_id)
        .one_or_none()
    )

    if not show:
        return None

    # Structure les données dans un format compréhensible
    result = {
        "id": show.id,
        "title": show.title,
        "type": show.type,
        "broadcast_date": show.broadcast_date,
        "duration": show.duration,
        "description": show.description,
        "status": show.status,
        "presenters": [
            {"id": presenter.id, "name": presenter.name, "contact_info": presenter.contact_info}
            for presenter in show.presenters
        ],
        # Tri des segments par leur position avant de les structurer
        "segments": [
            {
                "id": segment.id,
                "title": segment.title,
                "type": segment.type,
                "position": segment.position,  # Ajout de la position
                "duration": segment.duration,
                "description": segment.description,
                "guests": [
                    {"id": guest.id, "name": guest.name, "contact_info": guest.contact_info}
                    for guest in segment.guests
                ]
            }
            for segment in sorted(show.segments, key=lambda seg: seg.position)  # Tri par position
        ]
    }
    return result


# def get_show_with_details_raw(session, show_id):
#     query = """
#     SELECT
#         s.id AS show_id, s.title AS show_title, s.type AS show_type, 
#         p.id AS presenter_id, p.name AS presenter_name,
#         seg.id AS segment_id, seg.title AS segment_title, seg.position AS segment_position,
#         g.id AS guest_id, g.name AS guest_name
#     FROM shows s
#     LEFT JOIN show_presenters sp ON s.id = sp.show_id
#     LEFT JOIN presenters p ON sp.presenter_id = p.id
#     LEFT JOIN segments seg ON seg.show_id = s.id
#     LEFT JOIN segment_guests sg ON seg.id = sg.segment_id
#     LEFT JOIN guests g ON sg.guest_id = g.id
#     WHERE s.id = :show_id
#     ORDER BY seg.position ASC;  -- Tri des segments par position
#     """
#     result = session.execute(query, {"show_id": show_id}).fetchall()
#     return result




# Fonction pour créer un show
def create_show(db: Session, show: ShowCreate):
    """
    Crée un nouveau show dans la base de données.

    Parameters:
    - db: Session de la base de données SQLAlchemy
    - show: Schéma ShowCreate contenant les données du show à créer

    Retourne:
    - L'objet Show créé dans la base de données
    """
    try:
        # Crée une instance de Show à partir des données reçues dans le schéma ShowCreate
        db_show = Show(
            title=show.title,  # Le titre du show
            type=show.type,  # Le type du show (par exemple, talk-show, émission musicale, etc.)
            broadcast_date=show.broadcast_date,  # Date et heure de diffusion
            duration=show.duration,  # Durée du show en minutes
            frequency=show.frequency,  # Fréquence de diffusion (facultatif)
            description=show.description,  # Description du show (facultatif)
            status=show.status,  # Statut du show (par exemple, 'actif' ou 'inactif')
            emission_id=show.emission_id,  # L'ID de l'émission liée (facultatif)
        )

        # Ajoute l'objet Show à la session
        db.add(db_show)
        # Engage la transaction dans la base de données
        db.commit()
        # Récupère l'objet Show nouvellement créé et actualisé (inclut l'ID généré)
        db.refresh(db_show)

        # Retourne l'objet Show créé
        return db_show

    except Exception as e:
        # Si une erreur se produit, on la capture et on retourne une HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du show: {str(e)}"
        )


# Fonction pour obtenir tous les shows
def get_shows(db: Session, skip: int = 0, limit: int = 10):
    """
    Récupère une liste de shows depuis la base de données.

    Parameters:
    - db: Session de la base de données SQLAlchemy
    - skip: Nombre d'éléments à ignorer (pour la pagination)
    - limit: Nombre maximum de shows à récupérer (pour la pagination)

    Retourne:
    - Liste des objets Show
    """
    try:
        # Effectue une requête pour récupérer tous les shows, avec pagination
        return db.query(Show).offset(skip).limit(limit).all()

    except Exception as e:
        # Si une erreur se produit, on la capture et on retourne une HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des shows: {str(e)}"
        )


# Fonction pour obtenir un show par son ID
def get_show_by_id(db: Session, show_id: int):
    """
    Récupère un show en fonction de son ID.

    Parameters:
    - db: Session de la base de données SQLAlchemy
    - show_id: ID du show à récupérer

    Retourne:
    - L'objet Show correspondant à l'ID, ou une erreur si le show n'existe pas
    """
    try:
        # Effectue une requête pour rechercher un show avec l'ID donné
        db_show = db.query(Show).filter(Show.id == show_id).first()

        if db_show is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Show avec ID {show_id} non trouvé"
            )

        return db_show

    except HTTPException:
        # Re-raise HTTPException si elle a été levée
        raise
    except Exception as e:
        # Si une autre erreur se produit, on la capture et on retourne une HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du show: {str(e)}"
        )


# Fonction pour mettre à jour un show existant
def update_show(db: Session, show_id: int, show: ShowUpdate):
    """
    Met à jour les informations d'un show existant.

    Parameters:
    - db: Session de la base de données SQLAlchemy
    - show_id: ID du show à mettre à jour
    - show: Schéma ShowUpdate contenant les champs à mettre à jour

    Retourne:
    - L'objet Show mis à jour, ou une erreur si le show n'existe pas
    """
    try:
        # Recherche le show dans la base de données par son ID
        db_show = db.query(Show).filter(Show.id == show_id).first()

        if db_show is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Show avec ID {show_id} non trouvé"
            )

        # Pour chaque champ qui a été renseigné dans le schéma ShowUpdate, on met à jour l'attribut du show
        for key, value in show.model_dump(exclude_unset=True).items():
            setattr(db_show, key, value)  # Mise à jour de l'attribut

        # Engage la transaction de mise à jour dans la base de données
        db.commit()
        # Actualise l'objet Show avec les nouvelles données
        db.refresh(db_show)

        # Retourne l'objet Show mis à jour
        return db_show

    except HTTPException:
        # Re-raise HTTPException si elle a été levée
        raise
    except Exception as e:
        # Si une erreur se produit, on la capture et on retourne une HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du show: {str(e)}"
        )


# Fonction pour supprimer un show
def delete_show(db: Session, show_id: int):
    """
    Supprime un show de la base de données.

    Parameters:
    - db: Session de la base de données SQLAlchemy
    - show_id: ID du show à supprimer

    Retourne:
    - L'objet Show supprimé, ou une erreur si le show n'existe pas
    """
    try:
        # Recherche le show à supprimer par son ID
        db_show = db.query(Show).filter(Show.id == show_id).first()

        if db_show is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Show avec ID {show_id} non trouvé"
            )

        # Supprime le show de la base de données
        db.delete(db_show)
        # Engage la transaction de suppression
        db.commit()

        # Retourne l'objet Show supprimé
        return db_show

    except HTTPException:
        # Re-raise HTTPException si elle a été levée
        raise
    except Exception as e:
        # Si une erreur se produit, on la capture et on retourne une HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du show: {str(e)}"
        )


def delete_all_shows(db: Session) -> int:
    """
    Supprime tous les shows de la base et retourne le nombre supprimé.
    """
    try:
        count = db.query(Show).delete(synchronize_session=False)
        db.commit()
        return count
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de tous les shows : {e}"
        )


def delete_shows_by_user(db: Session, user_id: int) -> int:
    """
    Supprime tous les shows créés par un utilisateur donné et retourne le nombre supprimé.
    """
    try:
        count = (db.query(Show)
                   .filter(Show.created_by == user_id)
                   .delete(synchronize_session=False))
        db.commit()
        return count
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression des shows de l'utilisateur {user_id} : {e}"
        )
