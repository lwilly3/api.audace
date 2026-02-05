# ⚙️ Routes Setup, Version & Dashboard (`/setup`, `/version`, `/dashbord`)

> Configuration initiale, informations version et tableau de bord.

---

## 📋 Endpoints Setup (`/setup`)

> ⚠️ Routes accessibles **SANS authentification** uniquement si aucun admin n'existe.

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/setup/check-admin` | ❌ | Vérifier si un admin existe |
| `POST` | `/setup/create-admin` | ❌* | Créer le premier admin |
| `GET` | `/setup/env-check` | ❌ | Vérifier variables d'environnement |
| `GET` | `/setup/status` | ❌ | Statut complet du système |

> *⚠️ `/setup/create-admin` ne fonctionne QUE si aucun admin n'existe

## 📋 Endpoints Version (`/version`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/version/` | ❌ | Infos complètes version |
| `GET` | `/version/current` | ❌ | Version actuelle uniquement |
| `GET` | `/version/breaking-changes` | ❌ | Liste des breaking changes |
| `GET` | `/version/health` | ❌ | Health check avec version |
| `GET` | `/version/compatibility/{client_version}` | ❌ | Vérifier compatibilité client |

## 📋 Endpoints Dashboard (`/dashbord`)

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/dashbord/` | ✅ | Données du tableau de bord |

---

## 📦 Schémas de Données

### Setup
```typescript
/** GET /setup/check-admin */
interface CheckAdminResponse {
  admin_exists: boolean;
  setup_needed: boolean;
  admin_count: number;
  message: string;
}

/** GET /setup/status */
interface SystemStatusResponse {
  system_status: "ready" | "needs_setup";
  database_connected: boolean;
  admin_role_exists: boolean;
  admin_count: number;
  total_users: number;
  setup_route_active: boolean;
  message: string;
}

/** GET /setup/env-check */
interface EnvCheckResponse {
  all_set: boolean;
  missing: string[];
  environment: "development" | "production";
}

/** POST /setup/create-admin */
interface SetupAdminRequest {
  username: string;
  email: string;
  password: string;
  name?: string;         // défaut: "Administrateur"
  family_name?: string;  // défaut: "Système"
}
```

### Version
```typescript
/** GET /version/ */
interface VersionInfo {
  version: string;                // "2.5.0"
  release_date: string;
  api_version: string;            // "v1"
  breaking_changes: string[];
  docs_url: string;
}

/** GET /version/current */
interface VersionCurrent {
  version: string;
}

/** GET /version/breaking-changes */
interface BreakingChangesResponse {
  breaking_changes: Record<string, string[]>;
  documentation: string;
  changelog: string;
}

/** GET /version/health */
interface HealthCheckResponse {
  status: "healthy" | "unhealthy";
  version: string;
  api_version: string;
  timestamp: string;
}

/** GET /version/compatibility/{client_version} */
interface CompatibilityResponse {
  client_version: string;
  server_version: string;
  compatible: boolean;
  breaking_changes_since: string[];
  recommendation: string;
}
```

### Dashboard
```typescript
/** GET /dashbord/ */
interface DashboardResponse {
  total_users: number;
  total_shows: number;
  total_emissions: number;
  total_presenters: number;
  total_guests: number;
  shows_by_status: Record<ShowStatus, number>;
  recent_shows: ShowOut[];
  upcoming_shows: ShowOut[];
}
```

---

## 🔄 Exemples d'Utilisation

### Flow de Configuration Initiale
```typescript
// 1. Vérifier si le système a besoin d'être configuré
const checkResult = await fetch('/setup/check-admin').then(r => r.json());

if (checkResult.setup_needed) {
  // 2. Vérifier les variables d'environnement
  const envCheck = await fetch('/setup/env-check').then(r => r.json());
  
  if (!envCheck.all_set) {
    console.error('Variables manquantes:', envCheck.missing);
    // Afficher un message d'erreur
    return;
  }
  
  // 3. Créer le premier admin
  const admin = await fetch('/setup/create-admin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'admin',
      email: 'admin@radio.com',
      password: 'securePassword123',
      name: 'Admin',
      family_name: 'Principal'
    })
  }).then(r => r.json());
  
  // 4. Rediriger vers le login
  window.location.href = '/login';
} else {
  // Système déjà configuré, aller au login
  window.location.href = '/login';
}
```

### Vérifier le statut du système
```typescript
const status = await fetch('/setup/status').then(r => r.json());

// Exemple de réponse
{
  "system_status": "ready",
  "database_connected": true,
  "admin_role_exists": true,
  "admin_count": 2,
  "total_users": 25,
  "setup_route_active": false,
  "message": "Système configuré et opérationnel"
}
```

### Health Check (pour monitoring)
```typescript
// Utilisé par les load balancers, Kubernetes, etc.
const health = await fetch('/version/health').then(r => r.json());

if (health.status !== 'healthy') {
  // Alerter l'équipe ops
  sendAlert('API unhealthy!', health);
}
```

### Vérifier la compatibilité client
```typescript
const CLIENT_VERSION = '2.3.0';

const compat = await fetch(`/version/compatibility/${CLIENT_VERSION}`)
  .then(r => r.json());

if (!compat.compatible) {
  // Afficher un message de mise à jour
  showUpdateModal({
    message: compat.recommendation,
    breakingChanges: compat.breaking_changes_since
  });
}
```

### Afficher le dashboard
```typescript
const dashboard = await fetch('/dashbord/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
{
  "total_users": 25,
  "total_shows": 150,
  "total_emissions": 12,
  "total_presenters": 8,
  "total_guests": 45,
  "shows_by_status": {
    "En préparation": 15,
    "Planifié": 30,
    "En direct": 2,
    "Terminé": 95,
    "Annulé": 5,
    "Archivé": 3
  },
  "recent_shows": [...],
  "upcoming_shows": [...]
}
```

---

## 💡 Cas d'Usage Frontend

### Page de Setup Initial
```typescript
function SetupPage() {
  const [step, setStep] = useState<'check' | 'env' | 'create' | 'done'>('check');
  
  useEffect(() => {
    // Vérifier si setup nécessaire
    fetch('/setup/check-admin')
      .then(r => r.json())
      .then(data => {
        if (!data.setup_needed) {
          navigate('/login');
        } else {
          setStep('env');
        }
      });
  }, []);
  
  // ... render selon l'étape
}
```

### Header avec Version
```typescript
function AppHeader() {
  const [version, setVersion] = useState<string>('');
  
  useEffect(() => {
    fetch('/version/current')
      .then(r => r.json())
      .then(data => setVersion(data.version));
  }, []);
  
  return (
    <header>
      <h1>Radio Manager</h1>
      <span className="version">v{version}</span>
    </header>
  );
}
```

---

## ⚠️ Points d'Attention

1. **Setup unique** : `/setup/create-admin` ne fonctionne qu'une fois (si aucun admin)
2. **Typo "dashbord"** : L'URL est `/dashbord/` (sans le 'a' de dashboard)
3. **Health check public** : `/version/health` est conçu pour être appelé sans auth
4. **Compatibilité semver** : L'API utilise le versioning sémantique (MAJOR.MINOR.PATCH)
