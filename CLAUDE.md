# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based smart notification system with PostgreSQL database integration. The project manages device FCM tokens for push notifications, uses Python 3.13, UV for dependency management, and is configured for Railway deployment with environment variable management.

## Development Environment

- **Python Version**: 3.13 (specified in `.python-version`)
- **Package Manager**: UV (modern Python package manager)
- **Virtual Environment**: `.venv/` (managed by UV)
- **Web Framework**: FastAPI with Uvicorn ASGI server
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Environment Management**: python-dotenv for .env files

## Key Commands

### Environment Setup
```bash
# Copy environment template and configure
cp .env.example .env
# Edit .env with your database credentials

# Install dependencies
uv sync
```

### Running the Application
```bash
# Start development server (loads .env automatically)
uv run python main.py

# Alternative: Start with uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Package Management
```bash
# Add new dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Update lock file
uv lock
```

### Testing API Endpoints
```bash
# Test root endpoint
curl http://localhost:8000/

# Test health check with database status
curl http://localhost:8000/health

# Register a device
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "your_fcm_token_here"}'

# Get all active devices
curl http://localhost:8000/devices
```

## API Endpoints

- `GET /` - Returns JSON: `{"message": "Hello World"}`
- `GET /health` - Health check with database connectivity status
- `POST /devices` - Register device with FCM token, returns device UUID
- `GET /devices` - Retrieve all active devices

## Database Architecture

### Models
- **Device Model** (`models.py`):
  - `device_uuid` (Primary Key) - Auto-generated UUID
  - `fcm_token` (Text) - Firebase Cloud Messaging token
  - `is_active` (Boolean) - Device status flag
  - `created_at` / `updated_at` - Timestamps

### Database Layer
- **Connection** (`database.py`): SQLAlchemy engine with session management
- **Auto-initialization**: Tables created automatically on startup via `Base.metadata.create_all()`
- **Dependency Injection**: Database sessions injected via FastAPI's `Depends(get_db)`

## Environment Configuration

### Local Development
- Uses `.env` file loaded via python-dotenv
- `.env.example` provides template for required variables
- Database URL supports both PostgreSQL and SQLite

### Railway Deployment
- Automatic `DATABASE_URL` injection from Railway PostgreSQL addon
- Environment variables override .env file settings

## Deployment Configuration

### Railway
- **Configuration**: `railway.toml` with Nixpacks builder
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Database**: Railway PostgreSQL addon provides `DATABASE_URL`
- **Health Check**: `/health` endpoint includes database connectivity

### Alternative Platforms
- **Procfile**: Available for Heroku-compatible platforms
- **Environment Variables**: Uses `DATABASE_URL` and `$PORT`

## Project Structure

- `main.py` - FastAPI app with device management endpoints
- `database.py` - SQLAlchemy configuration and session management
- `models.py` - SQLAlchemy ORM models (Device)
- `pyproject.toml` - Dependencies including FastAPI, SQLAlchemy, psycopg2-binary
- `.env` / `.env.example` - Environment variable configuration
- `railway.toml` / `Procfile` - Deployment configurations

## Architecture Notes

Modular FastAPI application with clean separation:
- **API Layer** (`main.py`): Pydantic models, route handlers, dependency injection
- **Database Layer** (`database.py`): Connection management, session factory
- **Model Layer** (`models.py`): SQLAlchemy ORM definitions
- **Environment Layer**: python-dotenv for configuration management
- **Auto-migration**: Tables created on startup (no manual migrations needed)