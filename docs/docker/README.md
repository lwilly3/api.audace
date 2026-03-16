# 📚 Documentation Docker - API Audace

Documentation complète pour le déploiement et la maintenance de l'API Audace avec Docker et Dokploy.

---

## 📖 Guides disponibles

### 🚀 [Déploiement sur Dokploy](DOKPLOY_ENV.md)
**Pour qui :** DevOps, première installation  
**Contenu :**
- Variables d'environnement requises
- Configuration Dokploy
- Labels Traefik pour le routage HTTPS
- Checklist de déploiement

**À lire en premier** lors du déploiement initial.

---

### 🛠️ [Guide de Maintenance](MAINTENANCE_GUIDE.md)
**Pour qui :** Administrateurs système, opérations quotidiennes  
**Contenu :**
- Gestion des conteneurs (start/stop/restart)
- Consultation des logs
- Surveillance de la santé des services
- Exécution de commandes dans les conteneurs
- Migrations Alembic
- Mises à jour du code et des dépendances
- Dépannage des problèmes courants

**Référence quotidienne** pour la gestion du système en production.

---

### 🔐 [Sécurité de la Base de Données](DATABASE_SECURITY.md)
**Pour qui :** DBA, DevOps, sécurité  
**Contenu :**
- Protection des données avec volumes Docker
- Scripts de sauvegarde automatique
- Scripts de restauration
- Stratégies de backup (local, distant, snapshot)
- Plan de reprise après sinistre
- Checklist de sécurité

**Essentiel** pour garantir la pérennité des données.

---

### ⏰ [Guide Cron - Automatisation](CRON_GUIDE.md)
**Pour qui :** Administrateurs système, DevOps  
**Contenu :**
- Qu'est-ce que Cron et pourquoi l'utiliser
- Format et syntaxe des expressions Cron
- Installation et configuration
- Exemples de tâches automatiques
- Surveillance et logs
- Dépannage des problèmes courants
- Checklist de mise en place

**Recommandé** pour automatiser les sauvegardes quotidiennes.

---

### 🐳 [Guide Docker Complet](Docker_guide_api_audace.md)
**Pour qui :** Développeurs, DevOps
**Contenu :**
- Architecture Docker de l'application
- Explication du Dockerfile
- Explication du docker-compose.yml
- Réseau et volumes
- Variables d'environnement détaillées

**Référence technique** pour comprendre l'infrastructure.

---

### 🔄 [Déploiement et Récupération](DEPLOYMENT_RECOVERY.md)
**Pour qui :** Développeurs juniors, opérations de maintenance
**Contenu :**
- Comment le serveur démarre (`entrypoint.sh`)
- Connexion à la base de données (`URL.create()`)
- Migrations Alembic (chaîne, idempotence, `alembic_version`)
- Procédure de récupération complète (drop + recreate DB)
- Problèmes courants et solutions (password, DuplicateTable, hostname)
- Checklist de déploiement

**Guide de référence** pour comprendre et résoudre les problèmes de déploiement.

---

## 🗂️ Structure des fichiers

```
docs/docker/
├── README.md                    # Ce fichier (index)
├── DOKPLOY_ENV.md              # Configuration Dokploy
├── MAINTENANCE_GUIDE.md         # Guide de maintenance
├── DATABASE_SECURITY.md         # Sécurité de la base
├── CRON_GUIDE.md               # Automatisation avec Cron
├── Docker_guide_api_audace.md  # Guide technique Docker
└── DEPLOYMENT_RECOVERY.md      # Déploiement et récupération (niveau junior)
```

---

## 🚀 Démarrage rapide

### Pour un nouveau déploiement :
1. Lisez [DOKPLOY_ENV.md](DOKPLOY_ENV.md)
2. Configurez les variables d'environnement
3. Déployez via Dokploy
4. Configurez les sauvegardes automatiques ([DATABASE_SECURITY.md](DATABASE_SECURITY.md))
5. Activez Cron pour les tâches automatiques ([CRON_GUIDE.md](CRON_GUIDE.md))

### Pour la maintenance quotidienne :
- Consultez [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md)
- Commandes rapides : logs, restart, vérifications

### En cas de problème :
1. Section "Dépannage" du [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md)
2. Guide complet de récupération : [DEPLOYMENT_RECOVERY.md](DEPLOYMENT_RECOVERY.md)
3. Vérifiez les logs : `sudo docker logs audace_api --tail 100`
4. Plan de restauration : [DATABASE_SECURITY.md](DATABASE_SECURITY.md)

---

## 📦 Scripts utiles

### Sauvegarde de la base
```bash
./scripts/backup_db.sh
```

### Restauration de la base
```bash
./scripts/restore_db.sh ~/backups/audace_db_YYYYMMDD_HHMMSS.sql.gz
```

### Consulter les logs
```bash
sudo docker logs -f audace_api
```

### Redémarrer les services
```bash
sudo docker compose restart
```

---

## 🔗 Liens externes utiles

- [Documentation Docker](https://docs.docker.com/)
- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [Documentation Dokploy](https://dokploy.com/docs)
- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Traefik](https://doc.traefik.io/traefik/)

---

## 📞 Support

Pour toute question ou problème :
1. Consultez la section "Dépannage" des guides
2. Vérifiez les logs des conteneurs
3. Contactez l'équipe DevOps

---

**Dernière mise à jour :** 16 mars 2026
**Version de l'API :** 1.2.0
**Environnement :** Production (Dokploy + Traefik)
