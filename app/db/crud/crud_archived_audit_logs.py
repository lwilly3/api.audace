from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import ArchivedAuditLog
from app.schemas.schema_archived_audit_logs import ArchivedAuditLogCreate
from sqlalchemy.exc import SQLAlchemyError

def create_archived_log(db: Session, log: ArchivedAuditLogCreate, current_user_id: int):
    try:
        # Création d'un nouveau log d'audit archivé en utilisant les données du schéma
        archived_log = ArchivedAuditLog(
            user_id=current_user_id,  # On utilise l'ID de l'utilisateur actuel
            action=log.action,
            table_name=log.table_name,
            record_id=log.record_id,
            timestamp=log.timestamp or datetime.now(timezone.utc)  # Utilisation de timezone-aware datetime# Si timestamp n'est pas spécifié, utilise l'heure actuelle
        )
        
        # Ajout et commit du nouveau log dans la base de données
        db.add(archived_log)
        db.commit()
        db.refresh(archived_log)  # Rafraîchissement de l'objet pour récupérer les données mises à jour
        
        return archived_log
    except SQLAlchemyError as e:
        db.rollback()  # Annule la transaction en cas d'erreur
        # Vous pouvez aussi enregistrer l'erreur dans un log si nécessaire
        raise Exception(f"Erreur lors de la création du log d'audit archivé : {str(e)}")










# from sqlalchemy.orm import Session
# from app.models import ArchivedAuditLog
# from app.schemas.schema_archived_audit_logs import ArchivedAuditLogCreate



# def create_archived_log(db: Session, log: ArchivedAuditLogCreate):
#     archived_log = ArchivedAuditLog(**log.model_dump())
#     db.add(archived_log)
#     db.commit()
#     db.refresh(archived_log)
#     return archived_log
