# 🔔 Routes Notifications (`/notifications`)

> Gestion des notifications utilisateurs.

---

## 📋 Endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/notifications/` | ✅ | Notifications de l'utilisateur |
| `GET` | `/notifications/{id}` | ✅ | Détails d'une notification |
| `POST` | `/notifications/` | ✅ | Envoyer une notification |
| `PUT` | `/notifications/{id}` | ✅ | Modifier une notification |
| `DELETE` | `/notifications/{id}` | ✅ | Supprimer une notification |

---

## 📦 Schémas de Données

### NotificationRead
```typescript
/** GET /notifications/{id} */
interface NotificationRead {
  id: number;
  user_id: number;
  message: string;
  created_at: string;   // ISO 8601
  read: boolean;
}
```

### NotificationCreate
```typescript
/** POST /notifications/ - Création */
interface NotificationCreate {
  user_id: number;
  message: string;
  read?: boolean;       // défaut: false
}
```

### NotificationUpdate
```typescript
/** PUT /notifications/{id} */
interface NotificationUpdate {
  title?: string;
  message?: string;
  read?: boolean;
}
```

---

## 🔄 Exemples d'Utilisation

### Lister les notifications
```typescript
const notifications: NotificationRead[] = await fetch('/notifications/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Exemple de réponse
[
  {
    "id": 1,
    "user_id": 123,
    "message": "Votre show 'Journal du Matin' a été approuvé",
    "created_at": "2025-01-15T10:00:00Z",
    "read": false
  },
  {
    "id": 2,
    "user_id": 123,
    "message": "Nouveau commentaire sur votre émission",
    "created_at": "2025-01-14T15:30:00Z",
    "read": true
  }
]
```

### Créer une notification
```typescript
const notification: NotificationRead = await fetch('/notifications/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: 456,
    message: "Vous avez été ajouté comme présentateur sur 'Culture Express'"
  })
}).then(r => r.json());
```

### Marquer comme lue
```typescript
await fetch('/notifications/123', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ read: true })
});
```

### Marquer toutes comme lues
```typescript
// Obtenir toutes les notifications non lues
const unread = notifications.filter(n => !n.read);

// Les marquer comme lues
await Promise.all(
  unread.map(n => 
    fetch(`/notifications/${n.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ read: true })
    })
  )
);
```

### Supprimer une notification
```typescript
await fetch('/notifications/123', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### Obtenir les notifications d'un utilisateur (via Users)
```typescript
// Alternative : via la route users
const userNotifications = await fetch('/users/users/456/notifications', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

---

## 🔐 Permissions Requises

| Action | Permission |
|--------|------------|
| Voir les notifications | `can_view_notifications` |
| Gérer les notifications | `can_manage_notifications` |

---

## 💡 Cas d'Usage Frontend

### Badge de notifications non lues
```typescript
function NotificationBadge() {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    fetch('/notifications/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(notifications => {
        const unreadCount = notifications.filter(n => !n.read).length;
        setCount(unreadCount);
      });
  }, []);
  
  return count > 0 ? <span className="badge">{count}</span> : null;
}
```

### Polling des notifications
```typescript
// Vérifier les nouvelles notifications toutes les 30 secondes
useEffect(() => {
  const interval = setInterval(async () => {
    const notifications = await fetch('/notifications/', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    const newUnread = notifications.filter(n => !n.read);
    if (newUnread.length > 0) {
      // Afficher une notification toast
      showToast(`${newUnread.length} nouvelle(s) notification(s)`);
    }
  }, 30000);
  
  return () => clearInterval(interval);
}, []);
```

---

## ⚠️ Points d'Attention

1. **Authentification requise** : Toutes les routes nécessitent un token JWT
2. **Pas de websocket** : L'API utilise du polling, pas de push en temps réel
3. **Suppression définitive** : DELETE supprime vraiment la notification
4. **Route alternative** : `/users/users/{id}/notifications` donne aussi les notifications d'un user
