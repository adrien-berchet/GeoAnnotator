# Deployment on Render.com

This guide explains how to deploy GeoAnnotator on Render.com with all necessary services (Django backend, Celery workers, Redis). The database is hosted on Neon.tech (serverless PostgreSQL with PostGIS).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Render.com                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐                                       │
│  │  Backend (Web)   │──────────────┐                        │
│  │  Django + DRF    │              │                        │
│  │  Port: 10000     │              │                        │
│  └────────┬─────────┘              │                        │
│           │                        │                        │
│           │  ┌──────────────────┐  │                        │
│           └──│  Redis           │  │                        │
│              │  (Celery broker) │  │                        │
│              └────────┬─────────┘  │                        │
│                       │            │                        │
│           ┌───────────┴───────┐    │                        │
│           │                   │    │                        │
│  ┌────────▼─────────┐  ┌──────▼────▼──────┐                │
│  │ Celery Worker    │  │ Celery Beat      │                │
│  │ (emails async)   │  │ (cleanup tasks)  │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
        ┌────────▼────────┐   ┌───────────▼─────────┐
        │  PostgreSQL     │   │  Frontend           │
        │  + PostGIS      │   │  (Vercel)           │
        │  (Neon.tech)    │   │                     │
        └─────────────────┘   └─────────────────────┘
```

## Prerequisites

- Render.com account (free to start)
- Neon.tech account (serverless PostgreSQL with PostGIS)
- Git repository (GitHub, GitLab, or Bitbucket)
- Gmail account with App Password (for email sending)
- Frontend deployed on Vercel (or similar)

## Option 1 : Déploiement avec Blueprint (Recommandé)

Le fichier `render.yaml` à la racine du projet définit toute l'infrastructure.

### Étapes

1. **Push le fichier `render.yaml` sur votre repository Git**
   ```bash
   git add render.yaml
   git commit -m "Add Render.com blueprint"
   git push
   ```

2. **Créer un nouveau Blueprint sur Render**
   - Aller sur [Render Dashboard](https://dashboard.render.com/)
   - Cliquer sur "New +" → "Blueprint"
   - Connecter votre repository GitHub/GitLab
   - Sélectionner la branche (ex: `main` ou `fix_email`)
   - Render détectera automatiquement `render.yaml`
   - Cliquer sur "Apply"

3. **Configurer les variables d'environnement manuelles**

   Render va créer tous les services, mais vous devez configurer certaines variables sensibles :

   **Pour le Backend** :
   - `FERNET_KEY` : Générer avec `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `EMAIL_HOST_USER` : `geoannotator.noreply@gmail.com`
   - `EMAIL_HOST_PASSWORD` : App Password Gmail (voir ci-dessous)
   - `DEFAULT_FROM_EMAIL` : `geoannotator.noreply@gmail.com`
   - `FRONTEND_URL` : URL de votre frontend Vercel (ex: `https://geoannotator.vercel.app`)
   - `CORS_ALLOWED_ORIGINS` : Même URL que `FRONTEND_URL`
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` : Credentials S3/MinIO

   **Pour Celery Worker** :
   - Même `FERNET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`

   **Pour Celery Beat** :
   - Même `FERNET_KEY`

4. **Activer PostGIS sur la base de données**

   Une fois la base créée :
   ```bash
   # Depuis le dashboard Render, ouvrir un Shell dans le service Backend
   python manage.py dbshell

   # Exécuter dans psql :
   CREATE EXTENSION IF NOT EXISTS postgis;
   \q
   ```

5. **Exécuter les migrations**
   ```bash
   # Depuis le Shell du Backend
   python manage.py migrate
   ```

6. **Créer un superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Vérifier que tout fonctionne**
   - Backend : `https://geoannotator-backend.onrender.com/api/v1/`
   - Vérifier les logs des workers Celery
   - Tester l'inscription d'un utilisateur (email doit être envoyé)

## Option 2 : Déploiement Manuel (Services Individuels)

Si vous préférez créer les services un par un :

### 1. Créer la base de données PostgreSQL

1. New + → PostgreSQL
2. Name: `geoannotator-db`
3. Database: `geoannotator`
4. User: `geoannotator`
5. Region: Choisir proche de vous
6. Plan: **Starter** (gratuit)
7. PostgreSQL Version: **15**
8. Créer

