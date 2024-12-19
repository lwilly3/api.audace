from passlib.context import CryptContext
# 6h05 installation des librairie pour hacher le pass pip install passlib[bcrypt]

# dit a passlib quel est l'algorique par defaut de hash dans ce cas on ceux utiliser bcrypt
pwd_context= CryptContext(schemes=["bcrypt"], deprecated="auto")

# 6h09
def hash(password: str):
 #    creation et renvoie du hash du mot de pass 
    return pwd_context.hash(password)

def verify(plein_password, hashed_password):
    return pwd_context.verify(plein_password, hashed_password)
    
