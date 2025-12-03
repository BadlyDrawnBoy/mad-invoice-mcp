"""Minimal web UI for invoice overview and detail views."""
from __future__ import annotations

import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from bridge.backends.invoices_storage import (
    get_invoice_root,
    load_invoice,
)
from bridge.backends.invoices import (
    render_invoice_pdf_impl,
    update_invoice_status_impl,
    delete_invoice_draft_impl,
    WritesDisabled,
)
from bridge.utils.config import ENABLE_WRITES

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _load_index_payload() -> dict:
    index_path = get_invoice_root() / "index.json"
    if index_path.is_file():
        with index_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"count": 0, "invoices": []}


async def invoices_overview(request: Request) -> HTMLResponse:
    index = _load_index_payload()
    context = {
        "request": request,
        "invoices": index.get("invoices", []),
        "count": index.get("count", 0),
    }
    return _TEMPLATES.TemplateResponse("invoices_list.html", context)


async def invoice_detail(request: Request) -> Response:
    invoice_id = request.path_params.get("invoice_id")
    if not invoice_id:
        return HTMLResponse("Missing invoice id", status_code=400)

    try:
        invoice = load_invoice(invoice_id)
    except FileNotFoundError:
        return HTMLResponse("Invoice not found", status_code=404)
    except Exception as exc:
        return HTMLResponse(f"Failed to load invoice: {exc}", status_code=500)

    build_dir = get_invoice_root() / "build" / invoice_id
    pdf_path = build_dir / "invoice.pdf"
    pdf_exists = pdf_path.is_file()

    context = {
        "request": request,
        "invoice": invoice,
        "items": invoice.items,
        "pdf_exists": pdf_exists,
        "pdf_path": pdf_path,
    }
    return _TEMPLATES.TemplateResponse("invoice_detail.html", context)


async def render_invoice(request: Request) -> Response:
    invoice_id = request.path_params.get("invoice_id")
    if not ENABLE_WRITES:
        return HTMLResponse("Writes disabled (set MCP_ENABLE_WRITES=1)", status_code=403)
    try:
        render_invoice_pdf_impl(invoice_id)
    except WritesDisabled as exc:
        return HTMLResponse(str(exc), status_code=403)
    except Exception as exc:
        return HTMLResponse(f"Render failed: {exc}", status_code=500)
    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


async def mark_paid(request: Request) -> Response:
    invoice_id = request.path_params.get("invoice_id")
    if not ENABLE_WRITES:
        return HTMLResponse("Writes disabled (set MCP_ENABLE_WRITES=1)", status_code=403)
    try:
        update_invoice_status_impl(invoice_id, payment_status="paid")
    except WritesDisabled as exc:
        return HTMLResponse(str(exc), status_code=403)
    except Exception as exc:
        return HTMLResponse(f"Status update failed: {exc}", status_code=500)
    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


async def finalize_invoice(request: Request) -> Response:
    invoice_id = request.path_params.get("invoice_id")
    if not ENABLE_WRITES:
        return HTMLResponse("Writes disabled (set MCP_ENABLE_WRITES=1)", status_code=403)
    try:
        update_invoice_status_impl(invoice_id, payment_status="open", status="final")
    except WritesDisabled as exc:
        return HTMLResponse(str(exc), status_code=403)
    except Exception as exc:
        return HTMLResponse(f"Finalize failed: {exc}", status_code=500)
    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


async def delete_draft(request: Request) -> Response:
    invoice_id = request.path_params.get("invoice_id")
    if not ENABLE_WRITES:
        return HTMLResponse("Writes disabled (set MCP_ENABLE_WRITES=1)", status_code=403)
    try:
        delete_invoice_draft_impl(invoice_id)
    except WritesDisabled as exc:
        return HTMLResponse(str(exc), status_code=403)
    except Exception as exc:
        return HTMLResponse(f"Delete failed: {exc}", status_code=500)
    return RedirectResponse(url="/invoices", status_code=303)


def register_routes(app: Starlette) -> None:
    routes = [
        Route("/invoices", invoices_overview, methods=["GET"]),
        Route("/invoices/{invoice_id}", invoice_detail, methods=["GET"]),
        Route("/invoices/{invoice_id}/render", render_invoice, methods=["POST"]),
        Route("/invoices/{invoice_id}/mark-paid", mark_paid, methods=["POST"]),
        Route("/invoices/{invoice_id}/finalize", finalize_invoice, methods=["POST"]),
        Route("/invoices/{invoice_id}/delete", delete_draft, methods=["POST"]),
    ]
    for route in routes:
        app.router.routes.append(route)


__all__ = ["register_routes"]
