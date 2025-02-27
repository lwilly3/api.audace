from fastapi import FastAPI, Depends, HTTPException,APIRouter
from app.db.database import get_db
from app.db.crud.crud_dashbord import get_dashboard
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from app.models.model_user import User
from core.auth import oauth2

router = APIRouter(
        prefix="/dashbord",
     tags=['dashbord']
    
)

@router.get("/")
def get_dashboard_route(db: Session = Depends(get_db), user_id: User = Depends(oauth2.get_current_user)):
    """
    Endpoint pour récupérer les données du tableau de bord.
    
    Args:
        db (Session): Session de base de données injectée via Depends.
    
    Returns:
        dict: Données formatées pour le tableau de bord.
    
    Raises:
        HTTPException: Avec un code d'erreur approprié en cas d'échec.
    """
    try:
        dashboard_data = get_dashboard(db)
        return dashboard_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur de base de données : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne s'est produite : {str(e)}"
        )