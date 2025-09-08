# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based smart notification system with PostgreSQL database integration and AI-powered financial news analysis capabilities. The project manages device FCM tokens for push notifications, analyzes stock market news using CrewAI agents, and uses Python 3.13 with UV for dependency management. Configured for Railway deployment with comprehensive environment variable management.

## Development Environment

- **Python Version**: 3.13 (specified in `.python-version`)
- **Package Manager**: UV (modern Python package manager)
- **Virtual Environment**: `.venv/` (managed by UV)
- **Web Framework**: FastAPI with Uvicorn ASGI server
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Environment Management**: python-dotenv for .env files
- **AI Framework**: CrewAI with OpenAI GPT-4o
- **Web Scraping**: Firecrawl API for dynamic content extraction

## Key Commands

### Environment Setup
```bash
# Copy environment template and configure
cp .env.example .env
# Edit .env with your database credentials, OpenAI API key, and Firecrawl API key

# Install dependencies
uv sync
```

### Running the Application
```bash
# Start FastAPI development server (loads .env automatically)
uv run python main.py

# Alternative: Start with uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run AI news analysis system
uv run python crew_news_analysis.py
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
  -d '{"device_uuid": "unique-device-id", "fcm_token": "your_fcm_token_here"}'

# Get all active devices
curl http://localhost:8000/devices
```

## Application Architecture

### FastAPI Service (`main.py`)
- **Purpose**: Device registration and notification management API
- **Database Integration**: Auto-creates tables on startup using SQLAlchemy
- **Health Monitoring**: Database connectivity checks via `/health` endpoint
- **Device Management**: FCM token registration and retrieval for push notifications

### AI News Analysis System (`crew_news_analysis.py`)
- **Purpose**: Autonomous financial news collection and impact analysis
- **Data Sources**: RSS feeds (Yahoo Finance, CNBC, MarketWatch) + web scraping (Firecrawl)
- **AI Agents**: Multi-agent system using CrewAI framework with GPT-4o
  - News Collector: Aggregates from multiple financial sources
  - Impact Evaluator: Quantitative analysis with 1-10 scoring system
  - Impact Filter: Filters for actionable, market-moving events
  - Data Formatter: Structures output as production-ready JSON
- **Output**: Structured JSON with impact scores, affected tickers, confidence levels, and trading insights

### Database Layer
- **Models** (`models.py`): Device model with UUID-based primary keys
- **Connection** (`database.py`): SQLAlchemy session management with dependency injection
- **Auto-Migration**: Tables created automatically on application startup

## API Endpoints

- `GET /` - Returns JSON: `{"message": "Hello World"}`
- `GET /health` - Health check with database connectivity status
- `POST /devices` - Register/update device with FCM token (accepts device_uuid + fcm_token)
- `GET /devices` - Retrieve all active devices for notification targeting

## Required Environment Variables

### FastAPI Service
```bash
DATABASE_URL=postgresql://user:pass@host:port/db  # Railway auto-provides this
# Local development fallback to SQLite in database.py
```

### AI News Analysis
```bash
OPENAI_API_KEY=sk-proj-...  # GPT-4o access for CrewAI agents
FIRECRAWL_API_KEY=fc-...    # Web scraping for dynamic financial news sites
```

## Deployment Configuration

### Railway (Primary)
- **Configuration**: `railway.toml` with Nixpacks builder
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Database**: Railway PostgreSQL addon provides `DATABASE_URL`
- **Health Check**: `/health` endpoint with 100s timeout
- **Auto-Restart**: Always restart policy for production reliability

### Alternative Platforms
- **Procfile**: Available for Heroku-compatible platforms
- **Environment Variables**: Uses `DATABASE_URL` and `$PORT`

## AI System Architecture

The news analysis system implements a sophisticated multi-agent workflow:

1. **Data Collection Phase**: Parallel collection from RSS feeds and dynamic web scraping
2. **Content Processing**: Deduplication and relevance filtering using keyword matching
3. **Impact Analysis**: Quantitative scoring (1-10) with confidence levels and affected assets
4. **Filtering**: High-impact selection (score ≥7, large-cap focus, >3% price movement potential)
5. **Structured Output**: Production-ready JSON with tickers, sectors, timeframes, and trading strategies

### Integration Points
- The AI system runs independently but could be integrated with the FastAPI service for automated notifications
- Output format is designed for database storage and API consumption
- Supports both immediate analysis and scheduled execution

## Development Notes

- **Database**: Supports both PostgreSQL (production) and SQLite (local development)
- **Environment Loading**: All services use python-dotenv for configuration management
- **API Keys**: Never commit to repository - use .env files with .gitignore protection
- **Firecrawl Integration**: Uses updated v2 API with Document objects (not dictionary responses)
- **Error Handling**: Comprehensive exception handling in both FastAPI and AI analysis systems