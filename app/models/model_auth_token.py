# from sqlalchemy import Column, Integer, String, DateTime
# from app.db.database import Base #metadata

# # Modèle représentant un token d'authentification
# class AuthToken(Base):
#     __tablename__ = "auth_tokens"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, index=True)
#     access_token = Column(String, unique=True, index=True)
#     expires_at = Column(DateTime)
