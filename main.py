from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from endpoints import auth, utils
from utils.logger import setup_logger
from endpoints.token import router as token_router

# Setup logging for the entire application
logger = setup_logger()
logger.info("Starting CoffeeTech User Service")

app = FastAPI()

# Montar el directorio 'assets' en la ruta '/static'
app.mount("/static", StaticFiles(directory="assets"), name="static")

# Incluir las rutas de auth con prefijo y etiqueta
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Incluir las rutas de utilidades (roles y unidades de medida)
app.include_router(utils.router, prefix="/utils", tags=["Utilidades"])

# Agregar el router de verificación de tokens
app.include_router(token_router, prefix="/user-service", tags=["token"])

@app.get("/", include_in_schema=False)
def read_root():
    """
    Ruta raíz que retorna un mensaje de bienvenida.

    Returns:
        dict: Un diccionario con un mensaje de bienvenida.
    """
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the FastAPI application CoffeeTech User Service!"}