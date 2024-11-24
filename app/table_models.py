from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
# from sqlalchemy.sql.expression import null
from .database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text

# class PostsEtCount(Base):
#     Posts= relationship("Posts")
#     Votes= relationship("User")
    

# 10h30 database migration tool (alembic) pour resoudre la limitation de sqlalchemy de puvoir modifier la stucture dune table dejas cree
# model SQLAlchemy (model ORM)
# definit la structure des tables de la base de donnee
# utiliser pour effectuer des requettes dans la base de donnee
class Posts(Base):
    __tablename__ = "posts"

    id=Column(Integer, primary_key=True, nullable=False)
    title=Column(String, nullable=False)
    content=Column(String, nullable=False)
    published=Column(Boolean, server_default='TRUE', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False )
    # 8h34 on fait refference a la classe User et non a la table user
    # cela va cree une autre propriete a retourner en faisant la relation avec la table user se basant sur le owner id et nous le retourner
    # cette fonctionnalite est gere par sqlalchemy sans avoir a modifier notre table dans la base de donnee
    owner= relationship("User")
    # votes= relationship("Votes")



class User(Base):
    __tablename__ = "users"

    id=Column(Integer, primary_key=True, nullable=False)
    email=Column(String,nullable=False, unique=True)
    password=Column(String,nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()')) 
    phone_number=Column(String)



#9h30 ici dans la table votes,  post_id et user_id doivent ere une combinaison unique
# 9h53 la fonction de jonction de deux posts  
    # https://www.postgresqltutorial.com/postgresql-tutorial/postgresql-joins/

# 10h10 groupage
class Votes(Base):
    __tablename__="votes"  
    post_id=Column( Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    user_id=Column( Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)