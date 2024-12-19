# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from app.models.model_role import Role
# from app.models.model_permission import Permission
# from app.models.model_role_permission import RolePermission

# def create_default_role_and_permission(db: Session):
#     try:
#         # Vérifier si le rôle "public" existe déjà
#         public_role = db.query(Role).filter_by(name="public").first()
#         if not public_role:
#             public_role = Role(name="public")
#             db.add(public_role)
#             db.commit()
#     except SQLAlchemyError as e:
#         db.rollback()
#         print(f"Error creating public role: {e}")

#     try:
#         # Vérifier si la permission par défaut existe déjà
#         default_permission = db.query(Permission).filter_by(name="default_permission").first()
#         if not default_permission:
#             default_permission = Permission(name="default_permission")
#             db.add(default_permission)
#             db.commit()
#     except SQLAlchemyError as e:
#         db.rollback()
#         print(f"Error creating default permission: {e}")

#     try:
#         # Associer la permission par défaut au rôle "public"
#         role_permission = db.query(RolePermission).filter_by(
#             role_id=public_role.id, permission_id=default_permission.id
#         ).first()
#         if not role_permission:
#             role_permission = RolePermission(
#                 role_id=public_role.id, permission_id=default_permission.id
#             )
#             db.add(role_permission)
#             db.commit()
#     except SQLAlchemyError as e:
#         db.rollback()
#         print(f"Error associating permission to public role: {e}")
