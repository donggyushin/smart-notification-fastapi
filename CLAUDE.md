# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based smart notification system currently in early development stage. The project uses Python 3.13 and UV for dependency management.

## Development Environment

- **Python Version**: 3.13 (specified in `.python-version`)
- **Package Manager**: UV (modern Python package manager)
- **Virtual Environment**: `.venv/` (managed by UV)

## Key Commands

### Running the Application
```bash
python main.py
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

### Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Or use UV to run commands in the virtual environment
uv run python main.py
```

## Project Structure

- `main.py` - Entry point with basic "Hello World" functionality
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions
- `.python-version` - Python version specification for pyenv/UV

## Architecture Notes

The project is currently minimal with just a basic entry point. As a FastAPI project, future development should follow typical FastAPI patterns:
- API routes in separate modules
- Dependency injection for services
- Pydantic models for request/response validation
- Async/await patterns for I/O operations