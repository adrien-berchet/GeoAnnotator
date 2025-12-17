# GeoAnnotator Web Application

A comprehensive web application for geospatial annotation enabling field researchers to capture GPS points with rich multimedia annotations.

## Features

### Core Functionality
- 🗺️ **Interactive Leaflet Map** with marker clustering, bounding box search, and multiple map layers (OpenStreetMap, Satellite, Terrain)
- 📍 **GPS Point Management** with full CRUD operations, custom point types, and tag-based organization
- 📝 **Rich Annotations** supporting text with **Markdown formatting**, images, documents, and file attachments
- 🏷️ **Point Types** with customizable icons (emoji, uploaded images, or URLs), multi-language support, and drag-and-drop reordering
- 🔖 **Tag Management** for organizing and filtering points

### Collaboration & Sharing
- 👥 **Point Sharing** with view/edit/transfer permissions
- 👫 **Friends System** with add friend by username and shared content statistics
- 📧 **Share Invitations** via email with secure acceptance workflow

### Data Management
- 📤 **Import/Export** in multiple formats:
  - **GeoJSON** - Standard geographic format with full annotation support
  - **GPX** - GPS Exchange Format for device compatibility
  - **KML** - Google Earth format for visualization
  - **CSV** - Spreadsheet format for data analysis
  - **ZIP** - Complete archive with files and annotations
- 🗑️ **30-Day Trash** with point restoration capability

### User Settings & Account
- 🎨 **Theme Settings** with light/dark mode and system preference support
- 🌐 **Multi-language Support** (English, French) with automatic preference persistence
- 🗺️ **Default Map Type** configuration
- 👤 **Account Management** with username, email change (with confirmation), and password update
- 🗑️ **Account Deletion** with 30-day grace period and email confirmation

### Security & Performance
- 🔒 **JWT Authentication** with 1-hour access tokens and 7-day refresh tokens
- 💾 **Storage Quota** management (1GB/file, 2GB/user)
- 🔐 **Editing Locks** for concurrent access prevention
- 🔑 **Email Encryption** with Fernet encryption for stored emails
- 📊 **Monitoring & Observability** with Sentry integration, health checks, and metrics

## Tech Stack

### Backend
- **Django 4.2+** with Django REST Framework
- **PostgreSQL 15+** with PostGIS extension for geospatial data
- **JWT Authentication** via djangorestframework-simplejwt
- **Celery 5.3+** with Redis for background tasks (async email, scheduled cleanup)
- **django-fernet-fields** for email encryption
- **Sentry SDK** for error tracking and performance monitoring
- **MinIO/S3** for file storage
- **Python 3.11+**

### Frontend
- **React 19+** with TypeScript 5.9+
- **Vite 7+** for fast development and building
- **Leaflet 1.9+** for interactive mapping
- **@dnd-kit** for drag-and-drop functionality
- **@uiw/react-md-editor** for Markdown editing
- **@tanstack/react-query** for data fetching
- **Axios** for API calls
- **React Router 7+** for navigation
- **Sentry** for error tracking

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

See the [Deployment Guide](docs/deployment.md) for detailed production setup instructions.

## Prerequisites

### Docker Setup (Recommended)
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available

### Manual Setup
- Python 3.11+
- Node.js 20+ or 22+
- PostgreSQL 15+ with PostGIS extension
- GDAL 3.6+ (for GeoDjango)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd GeoAnnotator
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
│   │   ├── authentication/    # User auth, registration, JWT
│   │   ├── points/            # GPS points, point types, tags
│   │   ├── annotations/       # Text, image, document annotations
│   │   ├── sharing/           # Point sharing, friends system
│   │   ├── trash/             # Soft delete, restoration
│   │   ├── export_import/     # GeoJSON, GPX, KML, CSV, ZIP
│   │   ├── settings/          # User preferences
│   │   └── core/              # Shared utilities, middleware
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── celery.py          # Celery configuration
│   │   └── wsgi.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── manage.py
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── api/               # API client and endpoints
│   │   ├── components/        # Reusable UI components
│   │   │   ├── account/       # Account management components
│   │   │   ├── annotations/   # Annotation display/editing
│   │   │   ├── auth/          # Login, register forms
│   │   │   ├── common/        # Shared components
│   │   │   ├── layout/        # Navigation, header, footer
│   │   │   ├── map/           # Map components
│   │   │   ├── points/        # Point forms, type management
│   │   │   ├── settings/      # Settings selectors
│   │   │   ├── sharing/       # Share forms
│   │   │   └── trash/         # Trash list
│   │   ├── contexts/          # React contexts (Theme, Language, Auth)
│   │   ├── hooks/             # Custom React hooks
│   │   ├── pages/             # Page components
│   │   ├── styles/            # Global CSS and theme variables
│   │   ├── types/             # TypeScript type definitions
│   │   └── utils/             # Utility functions
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── docs/
│   ├── api.md                 # REST API documentation
│   ├── deployment.md          # Production deployment guide
│   ├── markdown-annotations.md # Markdown usage guide
│   └── map-popup-design.md    # Map popup design docs
├── docker-compose.yml         # Development stack
├── docker-compose.prod.yml    # Production overrides
├── Makefile                   # Development commands
├── MONITORING.md              # Observability documentation
├── CODE_QUALITY_REVIEW.md     # Code quality analysis
└── .pre-commit-config.yaml    # Pre-commit hooks
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

- **[API Documentation](docs/api.md)** - Complete REST API reference with endpoints, request/response formats, and error codes
- **[Markdown Annotations Guide](docs/markdown-annotations.md)** - Learn how to use Markdown formatting in text annotations
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions (Docker, manual, Nginx, SSL)
- **[Monitoring & Observability](MONITORING.md)** - Sentry integration, health checks, metrics, and logging

## License

[License information to be added]

## Contact

[Contact information to be added]
