from pathlib import Path

from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    template = env.get_template(name)
    return HTMLResponse(template.render(**context), status_code=status_code)
