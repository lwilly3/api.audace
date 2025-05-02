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
- Formulaire pour saisir l'email destinataire
- Appel POST `/auth/invite` avec `{ email }`
- Afficher le lien généré ou message de confirmation

### Signup avec invite (src/pages/auth/SignupWithInvite.tsx)
- Extraire `token` depuis l'URL
- Vérifier côté backend via GET `/auth/invite/validate?token=${token}`
- Si valide : afficher formulaire de création de compte
- À la soumission : POST `/auth/signup-with-invite` `{ token, username, password, ... }`

### Database Changes
- Nouvelle table `invite_tokens` :
  - `token` (PK, string)
  - `email` (string)
  - `expires_at` (timestamp)
  - `used` (bool)