# ⏰ Guide Cron - Automatisation des Sauvegardes

Guide complet pour configurer les tâches automatiques (Cron) sur votre serveur de production.

---

## 📋 Table des matières

1. [Qu'est-ce que Cron ?](#quest-ce-que-cron-)
2. [Installation et configuration](#installation-et-configuration)
3. [Exemples pour votre projet](#exemples-pour-votre-projet)
4. [Gestion des tâches Cron](#gestion-des-tâches-cron)
5. [Surveillance et logs](#surveillance-et-logs)
6. [Dépannage](#dépannage)

---

## 🤔 Qu'est-ce que Cron ?

**Cron** est un planificateur de tâches Linux qui exécute automatiquement des commandes à des moments précis.

### Pourquoi l'utiliser ?

| Sans Cron | Avec Cron |
|-----------|-----------|
| ❌ Sauvegardes manuelles tous les jours | ✅ Automatique à 2h du matin |
| ❌ Risque d'oubli | ✅ Toujours exécuté |
| ❌ Maintenance manuelle | ✅ Nettoyage automatique |
| ❌ Temps perdu | ✅ Vous dormez tranquille |

---

## 📝 Format d'une ligne Cron

```
┌───────────── minute (0 - 59)
│ ┌───────────── heure (0 - 23)
│ │ ┌───────────── jour du mois (1 - 31)
│ │ │ ┌───────────── mois (1 - 12)
│ │ │ │ ┌───────────── jour de la semaine (0 - 7, dimanche = 0 ou 7)
│ │ │ │ │
│ │ │ │ │
* * * * * commande-à-exécuter
```

### Symboles spéciaux

| Symbole | Signification | Exemple |
|---------|---------------|---------|
| `*` | Toutes les valeurs | `* * * * *` = chaque minute |
| `,` | Liste de valeurs | `0 8,12,18 * * *` = 8h, 12h et 18h |
| `-` | Intervalle | `0 9-17 * * *` = de 9h à 17h |
| `/` | Pas | `*/15 * * * *` = toutes les 15 minutes |

### Exemples de planification

| Expression | Quand ça s'exécute |
|------------|-------------------|
| `0 2 * * *` | Tous les jours à 2h00 |
| `30 3 * * *` | Tous les jours à 3h30 |
| `0 */6 * * *` | Toutes les 6 heures |
| `0 0 * * 0` | Tous les dimanches à minuit |
| `0 0 1 * *` | Le 1er de chaque mois à minuit |
| `*/10 * * * *` | Toutes les 10 minutes |
| `0 9-17 * * 1-5` | Toutes les heures de 9h à 17h, lundi au vendredi |

---

## 🚀 Installation et configuration

### 1. Se connecter au serveur

```bash
ssh ubuntu@votre-serveur
```

### 2. Vérifier que Cron est installé

```bash
# Vérifier le service
sudo systemctl status cron

# Si non installé (rare sur Ubuntu/Debian)
sudo apt-get update
sudo apt-get install cron
sudo systemctl enable cron
sudo systemctl start cron
```

### 3. Éditer votre crontab

```bash
# Ouvrir l'éditeur de cron pour l'utilisateur actuel
crontab -e

# Si c'est la première fois, choisissez nano (option 1)
```

### 4. Ajouter vos tâches

Ajoutez les lignes suivantes dans l'éditeur :

```bash
# ============================================
# SAUVEGARDES AUTOMATIQUES - API AUDACE
# ============================================

# Sauvegarde quotidienne de la base de données à 2h du matin
0 2 * * * /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code/scripts/backup_db.sh >> /var/log/backup_db.log 2>&1

# Nettoyer les sauvegardes de plus de 30 jours à 3h du matin
0 3 * * * find /home/ubuntu/backups -name "audace_db_*.sql.gz" -mtime +30 -delete

# Vérifier la santé de l'API toutes les heures
0 * * * * curl -f https://api.cloud.audace.ovh/ || echo "API DOWN at $(date)" >> /var/log/api_health.log
```

### 5. Sauvegarder et quitter

- **Nano** : `Ctrl + X`, puis `Y`, puis `Enter`
- **Vim** : `:wq` puis `Enter`

### 6. Vérifier la configuration

```bash
# Lister vos tâches cron
crontab -l

# Vérifier les logs système de cron
sudo tail -f /var/log/syslog | grep CRON
```

---

## 🎯 Exemples pour votre projet

### Configuration complète recommandée

```bash
# ============================================
# SAUVEGARDES ET MAINTENANCE - API AUDACE
# ============================================

# Sauvegarde de la base de données
# Tous les jours à 2h du matin
0 2 * * * /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code/scripts/backup_db.sh >> /var/log/backup_db.log 2>&1

# Nettoyage des anciennes sauvegardes (>30 jours)
# Tous les jours à 3h du matin
0 3 * * * find /home/ubuntu/backups -name "audace_db_*.sql.gz" -mtime +30 -delete >> /var/log/cleanup.log 2>&1

# Nettoyage des logs Docker (>7 jours)
# Tous les dimanches à 4h du matin
0 4 * * 0 docker system prune -f --filter "until=168h" >> /var/log/docker_cleanup.log 2>&1

# Vérification de santé de l'API
# Toutes les heures
0 * * * * curl -f https://api.cloud.audace.ovh/ || echo "API DOWN at $(date)" >> /var/log/api_health.log 2>&1

# Vérification de l'espace disque
# Tous les jours à 8h du matin
0 8 * * * df -h | grep -E '^/dev/' | awk '{if ($5+0 > 80) print "WARNING: Disk usage above 80% on "$1": "$5}' >> /var/log/disk_usage.log 2>&1

# Redémarrage optionnel de l'API (si problèmes de mémoire)
# Tous les lundis à 5h du matin (commenté par défaut)
# 0 5 * * 1 docker restart audace_api >> /var/log/api_restart.log 2>&1
```

### Exemples de fréquences alternatives

```bash
# Sauvegarde toutes les 6 heures (plus fréquent)
0 */6 * * * /path/to/scripts/backup_db.sh

# Sauvegarde toutes les 12 heures
0 0,12 * * * /path/to/scripts/backup_db.sh

# Sauvegarde hebdomadaire (tous les lundis)
0 2 * * 1 /path/to/scripts/backup_db.sh

# Sauvegarde mensuelle (le 1er du mois)
0 2 1 * * /path/to/scripts/backup_db.sh
```

---

## 🛠️ Gestion des tâches Cron

### Commandes de base

```bash
# Lister toutes vos tâches cron
crontab -l

# Éditer vos tâches cron
crontab -e

# Supprimer toutes vos tâches cron (ATTENTION!)
crontab -r

# Éditer les tâches d'un autre utilisateur (root uniquement)
sudo crontab -u username -e

# Lister les tâches système (root)
sudo cat /etc/crontab
```

### Désactiver temporairement une tâche

```bash
# Ouvrir l'éditeur
crontab -e

# Commenter la ligne avec #
# 0 2 * * * /path/to/script.sh

# Sauvegarder
```

### Activer/Désactiver le service Cron

```bash
# Arrêter le service cron
sudo systemctl stop cron

# Démarrer le service cron
sudo systemctl start cron

# Redémarrer le service cron
sudo systemctl restart cron

# Vérifier le statut
sudo systemctl status cron
```

---

## 📊 Surveillance et logs

### Vérifier l'exécution des tâches

```bash
# Voir les exécutions récentes de cron
sudo grep CRON /var/log/syslog | tail -20

# Voir les logs de votre script de sauvegarde
tail -f /var/log/backup_db.log

# Voir les erreurs
grep -i error /var/log/backup_db.log
```

### Créer un système d'alerte par email

```bash
# Installer mailutils (si pas déjà installé)
sudo apt-get install mailutils

# Ajouter MAILTO au début de votre crontab
crontab -e

# Ajouter cette ligne en haut :
MAILTO=votre.email@example.com

# Maintenant, en cas d'erreur, vous recevrez un email
0 2 * * * /path/to/script.sh
```

### Script de monitoring

Créez `/home/ubuntu/check_backups.sh` :

```bash
#!/bin/bash

BACKUP_DIR="/home/ubuntu/backups"
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/audace_db_*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ALERT: Aucune sauvegarde trouvée!"
    exit 1
fi

# Vérifier que la dernière sauvegarde a moins de 25 heures
BACKUP_AGE=$(find "$LATEST_BACKUP" -mtime +1)
if [ -n "$BACKUP_AGE" ]; then
    echo "ALERT: La dernière sauvegarde a plus de 24h!"
    exit 1
fi

echo "OK: Dernière sauvegarde: $LATEST_BACKUP"
```

Ajoutez au cron :

```bash
# Vérifier que les sauvegardes fonctionnent
0 9 * * * /home/ubuntu/check_backups.sh || echo "BACKUP FAILED!" | mail -s "Alert Backup" admin@example.com
```

---

## 🔧 Dépannage

### Les tâches ne s'exécutent pas

#### 1. Vérifier que Cron tourne

```bash
sudo systemctl status cron

# Si arrêté, le démarrer
sudo systemctl start cron
```

#### 2. Vérifier la syntaxe de votre crontab

```bash
# Tester la syntaxe avec crontab-validator (en ligne)
# https://crontab.guru/

# Vérifier les logs d'erreurs
sudo tail -f /var/log/syslog | grep CRON
```

#### 3. Vérifier les permissions

```bash
# Le script doit être exécutable
chmod +x /path/to/script.sh

# Vérifier les permissions
ls -l /path/to/script.sh
```

#### 4. Tester le script manuellement

```bash
# Exécuter le script comme Cron le ferait
/path/to/script.sh

# Vérifier les erreurs
echo $?  # 0 = succès, autre = erreur
```

#### 5. Utiliser des chemins absolus

```bash
# ❌ Mauvais (chemin relatif)
0 2 * * * ./scripts/backup.sh

# ✅ Bon (chemin absolu)
0 2 * * * /home/ubuntu/scripts/backup.sh
```

### Les logs ne s'écrivent pas

```bash
# Créer le fichier de log avec les bonnes permissions
sudo touch /var/log/backup_db.log
sudo chown $USER:$USER /var/log/backup_db.log

# Ou utiliser un dossier dans votre home
mkdir -p ~/logs
0 2 * * * /path/to/script.sh >> ~/logs/backup.log 2>&1
```

### Erreur "command not found"

Cron utilise un PATH limité. Ajoutez le PATH au début de votre crontab :

```bash
crontab -e

# Ajouter en haut :
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Puis vos tâches
0 2 * * * /path/to/script.sh
```

### Déboguer une tâche cron

```bash
# Créer un script de test
#!/bin/bash
echo "Script exécuté à $(date)" >> /tmp/cron_test.log
echo "PATH=$PATH" >> /tmp/cron_test.log
echo "USER=$USER" >> /tmp/cron_test.log
env >> /tmp/cron_test.log

# Ajouter au cron
* * * * * /tmp/test_cron.sh

# Vérifier après 1 minute
cat /tmp/cron_test.log
```

---

## 📚 Ressources et outils

### Outils en ligne

- **[Crontab.guru](https://crontab.guru/)** - Générateur et validateur de syntaxe Cron
- **[Crontab Generator](https://crontab-generator.org/)** - Interface graphique pour créer des crons

### Commandes utiles

```bash
# Tester une expression cron
# Installer cronic
sudo apt-get install cronic

# Logs en temps réel
sudo tail -f /var/log/syslog | grep --line-buffered CRON

# Voir toutes les tâches cron du système
for user in $(cut -f1 -d: /etc/passwd); do echo "=== $user ==="; sudo crontab -u $user -l 2>/dev/null; done
```

---

## ✅ Checklist de mise en place

- [ ] Service Cron installé et actif
- [ ] Scripts de sauvegarde testés manuellement
- [ ] Permissions correctes sur les scripts (chmod +x)
- [ ] Dossiers de logs créés
- [ ] Tâches cron ajoutées avec `crontab -e`
- [ ] Chemins absolus utilisés dans les commandes
- [ ] Redirection des logs configurée (`>> fichier.log 2>&1`)
- [ ] Alertes email configurées (optionnel)
- [ ] Première exécution vérifiée dans les logs
- [ ] Documentation conservée pour référence future

---

## 📞 Exemples de commandes rapides

```bash
# Installer et configurer en une fois
sudo systemctl enable cron && sudo systemctl start cron && crontab -e

# Vérifier que tout fonctionne
crontab -l && sudo systemctl status cron

# Voir les dernières exécutions
sudo grep CRON /var/log/syslog | tail -10

# Tester votre script de sauvegarde maintenant
/etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code/scripts/backup_db.sh
```

---

**Dernière mise à jour :** 10 décembre 2025  
**Recommandation :** Configurez au minimum la sauvegarde quotidienne et le nettoyage automatique.
