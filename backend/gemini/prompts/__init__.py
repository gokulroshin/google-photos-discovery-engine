import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))

jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_prompt(template_name: str, **context) -> str:
    """
    Renders a Jinja2 prompt template with the provided context dictionary.
    """
    if not template_name.endswith(".j2"):
        template_name = f"{template_name}.j2"
    template = jinja_env.get_template(template_name)
    return template.render(**context)


__all__ = ["render_prompt", "jinja_env"]
