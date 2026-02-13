from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db  # Cette fonction obtient une session de base de données
from app.db.crud.crud_emission import create_emission, get_emission_by_id, get_emissions, update_emission, delete_emission, soft_delete_emission
from app.schemas.schema_emission import EmissionResponse, EmissionCreate, EmissionUpdate
from core.auth import oauth2
from app.db.crud.crud_audit_logs import log_action

router=APIRouter(
    prefix="/emissions",
    tags=['emissions']
)



# Créer une émission
@router.post("/", response_model=EmissionResponse)
def create_emission_route(emission: EmissionCreate, db: Session = Depends(get_db),  current_user: int = Depends(oauth2.get_current_user)):
    result = create_emission(db, emission)
    log_action(db, current_user.id, "create", "emissions", result.id if result else 0)
    return result

# Lire toutes les émissions
@router.get("/", response_model=list[EmissionResponse])
def get_emissions_route(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return get_emissions(db, skip, limit)

# Lire une émission par son ID
@router.get("/{emission_id}", response_model=EmissionResponse)
def get_emission_by_id_route(emission_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    return get_emission_by_id(db, emission_id)

# Mettre à jour une émission
@router.put("/upd/{emission_id}", response_model=EmissionResponse)
def update_emission_route(emission_id: int, emission: EmissionUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    result = update_emission(db, emission_id, emission)
    log_action(db, current_user.id, "update", "emissions", emission_id)
    return result

# Supprimer une émission
@router.delete("/del/{emission_id}", response_model=bool)
def delete_emission_route(emission_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    result = delete_emission(db, emission_id)
    log_action(db, current_user.id, "delete", "emissions", emission_id)
    return result

# Supprimer une émission (soft delete)
@router.delete("/softDel/{emission_id}", response_model=bool)
def soft_delete_emission_route(emission_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    result = soft_delete_emission(db, emission_id)
    log_action(db, current_user.id, "soft_delete", "emissions", emission_id)
    return result