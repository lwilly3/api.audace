# Guide d'installation de l'API Audace sur Dokploy

## ✅ Compatibilité
Votre projet **FastAPI + PostgreSQL + Alembic + JWT** est totalement compatible avec **Dokploy** via Docker Compose.

---

## 📋 Prérequis
- Dokploy installé sur votre serveur Ubuntu
- Accès SSH au serveur
- Nom de domaine (optionnel mais recommandé)
- Repository GitHub disponible

---

## 🚀 Étapes d'installation

### 1️⃣ Préparer votre repository
Ajoutez ces fichiers à la racine de votre projet GitHub :
- `docker-compose.yml`
- `Dockerfile`
- `.dockerignore`

```bash
git add docker-compose.yml Dockerfile .dockerignore
git commit -m "Add Docker configuration for Dokploy"
git push origin main
```

---

### 2️⃣ Créer le projet dans Dokploy
1. Connectez-vous à Dokploy (`http://votre-ip:3000`)
2. Cliquez sur **Create Project**
3. Nom : `api-audace`
4. Cliquez sur **Create**

Ensuite, ajoutez un service "Compose" nommé : `audace-api`.

---

### 3️⃣ Configurer le repository GitHub
- **Repository URL** : `https://github.com/lwilly3/api.audace`
- **Branch** : `main`
- **Path** : `/`
- **Compose File** : `docker-compose.yml`
- Activez **Auto Deploy** (optionnel)

---

### 4️⃣ Configurer les variables d'environnement
Ajoutez dans Dokploy :

#### 🔐 Base de données
```
POSTGRES_DB=audace_db
POSTGRES_USER=audace_user
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
```

#### 🔑 JWT & sécurité
```
SECRET_KEY=votre_cle_secrete_32_caracteres_minimum
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 📧 Configuration email
```
MAIL_USERNAME=votre.email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
MAIL_FROM=noreply@audace.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Audace API
MAIL_TLS=true
MAIL_SSL=false
```

#### 🌐 URLs & Ports
```
FRONTEND_URL=https://votre-frontend.com
BACKEND_URL=https://api.votre-domaine.com
API_PORT=8000
ENVIRONMENT=production
DEBUG=false
WORKERS=4
```

---

### 5️⃣ Générer une clé secrète
```bash
openssl rand -hex 32
```
Copiez le résultat dans `SECRET_KEY`.

---

### 6️⃣ Configuration Gmail
1. Activez la validation en 2 étapes
2. Rendez-vous dans *Mots de passe d'applications*
3. Générez un mot de passe
4. Utilisez-le pour `MAIL_PASSWORD`

---

### 7️⃣ Déployer l'application
1. Cliquez sur **Deploy** dans Dokploy
2. Attendez 2 à 5 minutes
3. Vérifiez les logs : migrations Alembic, API démarrée

---

### 8️⃣ Configurer le domaine (optionnel)
1. Dans Dokploy → onglet **Domains**
2. Ajouter votre domaine : `api.votre-domaine.com`
3. Dokploy créera un certificat SSL automatiquement

---

## 🔍 Vérification du déploiement
Test :
```bash
curl http://votre-ip:8000/
curl https://api.votre-domaine.com/
```

Voir les logs :
```bash
docker logs audace_api -f
docker logs audace_db -f
```

---

## 🔧 Commandes utiles
### Redémarrer :
```bash
docker-compose restart api
```

### Migrations Alembic :
```bash
docker exec -it audace_api alembic upgrade head
```

### Accéder à PostgreSQL :
```bash
docker exec -it audace_db psql -U audace_user -d audace_db
```

### Conteneurs actifs :
```bash
docker ps
```

---

## 🛠️ Dépannage
### Erreur DB
```bash
docker logs audace_db
```

### Erreur Alembic
```bash
docker exec -it audace_api alembic downgrade base
docker exec -it audace_api alembic upgrade head
```

### API KO
```bash
docker logs audace_api --tail 100
docker restart audace_api
```

---

## 📊 Monitoring
Voir :
```bash
docker stats audace_api audace_db
```

Monitor Dokploy : CPU, RAM, statut conteneurs

---

## 🔄 Mise à jour de l’application
```bash
git push origin main
```
Puis : **Rebuild** dans Dokploy.

Si Auto Deploy est actif → déploiement automatique.

---

## 🎯 Points importants
- Utiliser mots de passe forts
- Ne jamais commit `.env`
- Configurer SSL
- Backups réguliers du volume Postgres

---

## 📞 Support
- Logs Dokploy
- Documentation : https://docs.dokploy.com
- Tests via curl

---

Votre API Audace est maintenant déployée sur Dokploy 🎉