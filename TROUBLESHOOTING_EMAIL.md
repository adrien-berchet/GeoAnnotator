# Dépannage Email SMTP

Guide pour résoudre les problèmes d'envoi d'email avec Gmail ou autre SMTP.

## 🧪 Test Rapide

Testez votre configuration email avec cette commande :

```bash
docker-compose exec backend python manage.py test_email --to votre-email@gmail.com
```

Cette commande va :
- ✅ Afficher toute votre configuration email
- ✅ Tenter d'envoyer un email de test
- ✅ Donner des messages d'erreur détaillés si ça échoue

## 📧 Configuration Gmail : Liste de Vérification

### 1. ✅ Authentification 2 Facteurs (2FA) Activée

Gmail exige que la 2FA soit activée pour utiliser les App Passwords.

**Vérifier :** https://myaccount.google.com/security

Si pas activé :
1. Aller dans Sécurité
2. Activer "Validation en deux étapes"
3. Suivre le processus de configuration

### 2. ✅ Générer un App Password (pas votre mot de passe Gmail normal)

**Ne PAS utiliser votre mot de passe Gmail habituel !**

**Étapes :**
1. Aller sur https://myaccount.google.com/apppasswords
2. Sélectionner "Autre (nom personnalisé)"
3. Entrer "GeoAnnotator"
4. Cliquer "Générer"
5. **Copier le mot de passe de 16 caractères** (format : `abcd efgh ijkl mnop`)

### 3. ✅ Configuration `.env` Correcte

Votre fichier `.env` doit ressembler à ça :

```bash
# Email - Gmail SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=votre-email@gmail.com
```

**Points importants :**
- ✅ `EMAIL_BACKEND` doit être `django.core.mail.backends.smtp.EmailBackend`
- ✅ `EMAIL_PORT` doit être `587` (TLS) ou `465` (SSL)
- ✅ `EMAIL_USE_TLS` doit être `True` (avec port 587)
- ✅ `EMAIL_HOST_PASSWORD` doit être l'App Password de 16 chars, **PAS votre mot de passe Gmail**
- ✅ Ne pas avoir de commentaires `#` sur les lignes actives

### 4. ✅ Redémarrer Docker Après Modification

**TRÈS IMPORTANT :** Les variables d'environnement ne sont chargées qu'au démarrage !

```bash
docker-compose restart backend
```

Ou pour être sûr :
```bash
docker-compose down
docker-compose up -d
```

## 🔍 Problèmes Courants

### Problème : "Email sent successfully" mais rien reçu

**Causes possibles :**

1. **Email dans les spams**
   - ✅ Vérifier le dossier Spam/Courrier indésirable
   - ✅ Vérifier les filtres Gmail

2. **Variables d'environnement pas chargées**
   ```bash
   # Vérifier si la config est bien chargée
   docker-compose exec backend python manage.py test_email
   ```

   Si vous voyez `EMAIL_BACKEND: django.core.mail.backends.console.EmailBackend`, c'est que la config SMTP n'est **pas** chargée !

3. **App Password incorrect**
   - Régénérer un nouveau App Password
   - Vérifier qu'il n'y a pas d'espaces dans le `.env`
   - Format attendu : `abcd efgh ijkl mnop` (4 groupes de 4 lettres)

### Problème : "SMTP AUTH extension not supported"

**Cause :** EMAIL_HOST_USER ou EMAIL_HOST_PASSWORD vide ou non défini.

**Solution :**
```bash
# Dans .env, vérifier que ces lignes existent et sont complètes :
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password-16-chars
```

Puis redémarrer : `docker-compose restart backend`

### Problème : "Authentication failed" ou "Invalid credentials"

**Causes :**
1. ❌ Vous utilisez votre mot de passe Gmail au lieu d'un App Password
2. ❌ L'App Password est incorrect
3. ❌ La 2FA n'est pas activée

**Solution :**
1. Aller sur https://myaccount.google.com/apppasswords
2. Supprimer l'ancien App Password
3. Créer un nouveau
4. Mettre à jour `.env`
5. `docker-compose restart backend`

### Problème : Console backend toujours actif

**Symptômes :**
- La commande `test_email` dit `Console backend detected`
- Les emails s'affichent dans les logs au lieu d'être envoyés

**Cause :** Les variables d'environnement Gmail sont commentées ou non chargées.

**Solution :**

1. **Vérifier `.env` :**
   ```bash
   # Ces lignes doivent être SANS # au début
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   # ... etc
   ```

2. **Vérifier que `.env` est bien à la racine du projet** (à côté de `docker-compose.yml`)

3. **Redémarrer complètement :**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Vérifier la config chargée :**
   ```bash
   docker-compose exec backend python manage.py test_email
   ```
   Doit afficher : `EMAIL_BACKEND: django.core.mail.backends.smtp.EmailBackend`

## 📋 Checklist de Dépannage

Cochez chaque point :

- [ ] 2FA activée sur le compte Google
- [ ] App Password généré (16 caractères)
- [ ] `.env` à la racine du projet (à côté de `docker-compose.yml`)
- [ ] Lignes Gmail dans `.env` décommentées (pas de `#` au début)
- [ ] `EMAIL_HOST_PASSWORD` contient l'App Password, pas le mot de passe Gmail
- [ ] `EMAIL_USE_TLS=True` (pas `False`)
- [ ] Docker redémarré après modification de `.env`
- [ ] Testé avec `python manage.py test_email`
- [ ] Vérifié le dossier Spam

## 🔧 Commandes Utiles

```bash
# Tester la configuration email
docker-compose exec backend python manage.py test_email --to your-email@gmail.com

# Voir les logs du backend
docker-compose logs backend --tail=100 -f

# Voir seulement les erreurs SMTP
docker-compose logs backend | grep -i "smtp\|email\|error"

# Redémarrer complètement
docker-compose down && docker-compose up -d

# Créer un utilisateur de test
docker-compose exec backend python manage.py create_test_user

# Vérifier les variables d'environnement dans Docker
docker-compose exec backend env | grep EMAIL
```

## 💡 Configuration Alternative : MailHog (Pour Tests Locaux)

Si vous voulez tester sans configurer Gmail, utilisez MailHog :

```yaml
# Ajouter dans docker-compose.yml
mailhog:
  image: mailhog/mailhog
  ports:
    - "1025:1025"  # SMTP
    - "8025:8025"  # Web UI
```

Puis dans `.env` :
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@geoannotator.local
```

Interface web : http://localhost:8025 (tous les emails y apparaissent)

## ❓ Besoin d'Aide ?

Si après tout ça ça ne marche toujours pas :

1. Exécuter : `docker-compose exec backend python manage.py test_email`
2. Copier toute la sortie
3. Partager l'erreur complète (en masquant les mots de passe !)
