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

### Running as a systemd service

To run the service in the background as a systemd service:

1. Create a systemd service file:

    ```bash
    sudo nano /etc/systemd/system/coffeetech-user-service.service
    ```

2. Add the following configuration:

    ```ini
    [Unit]
    Description=CoffeeTech User Service
    After=network.target

    [Service]
    Type=simple
    User=root
    Group=root
    WorkingDirectory=/home/projects/coffeetech_services/coffeetech_user_service/
    ExecStart=/root/.local/bin/uv --directory /home/projects/coffeetech_services/coffeetech_user_service/ run fastapi run
    StandardOutput=append:/var/log/coffeetech.out.log
    StandardError=append:/var/log/coffeetech.err.log
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

3. Enable and start the service:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable coffeetech-user-service
    sudo systemctl start coffeetech-user-service
    ```

4. Check the service status:

    ```bash
    sudo systemctl status coffeetech-user-service
    ```

5. View logs:

    ```bash
    tail -f /var/log/coffeetech.out.log
    tail -f /var/log/coffeetech.err.log
    ```

### Updating the Service

To update the running service with the latest changes from the main branch:

1. Navigate to the project directory:

    ```bash
    cd /home/projects/coffeetech_services/coffeetech_user_service/
    ```

2. Pull the latest changes from the repository:

    ```bash
    git pull origin main
    ```

3. Update dependencies if necessary:

    ```bash
    uv sync
    ```

4. Restart the systemd service to apply the changes:

    ```bash
    sudo systemctl restart coffeetech-user-service
    ```
