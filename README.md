# mad-invoice-mcp

MCP-Server für Rechnungen mit LaTeX-Output (M.A.D. Solutions). Der Server bietet eine schlanke Invoice-API mit Dateispeicher (`.mad_invoice/`) und zwei Kern-Tools:

- `create_invoice_draft(invoice: Invoice)` – legt eine Rechnung als JSON ab und aktualisiert das Index-File.
- `render_invoice_pdf(invoice_id: str)` – rendert eine vorhandene Rechnung per LaTeX-Template zu PDF.

## Schnellstart

```bash
./bin/dev               # erstellt .venv und startet uvicorn auf 127.0.0.1:8000
MCP_ENABLE_WRITES=1 ./bin/dev  # Schreibzugriffe aktivieren
```

Abhängigkeiten:
- Python 3.11+
- `pdflatex` (TeX Live/MiKTeX), damit PDF-Rendern klappt.

## Datenmodell & Speicher

Siehe `bridge/backends/invoices_models.py` (Party, LineItem, Invoice). Persistenz liegt unter `.mad_invoice/`:

```
.mad_invoice/
  invoices/<invoice-id>.json
  index.json
  build/<invoice-id>/invoice.tex|pdf   # erzeugt durch render_invoice_pdf
```

## LaTeX-Template

`templates/invoice.tex` enthält Platzhalter (`%%FOO%%`), die vom Backend ersetzt werden. Anpassungen kannst du direkt dort vornehmen (Logo, Farben, etc.).

## MCP-Tools

Registriert über `bridge/backends/invoices.py`:

- `create_invoice_draft(invoice: Invoice) -> {invoice_path, index_path}`  
  Speichert die Rechnung unter `.mad_invoice/invoices/{id}.json` und schreibt das Index neu.
- `render_invoice_pdf(invoice_id: str) -> {pdf_path, tex_path}`  
  Lädt die Rechnung, füllt das Template und ruft `pdflatex` auf.

Hinweis: Schreibende Tools erfordern `MCP_ENABLE_WRITES=1`.

## Entwicklung

- Anforderungen installieren: `pip install -r requirements.txt`
- Server lokal: `./bin/dev`
- Sandbox-Template für eigene Backends: `bridge/backends/example.py`

## Roadmap

- Web-UI anpassen (aktuell noch RE-KB-Layout, soll eine einfache Invoice-Übersicht werden).
- Optionale Mehrwertsteuer-Logik und Rabatte.
- CI-Tests gegen Beispiel-Invoices.
