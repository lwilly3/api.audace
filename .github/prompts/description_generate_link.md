Backend Route Creation (API):

Create a new API endpoint (e.g., /auth/generate-invite) on your backend.
This endpoint will:
Receive a request (likely a POST) containing the email address (optional) and any other relevant user data.
Generate a unique token or code.
Store this token in your database, along with the user's email (if provided) and an expiration timestamp.
Return the generated token.
Frontend Changes:

Create a new component (src/components/auth/GenerateInviteLink.tsx) to handle the request for generating the invite link.
This component will call the new API endpoint (/auth/generate-invite).
Display the generated link to the user.
Add a button or UI element in the user management section (e.g., src/pages/users/UserList.tsx) to trigger the link generation.
Add a new route for temporary user creation

Create a new page (src/pages/auth/SignupWithInvite.tsx) to handle the user signup process using the temporary link.
This page will:
Parse the token from the URL.
Verify the token against your database.
Display a signup form to the user.
Upon form submission, create the user account and store additional user data in your database.
Database Changes:

Create a new table or collection in your database to store the temporary invite tokens, associated user emails, and expiration timestamps.
Security:

Implement proper error handling in the API endpoint and frontend components.
Add validation to the signup form to ensure data integrity.
Use secure coding practices to prevent vulnerabilities such as SQL injection and cross-site scripting (XSS).
Ensure that the temporary links expire correctly and cannot be reused.
Persistence of Form Fields in CreateShowPlan:

Modify the CreateShowPlan component (src/pages/CreateShowPlan.tsx) to persist the form data (title, type, date, time, description) in the component's state using useState.
Update the handleAddSegment function to pass the current form data to the new segment, so it can be restored when the user returns to the segment list.
Testing:

Test the entire flow, including link generation, user signup, and data storage.
Ensure that the temporary links expire correctly and cannot be reused.
Test that the form fields in CreateShowPlan persist correctly after adding new segments.

## Temporary Invite Links

### Backend (routeur/auth.py)
- Route : POST `/auth/invite`
- Statut : 201 Created
- Corps de requête : `{ "email": string }`
- Réponse 201 :
  ```json
  {
    "token": "uuid-1234-abcd",         // jeton unique
    "expires_at": "2025-05-09T12:00:00Z" // date ISO d'expiration
  }
  ```
- Erreurs possibles :
  - 400 Bad Request : absence ou format d'email invalide
  - 500 Internal Server Error : problème interne serveur

- Route : GET `/auth/invite/validate`
- Statut : 200 OK
- Query param : `token` (string)
- Réponse 200 :
  ```json
  {
    "valid": true,                 // vrai si non expiré et non utilisé
    "email": "invitee@example.com" // email associé au token
  }
  ```
- Erreurs :
  - 400 Bad Request : token manquant
  - 404 Not Found : token non existant, déjà utilisé ou expiré

- Route : POST `/auth/signup-with-invite`
- Statut : 201 Created
- Corps de requête :
  ```json
  {
    "token": "uuid-1234-abcd",
    "username": "invitee",          // nom d'utilisateur unique
    "email": "invitee@example.com", // email valide
    "password": "Secret123!",       // mot de passe sécurisé
    "name": "Prénom",               // prénom de l'utilisateur
    "family_name": "Nomfamille",    // nom de famille
    "phone_number": "+33612345678", // numéro de téléphone
  }
  ```
- Réponse 201 :
  ```json
  {
    "id": 42,
    "email": "invitee@example.com",
    "username": "invitee",
    "created_at": "2025-05-02T10:15:00Z",
    "password": "Secret123!",       // mot de passe sécurisé
    "name": "Prénom",               // prénom de l'utilisateur
    "family_name": "Nomfamille",    // nom de famille
    "phone_number": "+33612345678", // numéro de téléphone
    
  }
  ```
- Erreurs :
  - 400 Bad Request : données manquantes ou invalides
  - 401 Unauthorized : token invalide ou expiré
  - 409 Conflict : email ou username déjà existant
  - 410 Gone : token utilisé ou périmé

