# MAD invoiceMCP server
*_Mechatronics Advisory & Design (M.A.D. Solutions) – JSON → LaTeX → PDF invoicing server with local file storage._*

<img width="2048" height="786" alt="logo" src="https://github.com/user-attachments/assets/203a5a7b-4802-4edc-8250-ddaf7143186c" />

## What is this?

MAD invoiceMCP is a small Model Context Protocol (MCP) server that lets you create, store, and render invoices for a **single company** using JSON data and LaTeX templates.

It is designed for local, single‑user workflows:

* one repository and one `.mad_invoice/` data directory
* no multi‑tenant or multi‑project switching
* no external database or cloud backend

**Best fit:** freelancers and small businesses who want to generate invoices on their own machine.

**Not designed as:**

* a multi‑tenant system for tax advisors or agencies with many clients
* a hosted SaaS product
* a full accounting or ERP system

---

## Key features

* JSON → LaTeX → PDF invoice rendering pipeline
* draft → final lifecycle with immutable final invoices
* payment status tracking (`open`, `paid`, `overdue`, `cancelled`)
* optional VAT handling and German §19 UStG ("small business") mode
* language‑aware labels and dates (German / English)
* simple web overview and detail pages for existing invoices
* MCP tools for listing, reading, updating, and rendering invoices

---

## Requirements

* **Python**: 3.10 or newer (tested with 3.11)
* **LaTeX**: a recent TeX Live release (2024 or newer recommended)

  * or use the Docker image, which already includes TeX Live
* **Optional:** Docker, if you prefer not to manage Python and LaTeX locally

Write‑capable tools are disabled by default. To allow creating or updating invoices, set:

```bash
export MCP_ENABLE_WRITES=1
```

---

## Quickstart

### Option A – Docker (recommended for a first try)

From the repository root:

```bash
docker build -t mad-invoice-mcp .
docker run --rm \
  -p 8000:8000 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  -e MCP_ENABLE_WRITES=1 \
  mad-invoice-mcp
```

Then open the web UI in your browser:

```text
http://localhost:8000/invoices
```

The container image already includes a recent TeX Live installation, so you do not need LaTeX on the host.

---

### Option B – Local MCP server (stdio)

Use this path if you have a compatible TeX Live installation on your machine.

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start the MCP server over stdio:

   ```bash
   MCP_ENABLE_WRITES=1 python -m bridge --transport stdio
   ```

Most MCP‑capable clients (Claude Desktop, Cline, Continue, etc.) can then be pointed at this server using their standard `command`/`args` configuration. See [MCP client configuration](docs/clients.md) for concrete examples.

---

## Where to go next

* [Concepts & storage model](docs/concepts.md)
* [Docker details](docs/getting-started-docker.md)
* [MCP client configuration](docs/clients.md)
* [Tools reference](docs/tools.md)
* [Advanced deployment (SSE, OpenWebUI, systemd, reverse proxy)](docs/advanced.md)

---

## Code generation notice

Most of this repository's code was originally produced with AI assistants. The project is maintained and reviewed by a human, but you should still treat it as experimental software and review it carefully before using it in production.

---

## License

See [LICENCE](LICENSE) for licensing details.
