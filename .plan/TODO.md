# TODO – mad-invoice-mcp

Dies ist die lebende Aufgabenliste für das Projekt.  
Ziel: schlanker, deterministischer Invoice-MCP-Server mit einfacher Web-UI.

---

## NOW (P1) – Kleine, sinnvolle Erweiterungen

- {MAD-INV-GITIGNORE}
  - Stelle sicher, dass `.mad_invoice/` **nicht** ins Git-Repo committet wird
    (z. B. durch einen Eintrag `/.mad_invoice/` in `.gitignore` im Projektroot).

- {MAD-INV-PAYMENT-STATUS}
  - Erweiterung des `Invoice`-Modells:
    - Füge ein Feld `payment_status` hinzu, z. B.  
      `Literal["open", "paid", "overdue", "cancelled"] = "open"`.
    - Nimm dieses Feld in `to_index_entry()` und damit in `index.json` auf.
  - Ziel: Im Web-UI und via MCP-Tools zwischen offenen und bezahlten Rechnungen unterscheiden können.

- {MAD-INV-LANGUAGE}
  - Erweiterung des `Invoice`-Modells:
    - Füge ein Feld `language: Literal["de", "en"] = "de"` hinzu.
  - Optionaler Follow-up (nicht zwingend sofort):
    - Im Renderer eine kleine Label-Tabelle vorbereiten, um später deutsche/englische
      Textfragmente (z. B. „Rechnung“ vs. „Invoice“) anhand von `invoice.language` zu wählen.

- {MAD-INV-STATUS-TOOL}
  - MCP-Tool `update_invoice_status(invoice_id, payment_status?, status?)` implementieren:
    - Lädt die Rechnung aus `.mad_invoice/invoices/<id>.json`.
    - Aktualisiert nur `status` und/oder `payment_status`.
    - Schreibt die Rechnung zurück und baut `index.json` neu.
    - Beachtet den Write-Gate (`MCP_ENABLE_WRITES`, Logging).

---

## NEXT (P2) – Web-UI für Übersicht & Kontrolle

- {MAD-INV-WEB-OVERVIEW}
  - Eine einfache Übersicht `GET /invoices` bauen:
    - Liest `index.json`.
    - Rendert eine HTML-Tabelle mit Spalten:
      - Rechnungsnummer, Datum, Fällig am,
      - Kunde, Betrag (total + currency),
      - `status`, `payment_status`.
    - Jede Zeile enthält einen Link zur Detailansicht (`/invoices/{id}`).

- {MAD-INV-WEB-DETAIL}
  - Route `GET /invoices/{id}` implementieren:
    - Lädt die Rechnung als `Invoice`.
    - Zeigt Kopf (Nummer, Datum, Fällig, Status, Payment-Status, Kunde).
    - Zeigt Positionen als einfache Tabelle (nur lesend).
    - Prüft, ob unter `.mad_invoice/build/<id>/invoice.pdf` eine PDF existiert und
      blendet entsprechend einen Download-/Öffnen-Link ein.

- {MAD-INV-WEB-ACTIONS}
  - Aktionen als HTTP-POST ergänzen:
    - `POST /invoices/{id}/render`
      - Ruft intern das bestehende MCP-Backend `_render_invoice`/`render_invoice_pdf`
        auf und erzeugt die PDF neu.
      - Redirect zurück auf `/invoices/{id}`.
    - `POST /invoices/{id}/mark-paid`
      - Ruft intern `update_invoice_status(invoice_id, payment_status="paid")` auf.
      - Redirect zurück auf `/invoices/{id}`.

---

## LATER (P3) – Robustheit & Komfort

- {MAD-INV-INVARIANTS}
  - Kleine zusätzliche Guards im `Invoice`-Modell:
    - Optionale Regeln wie „Gesamtbetrag darf bei normalen Rechnungen nicht negativ sein“.
    - Einfache Längenlimits für Freitext-Felder (`description`, `intro_text`, `outro_text`),
      um Ausreißer durch LLM-Fehleingaben zu begrenzen.

- {MAD-INV-TEMPLATE-TOOL}
  - Read-only MCP-Tool `get_invoice_template()` ergänzen:
    - Gibt ein Beispiel-JSON für `Invoice` zurück (mit sinnvollen Defaults),
      das LLMs als Ausgangspunkt zum Ausfüllen verwenden können.

- {MAD-INV-VAT}
  - Optionale Mehrwertsteuer-/Gutschriften-Logik:
    - Erweiterung des Modells um Felder für VAT-Rate / „Kind“ (`invoice` vs. `credit_note`).
    - LaTeX-Template entsprechend erweitern (Netto/USt/Brutto-Blöcke).
    - Nur anpacken, wenn es wirklich gebraucht wird.

---

## DONE

- {MAD-INV-BOOTSTRAP}
  - Projekt aus re-kb-mcp abgeleitet, auf `mad-invoice-mcp` umbenannt,
    Invoice-Modelle (`Party`, `LineItem`, `Invoice`) und LaTeX-Renderer implementiert,
    sowie grundlegende MCP-Tools `create_invoice_draft` und `render_invoice_pdf` hinzugefügt.
***