Après création, activer PostGIS :
```bash
# Depuis "Connect" → "PSQL Command"
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 2. Créer Redis

1. New + → Redis
2. Name: `geoannotator-redis`
3. Region: Même région que la DB
4. Plan: **Starter** (gratuit, 25MB)
5. Maxmemory Policy: **allkeys-lru**
6. Créer

### 3. Créer le Backend (Web Service)

1. New + → Web Service
2. Connect votre repository
3. Configuration :
   - **Name**: `geoannotator-backend`
   - **Region**: Même région
   - **Branch**: `main` (ou `fix_email`)
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Docker Build Context**: `backend`
   - **Docker Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:10000 --workers 4 --timeout 120`
   - **Plan**: Starter (gratuit avec limitations) ou Instance Type selon besoins

4. **Variables d'environnement** (à ajouter dans "Environment") :
   ```
   PYTHON_VERSION=3.11
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   SECRET_KEY=<générer-valeur-aléatoire>
   FERNET_KEY=<générer-avec-commande-ci-dessous>
   ALLOWED_HOSTS=.onrender.com
   DATABASE_URL=<copier depuis PostgreSQL "Internal Database URL">
   REDIS_URL=<copier depuis Redis "Internal Redis URL">
   CELERY_BROKER_URL=<même valeur que REDIS_URL>
   CELERY_RESULT_BACKEND=<même valeur que REDIS_URL>

   # Email
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=geoannotator.noreply@gmail.com
   EMAIL_HOST_PASSWORD=<app-password-gmail>
   DEFAULT_FROM_EMAIL=geoannotator.noreply@gmail.com

   # Frontend
   FRONTEND_URL=https://votre-frontend.vercel.app
   CORS_ALLOWED_ORIGINS=https://votre-frontend.vercel.app

   # S3/MinIO (optionnel)
   AWS_ACCESS_KEY_ID=<votre-key>
   AWS_SECRET_ACCESS_KEY=<votre-secret>
   AWS_STORAGE_BUCKET_NAME=geoannotator
   AWS_S3_REGION_NAME=eu-west-3
   ```

5. Créer le service

### 4. Créer Celery Worker

1. New + → Background Worker
2. Connect le même repository
3. Configuration :
   - **Name**: `geoannotator-celery-worker`
   - **Region**: Même région
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Docker Command**: `celery -A config worker --loglevel=info --concurrency=2`
   - **Plan**: Starter

4. **Variables d'environnement** (copier depuis Backend) :
   ```
   PYTHON_VERSION=3.11
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   SECRET_KEY=<même que backend>
   FERNET_KEY=<même que backend>
   DATABASE_URL=<même que backend>
   REDIS_URL=<même que backend>
   CELERY_BROKER_URL=<même que backend>
   CELERY_RESULT_BACKEND=<même que backend>
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=<même que backend>
   EMAIL_HOST_PASSWORD=<même que backend>
   DEFAULT_FROM_EMAIL=<même que backend>
   ```

5. Créer le service

### 5. Créer Celery Beat

1. New + → Background Worker
2. Connect le même repository
3. Configuration :
   - **Name**: `geoannotator-celery-beat`
   - **Region**: Même région
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Docker Command**: `celery -A config beat --loglevel=info`
   - **Plan**: Starter

4. **Variables d'environnement** :
   ```
   PYTHON_VERSION=3.11
   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   SECRET_KEY=<même que backend>
   FERNET_KEY=<même que backend>
   DATABASE_URL=<même que backend>
   REDIS_URL=<même que backend>
   CELERY_BROKER_URL=<même que backend>
   CELERY_RESULT_BACKEND=<même que backend>
   ```

5. Créer le service

## Configuration Gmail App Password

Pour envoyer des emails via Gmail SMTP :

