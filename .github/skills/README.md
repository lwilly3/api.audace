# 🎯 GitHub Skills - api.audace

> **Index central** des skills pour le développement et la maintenance de l'API radio Hapson.

---

## 📋 Vue d'ensemble

Ces skills guident les développeurs et agents IA pour :
- ✅ **Respecter** l'architecture existante
- 🛡️ **Protéger** le code en production
- 📏 **Standardiser** les pratiques
- 🚀 **Accélérer** l'onboarding

---

## 🏆 Skills par Priorité

### 🔴 Critiques (Obligatoires)

| Skill | Description | Quand l'utiliser |
|-------|-------------|------------------|
| [architecture-guardian](architecture-guardian/skill.md) | Protection de l'architecture globale | **Toujours** - À lire en premier |
| [security-rules](security-rules/skill.md) | Authentification, permissions, sécurité | Toute modification auth/permissions |
| [refactor-safe](refactor-safe/skill.md) | Modifications sûres du code existant | Refactoring, renaming, migrations |

### 🟠 Importants (Fortement recommandés)

| Skill | Description | Quand l'utiliser |
|-------|-------------|------------------|
| [endpoint-creator](endpoint-creator/skill.md) | Création de routes FastAPI | Nouveau endpoint |
| [model-generator](model-generator/skill.md) | Modèles SQLAlchemy + Pydantic | Nouveau modèle/table |
| [migration-helper](migration-helper/skill.md) | Migrations Alembic | Modification BDD |
| [test-enforcer](test-enforcer/skill.md) | Standards de tests pytest | Écriture de tests |

### 🟡 Recommandés

| Skill | Description | Quand l'utiliser |
|-------|-------------|------------------|
| [error-handling](error-handling/skill.md) | Gestion des erreurs/exceptions | Traitement d'erreurs |
| [logging-standard](logging-standard/skill.md) | Standards de logging | Ajout de logs |
| [service-pattern](service-pattern/skill.md) | Séparation logique métier | Logique complexe |
| [api-documentation](api-documentation/skill.md) | Documentation OpenAPI/Swagger | Documentation API |

### 🟢 Spécialisés

| Skill | Description | Quand l'utiliser |
|-------|-------------|------------------|
| [domain-radio-rules](domain-radio-rules/skill.md) | Règles métier radio | Émissions, Shows, Segments |

---

## 🚀 Guide de Démarrage Rapide

### Pour un Nouveau Développeur

1. **Lire** [architecture-guardian](architecture-guardian/skill.md) (5 min)
2. **Comprendre** la structure du projet
3. **Consulter** le skill correspondant à votre tâche

### Pour un Agent IA

```
Avant toute modification :
1. Charger architecture-guardian/skill.md
2. Identifier le skill correspondant à la tâche
3. Suivre les règles et interdictions
4. Valider avec la checklist
```

---

## 📁 Structure des Skills

```
.github/skills/
├── README.md                      # Ce fichier (index)
├── architecture-guardian/
│   ├── skill.md                   # Règles d'architecture
│   └── validation/
│       └── checklist.md           # Checklist de validation
├── endpoint-creator/
│   └── skill.md                   # Guide création endpoints
├── model-generator/
│   └── skill.md                   # Guide création modèles
├── service-pattern/
│   └── skill.md                   # Séparation logique métier
├── test-enforcer/
│   └── skill.md                   # Standards de tests
├── security-rules/
│   └── skill.md                   # Règles de sécurité
├── refactor-safe/
│   └── skill.md                   # Refactoring sécurisé
├── migration-helper/
│   └── skill.md                   # Migrations Alembic
├── error-handling/
│   └── skill.md                   # Gestion des erreurs
├── logging-standard/
│   └── skill.md                   # Standards de logging
├── api-documentation/
│   └── skill.md                   # Documentation OpenAPI
└── domain-radio-rules/
    └── skill.md                   # Règles métier radio
```

---

## 📊 Matrice Skill × Tâche

| Tâche | Skills à consulter |
|-------|-------------------|
| Nouveau endpoint | architecture-guardian → endpoint-creator → test-enforcer |
| Nouvelle table | architecture-guardian → model-generator → migration-helper |
| Modifier modèle | refactor-safe → model-generator → migration-helper |
| Ajouter permission | security-rules → migration-helper |
| Corriger bug | refactor-safe → test-enforcer |
| Refactoring | refactor-safe → architecture-guardian |
| Logique métier | service-pattern → domain-radio-rules |
| Documentation | api-documentation |

---

## ✅ Checklist Globale

Avant tout commit, vérifier :

- [ ] Architecture respectée (architecture-guardian)
- [ ] Tests écrits et passants (test-enforcer)
- [ ] Pas de données sensibles exposées (security-rules)
- [ ] Migrations testées up/down (migration-helper)
- [ ] Logs appropriés (logging-standard)
- [ ] Documentation à jour (api-documentation)

---

## 🔧 Commandes Utiles

```bash
# Vérifier les tests
pytest tests/ -v

# Vérifier la couverture
pytest tests/ --cov=app --cov-report=term-missing

# Vérifier les migrations
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# Lancer le serveur
uvicorn maintest:app --reload

# Formater le code
black .
isort .
```

---

## 📚 Documentation Complémentaire

- [AGENT.md](../../AGENT.md) - Instructions pour agents IA
- [docs/](../../docs/) - Documentation technique
- [README.md](../../README.md) - Documentation projet

---

## 🤝 Contribution aux Skills

Pour améliorer ou ajouter un skill :

1. Créer un dossier `.github/skills/<nom-du-skill>/`
2. Ajouter un `skill.md` avec les sections obligatoires :
   - 📋 Contexte du Projet
   - 🎯 Objectif du Skill
   - ✅ Règles Obligatoires
   - 🚫 Interdictions Explicites
   - 📝 Exemples Concrets
   - ✅ Checklist de Validation
3. Mettre à jour ce README
4. Tester avec un cas d'usage réel
