
# Étape 2 : Centraliser les imports des modèles
# Créez un fichier Python (ex. : models/__init__.py) qui importe tous les modèles :

# models/__init__.py :


# from app.models.table_models import Posts, UserPost, Votes
# from app.models.mediaLib_models import Skill, InviteSkill, Invite, Programme, Presenter, ProgrammeInvite, ProgrammeStatus, AuditLog, ShowPlan

# # Si nécessaire, importez ici d'autres modèles
# Cela garantit que tous vos modèles sont importés lorsque ce module est chargé.


from .model_permission import Permission
from .model_role import Role
from .model_role_permission import RolePermission
from .model_login_history import LoginHistory
from .model_audit_log import AuditLog
from .model_archive_log_audit import ArchivedAuditLog
from .model_notification import Notification
from .model_presenter import Presenter
# from .model_presenter_history import PresenterHistory
from .model_guest import Guest
from .model_user import User
from .model_user_role import UserRole
from .model_show import Show
from .model_guest import Guest
from .model_segment import Segment
from .model_segment_guests import SegmentGuest
from .model_emissions import Emission
from .model_show_presenter import ShowPresenter 
from .model_show import Show
from .model_user_permissions import UserPermissions

# from .model_show_segment import ShowSegment
# from .model_show_presenter import ShowPresenter

