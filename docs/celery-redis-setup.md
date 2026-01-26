# Configuration Celery + Redis pour la Production

Ce document explique comment configurer Celery et Redis pour l'envoi asynchrone d'emails en production.

## Pourquoi Celery + Redis ?

Sans Celery, l'envoi d'emails bloque la requête HTTP pendant plusieurs secondes, ce qui peut :
- Causer des timeouts Gunicorn en production
- Dégrader l'expérience utilisateur (pages qui ne répondent pas)
- Empêcher l'envoi d'emails si le timeout est atteint

Avec Celery + Redis :
- ✅ Les emails sont envoyés en arrière-plan (retour immédiat à l'utilisateur)
- ✅ Retry automatique en cas d'échec d'envoi
- ✅ Tâches planifiées (nettoyage des tokens expirés, suppression des comptes)
- ✅ Meilleure scalabilité

## Mode de Fonctionnement Actuel

L'application utilise un **système de fallback automatique** :

1. **Si Redis est disponible** : Les emails sont envoyés via Celery (mode asynchrone)
2. **Si Redis n'est pas disponible** : Les emails sont envoyés directement (mode synchrone)

Cela permet à l'application de fonctionner même sans Redis, mais l'envoi d'emails sera alors bloquant et sujet aux timeouts.

## Configuration avec Docker Compose

### Production Complète (Recommandé)

Si vous utilisez Docker Compose, les services Redis, Celery Worker et Celery Beat sont déjà configurés :

```bash
# Démarrer tous les services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Vérifier que Redis est bien démarré
docker-compose ps redis

# Vérifier que les workers Celery sont actifs
docker-compose ps celery_worker celery_beat

# Voir les logs Celery
docker-compose logs -f celery_worker celery_beat
```

**Services inclus** :
- `redis` : Broker de messages (port 6379)
- `celery_worker` : Traite les tâches asynchrones (envoi d'emails)
- `celery_beat` : Exécute les tâches planifiées (nettoyage quotidien)

**Variables d'environnement requises** (déjà dans `docker-compose.yml`) :
```env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Configuration Manuelle (Sans Docker)

### 1. Installer Redis

**Ubuntu/Debian** :
```bash
sudo apt update
sudo apt install redis-server

# Démarrer Redis
sudo systemctl start redis
sudo systemctl enable redis

# Vérifier
redis-cli ping  # Devrait répondre "PONG"
```

**macOS (Homebrew)** :
```bash
brew install redis
brew services start redis
```

### 2. Configurer les Variables d'Environnement

Ajouter dans votre fichier `.env` de production :

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Si Redis est sur un autre serveur :
```env
CELERY_BROKER_URL=redis://your-redis-host:6379/0
CELERY_RESULT_BACKEND=redis://your-redis-host:6379/0
```

### 3. Démarrer les Workers Celery

**Celery Worker** (traite les tâches) :
```bash
cd backend
source venv/bin/activate  # Si vous utilisez un virtualenv
celery -A config worker --loglevel=info
```

**Celery Beat** (tâches planifiées) :
```bash
cd backend
source venv/bin/activate
celery -A config beat --loglevel=info
```

### 4. Configuration avec Systemd (Recommandé pour Production)

**Celery Worker** (`/etc/systemd/system/geoannotator-celery-worker.service`) :
```ini
[Unit]
Description=GeoAnnotator Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/GeoAnnotator/backend
EnvironmentFile=/path/to/GeoAnnotator/.env
ExecStart=/path/to/GeoAnnotator/backend/venv/bin/celery -A config worker \
  --loglevel=info \
  --logfile=/var/log/geoannotator/celery-worker.log \
  --pidfile=/var/run/celery/worker.pid

[Install]
WantedBy=multi-user.target
```

**Celery Beat** (`/etc/systemd/system/geoannotator-celery-beat.service`) :
```ini
[Unit]
Description=GeoAnnotator Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/GeoAnnotator/backend
EnvironmentFile=/path/to/GeoAnnotator/.env
ExecStart=/path/to/GeoAnnotator/backend/venv/bin/celery -A config beat \
  --loglevel=info \
  --logfile=/var/log/geoannotator/celery-beat.log \
  --pidfile=/var/run/celery/beat.pid

[Install]
WantedBy=multi-user.target
```

**Activer et démarrer** :
```bash
# Créer les répertoires nécessaires
sudo mkdir -p /var/log/geoannotator /var/run/celery
sudo chown www-data:www-data /var/log/geoannotator /var/run/celery

# Activer les services
sudo systemctl enable geoannotator-celery-worker geoannotator-celery-beat
sudo systemctl start geoannotator-celery-worker geoannotator-celery-beat

# Vérifier le statut
sudo systemctl status geoannotator-celery-worker
sudo systemctl status geoannotator-celery-beat
```

## Services Redis Managés (Production à Grande Échelle)

Pour une production plus robuste, utilisez un service Redis managé :

### AWS ElastiCache

```env
CELERY_BROKER_URL=redis://your-cluster.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://your-cluster.cache.amazonaws.com:6379/0
```

### Redis Cloud (RedisLabs)

```env
CELERY_BROKER_URL=redis://default:password@redis-12345.redislabs.com:6379
CELERY_RESULT_BACKEND=redis://default:password@redis-12345.redislabs.com:6379
```

### DigitalOcean Managed Redis

```env
CELERY_BROKER_URL=redis://default:password@db-redis-nyc3-12345.ondigitalocean.com:25061
CELERY_RESULT_BACKEND=redis://default:password@db-redis-nyc3-12345.ondigitalocean.com:25061
```

### Upstash (Redis Serverless)

```env
CELERY_BROKER_URL=rediss://default:password@abc-12345.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://default:password@abc-12345.upstash.io:6379
```

## Tâches Celery Configurées

### 1. Envoi d'Emails Asynchrone

**Tâche** : `send_email_async`
- **Trigger** : Chaque fois qu'un email doit être envoyé (inscription, changement d'email, suppression de compte)
- **Retry** : 3 tentatives avec 60 secondes d'intervalle
- **Comportement** : Si Redis n'est pas disponible, fallback en mode synchrone

### 2. Nettoyage des Comptes Supprimés

**Tâche** : `cleanup_deleted_users`
- **Planification** : Tous les jours à 2h00 du matin
- **Action** : Supprime définitivement les comptes soft-deleted depuis plus de 30 jours
- **Requis** : Celery Beat doit être actif

### 3. Nettoyage des Tokens Expirés

**Tâche** : `cleanup_expired_confirmation_tokens`
- **Planification** : Tous les jours à 3h00 du matin
- **Action** : Supprime les tokens expirés depuis plus de 7 jours
- **Requis** : Celery Beat doit être actif

## Vérification du Bon Fonctionnement

### Tester l'Envoi d'Email

1. **Créer un nouveau compte** sur votre application
2. **Vérifier les logs Celery** :
   ```bash
   # Docker
   docker-compose logs -f celery_worker

   # Systemd
   sudo tail -f /var/log/geoannotator/celery-worker.log
   ```
3. **Chercher** : `Task apps.authentication.tasks.send_email_async[...] succeeded`

### Vérifier les Tâches Planifiées

```bash
# Lister les tâches enregistrées
celery -A config inspect registered

# Voir les tâches actives
celery -A config inspect active

# Vérifier le schedule de Beat
celery -A config inspect scheduled
```

### Monitoring Redis

```bash
# Connexion à Redis
redis-cli

# Voir les statistiques
INFO

# Voir les clés Celery
KEYS celery*

# Vérifier la file d'attente
LLEN celery

# Quitter
EXIT
```

## Dépannage

### Erreur : "Connection refused" sur localhost:6379

**Cause** : Redis n'est pas démarré ou `CELERY_BROKER_URL` n'est pas défini

**Solution** :
1. Vérifier que Redis est actif : `redis-cli ping`
2. Si Redis est dans Docker : utiliser `redis://redis:6379/0` (nom du service)
3. Si Redis est local : utiliser `redis://localhost:6379/0`
4. Vérifier les variables d'environnement : `echo $CELERY_BROKER_URL`

### Les Emails sont Envoyés mais Lentement

**Cause** : Celery n'est pas configuré, le fallback synchrone est utilisé

**Solution** :
- Vérifier que `celery_worker` est démarré
- Vérifier les logs : un warning "Celery unavailable, sending email synchronously" apparaît

### Les Tâches Planifiées ne s'Exécutent Pas

**Cause** : Celery Beat n'est pas démarré

**Solution** :
```bash
# Docker
docker-compose ps celery_beat

# Systemd
sudo systemctl status geoannotator-celery-beat

# Vérifier les logs
docker-compose logs celery_beat
# ou
sudo tail -f /var/log/geoannotator/celery-beat.log
```

### Redis Consomme Trop de Mémoire

**Cause** : Accumulation de résultats de tâches

**Solution** : Configurer l'expiration des résultats dans `backend/config/celery.py` :
```python
app.conf.result_expires = 3600  # 1 heure
```

Ou désactiver le stockage des résultats :
```python
CELERY_RESULT_BACKEND = None
```

## Sécurité

### Redis avec Authentification

1. **Configurer un mot de passe Redis** (`/etc/redis/redis.conf`) :
   ```conf
   requirepass your-strong-password
   ```

2. **Mettre à jour les URLs Celery** :
   ```env
   CELERY_BROKER_URL=redis://:your-strong-password@localhost:6379/0
   CELERY_RESULT_BACKEND=redis://:your-strong-password@localhost:6379/0
   ```

### Redis sur Réseau Privé

Ne jamais exposer Redis sur Internet. Configurer le firewall :

```bash
# Autoriser Redis uniquement en local
sudo ufw allow from 127.0.0.1 to any port 6379

# Ou uniquement depuis le réseau Docker
sudo ufw allow from 172.18.0.0/16 to any port 6379
```

## Performance et Scalabilité

### Ajuster le Nombre de Workers

Plus de workers = plus de tâches traitées en parallèle :

```bash
# 4 workers
celery -A config worker --loglevel=info --concurrency=4

# Auto (nombre de CPUs)
celery -A config worker --loglevel=info --autoscale=10,3
```

### Monitoring Avancé

**Flower** (interface web pour Celery) :

```bash
pip install flower
celery -A config flower --port=5555
```

Accéder à `http://localhost:5555` pour voir :
- Tâches en cours
- Historique des tâches
- Workers actifs
- Graphiques de performance

## Résumé

| Environnement | Redis | Celery Worker | Celery Beat | Comportement |
|---------------|-------|---------------|-------------|--------------|
| **Tests (CI)** | ❌ Non (memory) | ❌ Non (eager mode) | ❌ Non | Synchrone, pas de Redis |
| **Dev (Docker)** | ✅ Container | ✅ Container | ✅ Container | Asynchrone complet |
| **Dev (Local)** | ❌ Non | ❌ Non | ❌ Non | Fallback synchrone |
| **Production** | ✅ Requis | ✅ Requis | ✅ Recommandé | Asynchrone complet |

**Recommandation** : En production, toujours configurer Redis + Celery Worker + Celery Beat pour une meilleure expérience utilisateur et éviter les timeouts.

---

**Dernière mise à jour** : 2025-11-17
