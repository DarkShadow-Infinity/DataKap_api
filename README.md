# DataKap API

This repository provides a FastAPI-based reference implementation of the DataKap backend specification.

## Requisitos previos

- Python 3.10 o superior.
- `pip` y `virtualenv` instalados.
- Opcional: [HTTPie](https://httpie.io/) o [curl](https://curl.se/) para probar los endpoints.

## Puesta en marcha paso a paso

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/DataKap_api.git
   cd DataKap_api
   ```
2. **Crear y activar un entorno virtual** (recomendado)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```
3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```
4. **Verificar que el código compile**
   ```bash
   python -m compileall app
   ```
5. **Levantar el servidor en modo desarrollo**
   ```bash
   uvicorn app.main:app --reload
   ```

Con esto tendrás disponible la documentación interactiva de la API en `http://127.0.0.1:8000/docs` y el archivo JSON de OpenAPI en `http://127.0.0.1:8000/openapi.json`.

## Credenciales y datos de prueba

La base de datos en memoria se inicializa con los siguientes usuarios:

| Rol      | Email               | Contraseña    |
|----------|---------------------|---------------|
| Admin    | `admin@datakap.mx`  | `Admin#2025`  |
| Líder    | `leader@datakap.mx` | `Leader#2025` |
| Promotor | `promoter@datakap.mx` | `Promoter#2025` |

Ejemplo para autenticar con HTTPie:

```bash
http POST :8000/auth/login email=admin@datakap.mx password=Admin#2025
```

El archivo `app/storage.py` contiene el sembrado de datos y puedes modificarlo para agregar más usuarios o registros.

## Flujo sugerido de validación manual

1. Inicia sesión con alguno de los usuarios de prueba.
2. Consume `GET /profile` usando el token obtenido.
3. Crea registros con `POST /registrations` y verifica el resultado en `GET /registrations`.
4. Simula sincronizaciones offline con `POST /registrations/sync`.
5. Explora los endpoints de administración (`/admin/users`, `/admin/dashboard/summary`).

Cada endpoint expuesto por `app/main.py` replica la especificación descrita en el documento del proyecto.

## IDEs recomendados

El proyecto es pequeño y funciona bien en cualquier editor, pero estas opciones facilitan el flujo de trabajo:

- **Visual Studio Code** con las extensiones *Python*, *Pylance* y *REST Client*. Permite depurar FastAPI, ejecutar tareas desde la terminal integrada y documentar solicitudes HTTP.
- **PyCharm Community/Professional** si prefieres un entorno especializado para Python. Ofrece creación automática de entornos virtuales, inspecciones de código y depuración integrada.

Ambos IDEs soportan `uvicorn` con recarga automática (`--reload`), por lo que los cambios en los módulos `app/` se reflejarán sin reiniciar manualmente.

## Project structure

- `app/schemas.py` – Pydantic models representing request and response payloads.
- `app/storage.py` – In-memory storage used to simulate persistence and authentication.
- `app/auth.py` – Dependency helpers for token-based authentication.
- `app/main.py` – FastAPI routes implementing the endpoints described in the specification.

The implementation favors readability and mirrors the behavior expected by the mobile application while keeping the persistence layer lightweight for demonstration purposes.
