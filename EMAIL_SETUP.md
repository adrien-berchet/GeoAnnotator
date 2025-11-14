# Configuration Email pour Docker

Ce guide explique comment changer facilement le backend email sans reconstruire l'image Docker.

## 🚀 Changement Rapide du Backend Email

Toute la configuration se fait dans le fichier `.env` à la racine du projet. **Aucun rebuild Docker n'est nécessaire**, il suffit de redémarrer les conteneurs.

### Option 1: Console Backend (par défaut)

Les emails sont affichés dans les logs Docker.

**Dans `.env`:**
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@geoannotator.local
```

**Pour voir les emails:**
```bash
docker-compose logs -f backend
```

### Option 2: Gmail SMTP

**Étape 1:** Générer un App Password Google
1. Aller sur https://myaccount.google.com/apppasswords
2. Activer l'authentification à 2 facteurs (requis)
3. Créer un mot de passe d'application pour "Mail"
4. Copier le mot de passe de 16 caractères

**Étape 2:** Modifier `.env`
```bash
# Commenter la config console
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# DEFAULT_FROM_EMAIL=noreply@geoannotator.local

# Décommenter et remplir la config Gmail
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop  # Le mot de passe d'app de 16 chars
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

**Étape 3:** Redémarrer les conteneurs
```bash
docker-compose restart backend
```

C'est tout ! Les emails seront maintenant envoyés via Gmail.

### Option 3: Autre serveur SMTP

**Dans `.env`:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.votreserveur.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@example.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
DEFAULT_FROM_EMAIL=noreply@votredomaine.com
```

**Redémarrer:**
```bash
docker-compose restart backend
```

## 📝 Variables Disponibles

| Variable | Description | Exemple |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Type de backend email | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | Serveur SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | Port SMTP | `587` (TLS) ou `465` (SSL) |
| `EMAIL_USE_TLS` | Utiliser TLS | `True` ou `False` |
| `EMAIL_USE_SSL` | Utiliser SSL | `True` ou `False` |
| `EMAIL_HOST_USER` | Nom d'utilisateur SMTP | `email@example.com` |
| `EMAIL_HOST_PASSWORD` | Mot de passe SMTP | `votre-mot-de-passe` |
| `DEFAULT_FROM_EMAIL` | Email expéditeur | `noreply@example.com` |

## 🔧 Tester la Configuration

### Créer un utilisateur de test

```bash
docker-compose exec backend python manage.py create_test_user
```

Vous devriez voir l'email dans les logs (console) ou le recevoir dans votre boîte mail (SMTP).

### Vérifier les logs

```bash
# Voir les logs du backend
docker-compose logs -f backend

# Voir seulement les emails (avec console backend)
docker-compose logs backend | grep -A 20 "Subject:"
```

## 🐛 Dépannage

### Les emails n'arrivent pas (Gmail)

1. ✅ Vérifier que l'authentification 2FA est activée
2. ✅ Utiliser un App Password, pas votre mot de passe Gmail normal
3. ✅ Vérifier le dossier spam
4. ✅ Vérifier les logs : `docker-compose logs backend`

### Erreur "Authentication failed"

Le mot de passe est probablement incorrect. Regénérez un App Password.

### Les variables ne sont pas prises en compte

1. Vérifier que le fichier `.env` est bien à la racine du projet (à côté de `docker-compose.yml`)
2. Redémarrer les conteneurs : `docker-compose restart backend`
3. En dernier recours : `docker-compose down && docker-compose up -d`

## 💡 Conseils

- **Développement:** Utilisez le backend console pour rapidité
- **Tests réalistes:** Utilisez Gmail pour tester les vrais emails
- **Production:** Utilisez un service SMTP dédié (SendGrid, Mailgun, etc.)
- **Ne commitez jamais** le fichier `.env` avec vos vrais identifiants !

## 🔄 Revenir au Backend Console

```bash
# Dans .env, commenter Gmail et décommenter console
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@geoannotator.local

# Redémarrer
docker-compose restart backend
```
