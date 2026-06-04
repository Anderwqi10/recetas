# Recetas — inventario + recetas con LLM

Aplicación web para registrar ingredientes en casa, generar recetas con un modelo de lenguaje (OpenRouter) y gestionarlas (calificar, guardar, eliminar).

## Requisitos

- Python 3.11+
- Cuenta en [OpenRouter](https://openrouter.ai/) y API key

## Instalación

```bash
cd recetas
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env y pon OPENROUTER_API_KEY y SECRET_KEY
```

## Ejecutar

```bash
uvicorn app.main:app --reload
```

Abre http://127.0.0.1:8000 — regístrate, añade ingredientes en el panel y pulsa **Generar receta con IA**.

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave para firmar JWT |
| `DATABASE_URL` | Por defecto `sqlite:///./recetas.db` |
| `OPENROUTER_API_KEY` | API key de OpenRouter |
| `OPENROUTER_MODEL` | Modelo (ej. `openai/gpt-4o-mini`) |

## API principal

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/ingredients` | Añadir ingrediente |
| GET | `/api/ingredients` | Listar inventario |
| DELETE | `/api/ingredients/{id}` | Eliminar ingrediente |
| POST | `/api/recipes/generate` | Generar receta (LLM) |
| GET | `/api/recipes` | Listar recetas (`?saved_only=true`) |
| PATCH | `/api/recipes/{id}` | Calificar / guardar |
| DELETE | `/api/recipes/{id}` | Eliminar receta |

Autenticación: cookie en la web o `Authorization: Bearer <token>` (ver `/api/login`).

## Pruebas

```bash
pytest -v
```

Incluye `pytest.ini` con al menos 18 pruebas que cubren:

- Validación de ingredientes
- Construcción del prompt para el LLM
- Parseo de la respuesta del LLM
- Endpoints de la API (ingredientes, generación, calificación, borrado)
