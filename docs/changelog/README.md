# Archives du Changelog

Ce répertoire contient les archives des versions précédentes du CHANGELOG, organisées par année.

## 📁 Structure

```
docs/changelog/
├── README.md              # Ce fichier
├── CHANGELOG-2026.md      # Versions de 2026
├── CHANGELOG-2025.md      # Versions de 2025
└── ...
```

## 🤖 Gestion Automatique

Le CHANGELOG principal est automatiquement archivé lorsqu'il dépasse **300 lignes**.

### Processus d'archivage

1. Le script `scripts/archive_changelog.py` détecte quand le fichier principal dépasse 300 lignes
2. Il extrait toutes les versions des années précédentes
3. Il crée/met à jour les fichiers d'archive par année
4. Il met à jour le CHANGELOG principal pour ne garder que l'année en cours
5. Il ajoute des liens vers les archives

### Commandes

```bash
# Vérifier si archivage nécessaire (simulation)
python scripts/archive_changelog.py --dry-run

# Effectuer l'archivage
python scripts/archive_changelog.py
```

## 📚 Consulter les archives

- Retour au [CHANGELOG principal](../../CHANGELOG.md)
- [Versions 2025](CHANGELOG-2025.md)

## 🎯 Pourquoi archiver ?

1. **Performance** : Garder le CHANGELOG principal léger et rapide à charger
2. **Lisibilité** : Faciliter la consultation des changements récents
3. **Organisation** : Séparer clairement les versions par période
4. **Historique** : Préserver l'historique complet de manière organisée
5. **Agents IA** : Éviter les contextes trop longs lors de l'analyse

## 📝 Format des archives

Chaque fichier d'archive suit ce format :

```markdown
# Changelog {ANNÉE}

Archive des versions publiées en {ANNÉE}.

Retour au [CHANGELOG principal](../../CHANGELOG.md)

---

## [X.Y.Z] - YYYY-MM-DD

### Ajouté
- ...

### Modifié
- ...

---

_Archive créée le DD mois YYYY_
```

## 🔄 Mise à jour automatique

Les agents IA sont configurés pour :
- Vérifier la taille du CHANGELOG après chaque ajout significatif
- Déclencher l'archivage automatiquement si nécessaire
- Maintenir les liens à jour

## 💡 Bonnes Pratiques

- ✅ Ne jamais modifier manuellement les archives (elles sont générées automatiquement)
- ✅ Toujours ajouter les nouvelles entrées dans le CHANGELOG principal
- ✅ Laisser le script gérer l'archivage automatiquement
- ✅ Vérifier les liens après archivage
