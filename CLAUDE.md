# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based smart notification system with a simple JSON API. The project uses Python 3.13, UV for dependency management, and is configured for Railway deployment.

## Development Environment

- **Python Version**: 3.13 (specified in `.python-version`)
- **Package Manager**: UV (modern Python package manager)
- **Virtual Environment**: `.venv/` (managed by UV)
- **Web Framework**: FastAPI with Uvicorn ASGI server

## Key Commands

### Running the Application
```bash
# Start development server
uv run python main.py

# Alternative: Start with uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Package Management
```bash
# Install dependencies
uv sync

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

# Test health check
curl http://localhost:8000/health
```

## API Endpoints

- `GET /` - Returns JSON: `{"message": "Hello World"}`
- `GET /health` - Health check endpoint: `{"status": "healthy", "message": "Smart Notification API is running"}`

## Deployment Configuration

### Railway
- **Configuration**: `railway.toml` with Nixpacks builder
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health` endpoint
- **Deployment**: Connect GitHub repository to Railway for auto-deployment

### Alternative Platforms
- **Procfile**: Available for Heroku-compatible platforms
- **Port Binding**: Uses `$PORT` environment variable for deployment flexibility

## Project Structure

- `main.py` - FastAPI application with root and health endpoints
- `pyproject.toml` - Project configuration and dependencies (FastAPI, Uvicorn)
- `railway.toml` - Railway deployment configuration
- `Procfile` - Alternative platform deployment configuration
- `uv.lock` - Locked dependency versions
- `.python-version` - Python version specification

## Architecture Notes

Simple FastAPI application structure:
- Single module (`main.py`) with FastAPI app instance
- Async route handlers for better I/O performance  
- Health check endpoint for deployment monitoring
- Configured for cloud deployment with environment port binding