"""PDF rendering via Jinja2 + WeasyPrint.

Templates live in ``plugins/searchcarriers-ops-reporter/templates/``.
WeasyPrint is imported lazily so the module degrades gracefully when it
is not installed (e.g. in minimal CI environments).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "reports" / "generated"


def report_output_path(report_type: str, dot: str, fmt: str = "pdf") -> Path:
    """Build a deterministic output path for a generated report.

    Example: ``reports/generated/vetting_299569_2026-03-01.pdf``
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return _REPORTS_DIR / f"{report_type}_{dot}_{today}.{fmt}"


def render_pdf(template_name: str, context: dict[str, Any], output_path: Path | str) -> str:
    """Render an HTML template to PDF and write it to *output_path*.

    Args:
        template_name: Filename of the Jinja2 template (e.g. ``vetting_report.html``).
        context: Template context variables.
        output_path: Where to write the PDF file.

    Returns:
        The absolute path of the written PDF as a string.

    Raises:
        RuntimeError: If WeasyPrint or Jinja2 is not installed.
    """
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        raise RuntimeError(
            "jinja2 is required for PDF rendering. Install with: pip install jinja2>=3.1"
        )

    try:
        from weasyprint import HTML
    except ImportError:
        raise RuntimeError(
            "weasyprint is required for PDF rendering. Install with: pip install weasyprint>=62.0"
        )

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template(template_name)
    html_string = template.render(**context)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    HTML(string=html_string).write_pdf(str(output_path))

    return str(output_path.resolve())
