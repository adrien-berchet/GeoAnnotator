# GeoAnnotator Web Application

A comprehensive web application for geospatial annotation enabling field researchers to capture GPS points with rich multimedia annotations.

## Features

- 🗺️ **Interactive Leaflet Map** with clustering and bounding box search
- 📍 **GPS Point Management** with create, read, update, delete operations
- 📝 **Rich Annotations** supporting text with **Markdown formatting**, images, documents, and files
- 👥 **Collaborative Sharing** with view/edit/transfer permissions
- 📤 **Import/Export** in multiple formats (GeoJSON, GPX, KML, CSV, ZIP)
- 🗑️ **30-Day Trash** with restoration capability
- 🔒 **JWT Authentication** with 1-hour access tokens
- 💾 **Storage Quota** management (1GB/file, 2GB/user)
- 🔐 **Editing Locks** for concurrent access prevention

## Tech Stack

### Backend
- **Django 4.2+** with Django REST Framework
- **PostgreSQL 15+** with PostGIS extension
- **JWT Authentication** via djangorestframework-simplejwt
- **Python 3.11+**

### Frontend
- **React 18+** with TypeScript
- **Vite 5+** for fast development
- **Leaflet 1.9+** for interactive mapping
- **Axios** for API calls
- **React Router** for navigation

## Quick Start with Docker (Recommended)

The fastest way to get started is using Docker:

```bash
# Start all services
./start-local.sh

# Or using make
make start
```

This will:
- Start PostgreSQL with PostGIS
- Start Django backend
- Start React frontend
- Start MinIO for file storage
- Run migrations
- Create a default admin user

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- MinIO Console: http://localhost:9001

**Default credentials:**
- Email: `admin@geoannotator.local`
- Password: `admin123`

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## Prerequisites

### Docker Setup (Recommended)
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available

### Manual Setup
- Python 3.11+
- Node.js 20.19+ or 22.12+
- PostgreSQL 15+ with PostGIS extension
- GDAL 3.7+ (for GeoDjango)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd GeoAnnotator
git checkout 001-build-a-web
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Create .env file
cp .env.example .env
# Edit .env with your database credentials

# Create database with PostGIS
createdb geoannotator
psql geoannotator -c "CREATE EXTENSION postgis;"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Backend API will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Development

### Using Make Commands (Recommended)

```bash
make help          # Show all available commands
make start         # Start all services
make stop          # Stop all services
make logs          # View logs
make health        # Check service health
make test          # Run all tests
make shell         # Open Django shell
make migrate       # Run migrations
make backup        # Backup database
```

See `make help` for all available commands.

### Backend Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov

# Format code
black apps/
isort apps/

# Lint code
flake8 apps/
mypy apps/

# Create new Django app
python manage.py startapp <app_name> apps/<app_name>
```

### Frontend Commands

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build

# Preview production build
npm run preview
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Project Structure

```
GeoAnnotator/
├── backend/
│   ├── apps/
│   │   ├── authentication/
│   │   ├── points/
│   │   ├── annotations/
│   │   ├── sharing/
│   │   ├── trash/
│   │   └── export_import/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── manage.py
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── specs/
│   └── 001-build-a-web/
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── quickstart.md
│       ├── tasks.md
│       └── contracts/
└── .pre-commit-config.yaml
```

## API Documentation

API documentation is available at:
- Development: `http://localhost:8000/api/docs/`
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`

## Testing

### Backend Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest apps/authentication/tests/test_models.py

# Run tests with markers
pytest -m unit  # Unit tests only
pytest -m integration  # Integration tests only
pytest -m contract  # Contract tests only

# Run with coverage
pytest --cov --cov-report=html
```

### Frontend Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test src/components/auth/LoginForm.test.tsx
```

## Contributing

1. Create a feature branch from `main`
2. Follow the `.specify` workflow for feature development
3. Ensure all tests pass and coverage meets requirements (≥80% general, ≥95% critical paths)
4. Run pre-commit hooks before committing
5. Submit a pull request

## Documentation

- **[Markdown Annotations Guide](docs/markdown-annotations.md)** - Learn how to use Markdown formatting in text annotations
- **[API Documentation](docs/api.md)** - REST API reference
- **[Deployment Guide](docs/deployment.md)** - General production deployment instructions
- **[Render.com + Neon Deployment](RENDER.md)** - Quick deploy with Blueprint (recommended)
- **[Celery & Redis Setup](docs/celery-redis-setup.md)** - Async email configuration

## License

[License information to be added]

## Contact

[Contact information to be added]
