# CoffeeTech User Service

This service handles user authentication and management for the CoffeeTech platform.

## Prerequisites

- Python 3.8+
- PostgreSQL
- UV package manager
- FastAPI
- SQLAlchemy

## Database Setup

The service connects to a PostgreSQL database using environment variables defined in the `.env` file:

```bash
PGHOST=your-host
PGPORT=your-port
PGDATABASE=your_database_name
PGUSER=postgresql-database-user
PGPASSWORD=your_password
```

Configure these environment variables according to your database setup before running the service.

To install dependencies:

```bash
uv sync
```

## Running the Service

To run the service in development mode:

```bash
uv run fastapi dev
```

## Production Deployment

For production environments, use:

```bash
uv run fastapi run
```
