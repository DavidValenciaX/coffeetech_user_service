# CoffeeTech User Service

This service handles user authentication and management for the CoffeeTech platform.

## Prerequisites

- Python 3.13+
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) package manager
- FastAPI
- SQLAlchemy

## Database Setup

The service connects to a PostgreSQL database using environment variables defined in the `.env` file:

```env
PGHOST=your-host
PGPORT=your-port
PGDATABASE=your_database_name
PGUSER=postgresql-database-user
PGPASSWORD=your_password
```

Configure these environment variables according to your database setup before running the service.

## Installing Dependencies

To install dependencies, run:

```bash
uv sync
```

## Running the Service (Development)

To run the service in development mode:

```bash
uv run fastapi dev
```

## Running the Service (Production)

For production environments, use:

```bash
uv run fastapi run
```

## Docker Deployment

To build and run the service with Docker:

```bash
docker build -t coffeetech-user-service .
docker run -p 8000:8000 --env-file .env coffeetech-user-service
```

This will expose the service at [http://localhost:8000](http://localhost:8000).

## Project Structure

```bash
user_service/
├── main.py
├── dataBase.py
├── endpoints/
├── utils/
├── pyproject.toml
├── .env
├── Dockerfile
└── ...
```

## Notes

- The Dockerfile uses `uv` for dependency management and runs FastAPI directly.
- The `.dockerignore` file is used to exclude unnecessary files from the Docker build context.