### Frontend (src/components/auth/GenerateInviteLink.tsx)
- Importer les hooks React (`useState`, `useEffect`) et un client HTTP (`axios` ou `fetch`).
- États à gérer :
  * `email: string` – modèle du champ email.
  * `loading: boolean` – indicateur de chargement pendant l’appel.
  * `inviteLink: string | null` – lien généré ou null.
  * `expiresAt: string | null` – date d’expiration ISO pour affichage.
  * `error: string | null` – message d’erreur utilisateur.
- Formulaire :
  1. Champ email avec validation en `onChange` (regex simple + non vide).
  2. Bouton « Générer le lien » désactivé si `loading` ou email invalide.
- Fonction `handleGenerate` :
  ```tsx
  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/auth/invite', { email });
      const { token, expires_at } = response.data;
      setInviteLink(`${window.location.origin}/signup/${token}`);
      setExpiresAt(expires_at);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération du lien');
    } finally {
      setLoading(false);
    }
  }
  ```
- UI à afficher :
  * Spinner ou indicator lorsque `loading === true`.
  * En cas de succès (`inviteLink` non null) :
    - Afficher le lien cliquable.
    - Bouton « Copier » avec `navigator.clipboard.writeText(inviteLink)` et feedback visuel (« Lien copié !»).
    - Texte « Expire le: {new Date(expiresAt).toLocaleString()} ».
  * En cas d’erreur (`error` non null) : afficher `error` en rouge.
- Réinitialisation :
  * Si l’email change, nettoyer `inviteLink`, `expiresAt` et `error`.
- Intégration :
  * Render ce composant dans la page d’administration (`src/pages/users/UserList.tsx` ou `AdminDashboard`).
  * Passer un prop `onInviteSent(token: string)` si besoin de notifier le parent.

### Signup avec invite (src/pages/auth/SignupWithInvite.tsx)
- Importer les hooks React (`useState`, `useEffect`) et router (`useParams`, `useNavigate`) ainsi qu’un client HTTP (`axios` ou `fetch`).
- États à gérer :
  * `token: string` – extrait de l’URL (`useParams`).
  * `loading: boolean` – pour l’appel de validation et de création.
  * `error: string | null` – message d’erreur global.
  * `valid: boolean` – si le token est valide (initialement false).
  * `email: string` – obtenu via la validation du token (lecture seule).
  * `form: { username: string; password: string; name: string; family_name: string; phone_number?: string; profilePicture?: string }` – données saisies.
- `useEffect` au montage :
  ```tsx
  useEffect(() => {
    async function validate() {
      setLoading(true);
      try {
        const res = await axios.get(`/auth/invite/validate?token=${token}`);
        setEmail(res.data.email);
        setValid(true);
      } catch (err) {
        setError(err.response?.data?.detail || 'Lien invalide ou expiré');
      } finally {
        setLoading(false);
      }
    }
    validate();
  }, [token]);
  ```
- Formulaire de signup (affiché si `valid === true`) :
  1. Champs : username, password, name, family_name, phone_number, profilePicture (URL). Tous obligatoires sauf les deux derniers.
  2. Validation simple : non vide pour username/password, format URL pour avatar.
- Fonction `handleSignup` :
  ```tsx
  async function handleSignup() {
    setLoading(true);
    setError(null);
    try {
      const payload = { token, email, ...form };
      await axios.post('/auth/signup-with-invite', payload);
      navigate('/login', { state: { message: 'Compte créé avec succès. Veuillez vous connecter.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création de compte');
    } finally {
      setLoading(false);
    }
  }
  ```
- UI :
  * Si `loading`, afficher un spinner.
  * Si `error`, afficher le message en rouge.
  * Si `!valid && !loading`, afficher un message « Lien invalide ou expiré ».
  * Formulaire : boutons « Valider » désactivé tant que `loading` ou validation échoue.
  * Après succès, rediriger vers la page de login avec un toast ou message.
- Intégration :
  * Déclarer la route React : `<Route path="/signup/:token" element={<SignupWithInvite />} />`.
  * Ajouter de la navigation conditionnelle pour `token` manquant.

### Database Changes
- Nouvelle table `invite_tokens` :
  - `token` (PK, string)
  - `email` (string)
  - `expires_at` (timestamp)
  - `used` (bool)