# Variables d'environnement pour Dokploy

## 📋 À configurer dans Dokploy UI → Settings → Environment Variables

```bash
# === BASE DE DONNÉES (OBLIGATOIRE) ===
POSTGRES_DB=la-database
POSTGRES_USER=le-user
POSTGRES_PASSWORD=le-mot-de-pass

# === JWT & SÉCURITÉ (OBLIGATOIRE) ===
SECRET_KEY=le-code-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRATION_MINUTE=30

# === CONFIGURATION EMAIL (OPTIONNEL) ===
MAIL_USERNAME=votre.email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
MAIL_FROM=noreply@audace.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Audace API
MAIL_TLS=true
MAIL_SSL=false

# === URLS DE L'APPLICATION ===
FRONTEND_URL=https://app.cloud.audace.ovh
BACKEND_URL=https://api.cloud.audace.ovh

# === ENVIRONNEMENT ===
ENVIRONMENT=production
DEBUG=false
WORKERS=4
```

## ⚠️ NOTES IMPORTANTES

1. **NE PAS** mettre `DATABASE_HOSTNAME` dans Dokploy - c'est géré automatiquement par le docker-compose.yml (valeur: `db`)
2. **NE PAS** mettre `DATABASE_PORT`, `DATABASE_USERNAME`, `DATABASE_NAME` - ils sont dérivés automatiquement des variables `POSTGRES_*`
3. **Utilisez** `ACCESS_TOKEN_EXPIRATION_MINUTE` (singulier, pas `MINUTES`)
4. **Générez une nouvelle SECRET_KEY** avec : `openssl rand -hex 32`

## 🔄 Après avoir configuré les variables

1. Cliquez sur **Save** dans Dokploy
2. Cliquez sur **Redeploy**
3. Attendez 2-3 minutes
4. Testez : `https://api.cloud.audace.ovh/docs`
