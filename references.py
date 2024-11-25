










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




# …or push an existing repository from the command line
# git remote add origin https://github.com/lwilly3/api.audace.git
# git branch -M main
# git push -u origin main