1. Aller sur [Google Account Security](https://myaccount.google.com/security)
2. Activer la **vérification en 2 étapes** (si pas déjà fait)
3. Chercher "App passwords" / "Mots de passe des applications"
4. Sélectionner "Mail" et "Other (Custom name)"
5. Nommer "GeoAnnotator Render"
6. Copier le mot de passe généré (16 caractères)
7. Utiliser ce mot de passe dans `EMAIL_HOST_PASSWORD`

**⚠️ Important** : Ne jamais committer ce mot de passe dans Git !

## Générer les Clés de Sécurité

### SECRET_KEY (Django)
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### FERNET_KEY (Encryption)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Vérification Post-Déploiement

### 1. Vérifier les Services

Dans le dashboard Render, tous les services doivent être **Live** :
- ✅ geoannotator-backend (Web)
- ✅ geoannotator-celery-worker (Worker)
- ✅ geoannotator-celery-beat (Worker)
- ✅ geoannotator-redis (Redis)
- ✅ geoannotator-db (PostgreSQL)

### 2. Vérifier les Logs

**Backend** :
```
Starting gunicorn 21.2.0
Listening at: http://0.0.0.0:10000
```

**Celery Worker** :
```
celery@... ready.
Tasks:
  - apps.authentication.tasks.send_email_async
  - apps.authentication.tasks.cleanup_deleted_users
  - apps.authentication.tasks.cleanup_expired_confirmation_tokens
```

**Celery Beat** :
```
Scheduler: Starting...
DatabaseScheduler: Schedule changed.
```

### 3. Tester l'Envoi d'Email

1. Aller sur votre frontend
2. Créer un nouveau compte
3. Vérifier l'email de confirmation
4. Vérifier les logs Celery Worker :
   ```
   Task apps.authentication.tasks.send_email_async[...] succeeded in 2.5s
   ```

### 4. Vérifier les Tâches Planifiées

Dans les logs Celery Beat, chercher :
```
Scheduler: Sending due task cleanup-deleted-users-daily
Scheduler: Sending due task cleanup-expired-tokens-daily
```

## Coûts Render.com

### Plan Gratuit (Starter)

| Service | Plan | Prix | Limitations |
|---------|------|------|-------------|
| PostgreSQL | Starter | **Gratuit** | 256MB RAM, 1GB storage, expire après 90 jours |
| Redis | Starter | **Gratuit** | 25MB RAM |
| Backend (Web) | Starter | **Gratuit** | 0.1 CPU, 512MB RAM, sleep après 15min inactivité |
| Celery Worker | Starter | **Gratuit** | 0.1 CPU, 512MB RAM, sleep après 15min inactivité |
| Celery Beat | Starter | **Gratuit** | 0.1 CPU, 512MB RAM, sleep après 15min inactivité |

**Total : 0€/mois** (avec limitations)

**⚠️ Limitations importantes** :
- **Sleep** : Les services gratuits s'endorment après 15 minutes d'inactivité
- **Spin-up delay** : 30-50 secondes au premier appel après sleep
- **Database expiration** : DB gratuite expire après 90 jours (sauvegarder régulièrement !)

### Plans Payants (Production)

Pour éviter le sleep et avoir de meilleures performances :

| Service | Plan | Prix/mois | Specs |
|---------|------|-----------|-------|
| PostgreSQL | Standard | **$7** | 1GB RAM, 10GB storage, persistant |
| Redis | Standard | **$10** | 100MB RAM, persistant |
| Backend (Web) | Starter | **$7** | 0.5 CPU, 512MB RAM, pas de sleep |
| Celery Worker | Starter | **$7** | 0.5 CPU, 512MB RAM, pas de sleep |
| Celery Beat | Starter | **$7** | 0.5 CPU, 512MB RAM, pas de sleep |

**Total : ~$38/mois** pour une production stable

**Optimisation** : Vous pouvez combiner Worker + Beat dans un seul service pour économiser $7/mois.

## Mise à Jour du Code

### Déploiement Automatique

Si vous avez activé "Auto-Deploy" :
```bash
git add .
git commit -m "Update feature X"
git push origin main
```

Render va automatiquement rebuilder et redéployer tous les services.

### Déploiement Manuel

Dans le dashboard Render :
1. Sélectionner le service
2. Cliquer "Manual Deploy" → "Deploy latest commit"

## Commandes Utiles

### Exécuter des Commandes Django

Depuis le dashboard Render, service Backend → Shell :

```bash
# Migrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Shell Django
python manage.py shell

# Accès à la DB
python manage.py dbshell
```

### Vérifier Celery

Depuis le worker Shell :
```bash
# Lister les tâches enregistrées
celery -A config inspect registered

# Voir les tâches actives
celery -A config inspect active

# Voir les stats
celery -A config inspect stats
```

### Vérifier Redis

Depuis n'importe quel service connecté à Redis :
```bash
# Installer redis-tools si nécessaire
apt-get update && apt-get install -y redis-tools

# Se connecter
redis-cli -u $REDIS_URL

# Commandes Redis
PING
INFO
KEYS celery*
LLEN celery  # Taille de la queue
```

## Dépannage

### Erreur : "Connection to Redis lost"

**Cause** : Le service Redis n'est pas démarré ou l'URL est incorrecte

**Solution** :
1. Vérifier que le service Redis est "Live"
2. Vérifier que `CELERY_BROKER_URL` = URL interne de Redis
3. Redémarrer les workers Celery

### Erreur : "Database connection failed"

**Cause** : PostgreSQL pas encore prêt ou URL incorrecte

**Solution** :
1. Vérifier que la DB est "Available"
2. Utiliser l'**Internal Database URL** (pas l'External)
3. Vérifier que PostGIS est installé : `CREATE EXTENSION postgis;`

