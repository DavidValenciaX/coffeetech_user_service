# ---- Build stage ----
FROM python:3.13-alpine@sha256:sha256:81161cb5b87d894a48f667edbfa82121634aa2308ccdf67b86d08c1b6f7fe033 AS build

# Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copia el código fuente y archivos de configuración
WORKDIR /app
COPY . /app

# Instala las dependencias en el entorno virtual
RUN uv sync --frozen --no-cache

# ---- Runtime stage ----
FROM python:3.13-alpine@sha256:sha256:81161cb5b87d894a48f667edbfa82121634aa2308ccdf67b86d08c1b6f7fe033

# Copia uv y el entorno virtual desde la etapa de build
COPY --from=build /bin/uv /bin/uvx /bin/
COPY --from=build /app /app

WORKDIR /app

# Expone el puerto interno 8000
EXPOSE 8000

# Copia el archivo .env para variables de entorno
ENV PYTHONUNBUFFERED=1

# Comando de arranque: usa el puerto interno 8000, el externo se mapea con -p $PORT:8000
CMD ["/app/.venv/bin/fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]
