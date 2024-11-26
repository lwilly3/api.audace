










import time
import psycopg2
from psycopg2.extras import RealDictCursor
# 6h05 installation des librairie pour hacher le pass pip install passlib[bcrypt]
# pip freeze permet de voir toutes les librairie installer dans notre projet

# 8h51 supression de main pour juste le garder comme refference par la suite mais nest plus utiliser dans le projet

# while True:
#     try:
#         connexion =psycopg2.connect(host='localhost', database='fastapi', user='postgres', password='Wcz9pylh', 
#                                 cursor_factory=RealDictCursor)
#         cursor=connexion.cursor()
#         print('conexion a la base de donee reussi')
#         break
#     except Exception as error:
#         print('erreur de connexion a la base de donneee')
#         print(f'Erreur:  {error}')
#         time.sleep(2)   



# 10h10 - 10h15  https://www.postgresqltutorial.com/postgresql-tutorial/postgresql-joins/
# La première requête récupère toutes les informations sur les publications ainsi que les votes associés à chaque publication.
# SELECT * FROM posts LEFT JOIN votes ON posts.id=votes.post_id ;

# La deuxième requête compte le nombre total de votes pour chaque publication. (le probleme ici est que les votes null sont compte comme 1)
# SELECT posts.id, COUNT(*) FROM posts LEFT JOIN votes ON posts.id=votes.post_id group by posts.id ;

# La troisième requête compte le nombre de votes pour chaque publication, même si aucune n'a été effectuée. (indiquera 0 sur les votes null)
# SELECT posts.id, COUNT(votes.post_id) FROM posts LEFT JOIN votes ON posts.id=votes.post_id group by posts.id ;

# La quatrième requête compte le nombre total de votes pour chaque publication et récupère toutes les informations sur les publications.
# SELECT posts.*, COUNT(votes.post_id) FROM posts LEFT JOIN votes ON posts.id=votes.post_id group by posts.id ;

# La cinquième requête compte le nombre total de votes pour chaque publication, mais renomme cette information en "votes" et récupère toutes les informations sur les publications.
# SELECT posts.*, COUNT(votes.post_id) as votes FROM posts LEFT JOIN votes ON posts.id=votes.post_id group by posts.id ;

# La dernière requête est similaire à la cinquième, mais elle ne récupère que les informations sur une publication spécifique (l'identifiant 20).
# SELECT posts.*, COUNT(votes.post_id) as votes FROM posts LEFT JOIN votes ON posts.id=votes.post_id WHERE posts.id=20 group by posts.id ;




# 11h21 config gethub
# le fichier .gitignore permet de definire ce que lon ne veux pas publier sur github
# pip freeze > requirements.txt      vas cree le fichier requirements.txt et y inscrire toutes nos dependence
# pour reinstaller par la suite les dependences pip install -r requirements.txt

# …or create a new repository on the command line
# echo "# api.audace" >> README.md
# git init
# git add README.md      
# git commit -m "first commit"      
# git branch -M main
# git remote add origin https://github.com/lwilly3/api.audace.git
# git push -u origin main


# git init
# git add --all
# git commit -m "publication initial"  

# si on me demande de m'authentifier
# git config --global user.email lwilly32@gmail.com
# git config --global user.name lwilly3

# git branch -M main
# git remote add origin https://github.com/lwilly3/api.audace.git




# …or push an existing repository from the command line
# git remote add origin https://github.com/lwilly3/api.audace.git
# git branch -M main
# git push -u origin main


# ////////////////////// heroku nb se metre dans le dossier de lapliction 
# pour voir si huroko est installee
# heroku --version

# pour se connecter
# heroku login

# pour cree notre app sur huroko
# https://devcenter.heroku.com/articles/getting-started-with-python#create-and-deploy-the-app
# le nom que jutilise est audace-api
# heroku create <nom de l'app>

# pour voir si heruku est maintenant presant dans le projet en plus de l'instende gi(origin ou autre) on devrais voir linstance heroku
# git remote  

# on envoi notre code sur le serveur heroku
#  git push heroku main
# deploiement fait et peut etre verifier sur l'url genere  https://git.heroku.com/audace-api.git

# in faut donnet la commande de demarrage a notre serveru. uvicorn app.main:app
# pour cela on cree un fichier qui indormera a heroku quelle commande faire pour lancer l'application
# pour cela dans le docier racine on cree le fichier Procfile
# https://devcenter.heroku.com/articles/getting-started-with-python#define-a-procfile

# on inscri cette comande dans le Procfife : web: unvicorn app.main:app --host=0.0.0.0 --port=${PORT:-5000}
#  elle autorise toute adresse que le serveur va alouer comme ip host dynamiquement et le port aussi par securite on a mis 5000 comme port par defaut mais cela nest pas cecessaire vue que a chaque demarrage ce port changera
# ici on nutilise pas unvicorn app.main:app --reload vue que nous somme en production et on le vas pas faire des changement sur la production donc pas necessaire dactiver le redemarrage automatique apres modification du serveur


# apres avoir fair des modification les etapes a faire sont :
#  ajouter tout les changements : git add --all
# soumetre la commende : git commit -m " message decrivant la modification"

# envoyer sur github : git push origin main

#  en fin transferer notre code nouvellement envoye sur github ver heroku : git push heroku main

#  pour voir les log heroku
#  heroku logs -t

#  pour avoir postgresql il vas maintelant faloir fayer 5usd par mois ce c'est plus gratuit.
# https://devcenter.heroku.com/articles/eco-dyno-hours



# /////////////////////////////////////// unbutu


# mise a jour du system nouvellement installee
# sudo apt update && sudo apt upgrade -y
# version de python installee  python3 --version
# virification si pip est installee  pip --version

# on vas installer un environnement virtuelle dans notre serveur virtualenv 
#  sudo apt install python3-venv -y

# on install postgresql dans le serveur
# sudo apt install postgresql  postgresql-contrib -y

#  pour acceder a posgresql depuis le termilal on utilise l'outil psql
# psql --version  ou psql --help
# psql -U postgres 
# pour une connexion local postgres a besoin de cette autre methode de connexion car il essaie de me onnecter avec lutilisation actif sur ubuntu (postgres) 
#  lors de l'installation postgress a cree un utilisateur postgres sur mon serveur ubuntu pour le voir : sudo cat /etc/passwd
# pour se connecter sur postgress il va nou faloir nous connecter avat sur cet utilisateur. : sudo -i -u postgres
# 
# puis on se reconnect # psql -U postgres 
# ensuite on cree un mot de pass pour cet utilisateur car par defaut il nas pas de mot de pass
# \password postgres 

# \q pour quiter le terminal postgres
# pour se deconnecter le dutilisateur postgres on entre: exit
# 
# 

# ############### configuration postgress ###########
# 
# on devra modifier les fichiers pg_hba.conf et postgresql.conf
# ils se retrou