### Workers Celery ne démarrent pas

**Cause** : Erreur dans le code ou dépendances manquantes

**Solution** :
1. Vérifier les logs du worker
2. Vérifier que le Dockerfile build correctement
3. Tester localement avec Docker : `docker build -t test backend/`

### Emails ne partent pas

**Cause** : App Password Gmail invalide ou variables manquantes

**Solution** :
1. Vérifier `EMAIL_HOST_PASSWORD` (16 caractères sans espaces)
2. Vérifier `EMAIL_HOST_USER` = adresse Gmail complète
3. Vérifier les logs Celery Worker pour les erreurs SMTP
4. Tester avec `telnet smtp.gmail.com 587`

### Service "sleep" trop rapidement

**Cause** : Plan gratuit avec auto-sleep après 15min

**Solution** :
- Upgrader vers un plan payant ($7/mois/service)
- OU utiliser un service de "ping" pour garder le service actif (ex: UptimeRobot, cron-job.org)

## Monitoring & Alertes

### Uptime Robot (Gratuit)

1. Créer un compte sur [UptimeRobot](https://uptimerobot.com/)
2. Ajouter un monitor HTTP :
   - URL: `https://geoannotator-backend.onrender.com/api/v1/health/`
   - Interval: 5 minutes
3. Configurer les alertes par email

### Sentry (Erreurs)

Pour capturer les erreurs en production :

1. Créer un compte [Sentry](https://sentry.io/)
2. Installer le SDK :
   ```bash
   pip install sentry-sdk
   ```
3. Configurer dans `backend/config/settings/production.py` :
   ```python
   import sentry_sdk

   sentry_sdk.init(
       dsn="votre-sentry-dsn",
       environment="production",
   )
   ```
4. Ajouter `SENTRY_DSN` dans les variables d'environnement Render

## Sauvegardes

### Base de Données

Render fait des backups automatiques, mais vous pouvez aussi :

```bash
# Depuis le Shell Backend
pg_dump $DATABASE_URL > backup.sql

# Ou depuis votre machine locale
pg_dump <External-Database-URL> > backup-$(date +%Y%m%d).sql
```

> **⚠️ Note pour Neon.tech**: Si vous utilisez Neon, utilisez l'URL de **connexion directe** (pas l'URL poolée) pour `pg_dump`. Voir [Database Backup Troubleshooting](./database-backup-troubleshooting.md) pour plus de détails.

### Restaurer une Sauvegarde

```bash
psql $DATABASE_URL < backup.sql
```

## Checklist de Déploiement

- [ ] Services créés (Backend, Worker, Beat, Redis, PostgreSQL)
- [ ] PostGIS activé sur la DB
- [ ] Variables d'environnement configurées
- [ ] Migrations exécutées
- [ ] Superuser créé
- [ ] Envoi d'email testé
- [ ] CORS configuré avec l'URL frontend
- [ ] Frontend Vercel configuré avec l'URL backend
- [ ] Monitoring configuré (UptimeRobot)
- [ ] Alertes email configurées
- [ ] Sauvegardes DB testées

## Support

- **Render Docs** : https://render.com/docs
- **Community** : https://community.render.com/
- **Status** : https://status.render.com/

---

**Dernière mise à jour** : 2025-11-17
