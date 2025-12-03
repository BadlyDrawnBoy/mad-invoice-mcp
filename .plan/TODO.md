# TODO – mad-invoice-mcp

> Siehe `.plan/ORIENTATION.md` und `README.md` für Kontext zum Projekt.  

## NOW (P1) – Kernfunktionen abrunden

- {MAD-INV-ROOT}
  - Ergänze eine optionale Env-Variable `MAD_INVOICE_ROOT` in `invoices_storage.get_invoice_root()`, so dass der Speicherort von `.mad_invoice/` explizit gesetzt werden kann (Fallback: `Path.cwd() / ".mad_invoice"`).
- {MAD-INV-PAYMENT-STATUS}
  - Erweitere das `Invoice`-Modell um ein Feld `payment_status` (z. B. `"open" | "paid" | "overdue" | "cancelled"`) und nimm es in `to_index_entry()` / `index.json` auf.  
- {MAD-INV-STATUS-TOOL}
  - Implementiere ein MCP-Tool `update_invoice_status(invoice_id, payment_status, status?)`, das eine Rechnung lädt, Felder aktualisiert, speichert und den Index neu schreibt (unter Beachtung der Write-Gates).

## NEXT (P2) – Web-UI für Übersicht & Kontrolle

- {MAD-INV-WEB-OVERVIEW}
  - Baue eine einfache Übersicht `GET /invoices`, die `index.json` liest und eine HTML-Tabelle mit Rechnungsnummer, Datum, Fällig am, Kunde, Betrag, `status`, `payment_status` anzeigt.
- {MAD-INV-WEB-DETAIL}
  - Implementiere `GET /invoices/{id}` für eine Detailansicht:
    - Kopf mit Meta-Daten (Nummer, Datum, Fällig, Status, Payment-Status).
    - Liste der Positionen (nur lesend).
    - Hinweis, ob ein PDF existiert.
- {MAD-INV-WEB-ACTIONS}
  - Ergänze einfache Aktionen:
    - `POST /invoices/{id}/render` → ruft intern `render_invoice_pdf(invoice_id)` auf.
    - `POST /invoices/{id}/mark-paid` → ruft intern das Status-Tool mit `payment_status="paid"` auf.
  - Danach zurück auf die Detailseite redirecten.

## LATER (P3) – Komfort & Extras

- {MAD-INV-WEB-STYLE}
  - Web-UI optisch aufhübschen (Basis-CSS, evtl. leichte JS-Verbesserungen), ohne die Architektur zu verkomplizieren.
- {MAD-INV-VAT}
  - Optionale Mehrwertsteuer-Logik ergänzen (wenn Kleinunternehmer-Status wegfallen sollte): Netto/USt/Brutto-Berechnungen + Template-Erweiterung.
- {MAD-INV-DOCS}
  - Kurze Dokumentation ergänzen:
    - Beispiel-JSON für `Invoice`,
    - Beispiel-Workflow mit OpenWebUI (Prompt → Tool-Call → PDF),
    - Hinweise zu `MAD_INVOICE_ROOT` und Web-UI.

## DONE

- {MAD-INV-BOOTSTRAP}
  - Projekt von re-kb-mcp abgeleitet, auf `mad-invoice-mcp` umgelabelt und ein Invoice-Backend mit LaTeX-Template implementiert (`create_invoice_draft`, `render_invoice_pdf`).
