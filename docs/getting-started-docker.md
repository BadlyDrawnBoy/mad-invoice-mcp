# Docker Quickstart – MAD invoiceMCP

This guide shows how to build and run the MAD invoiceMCP Docker image and mount a directory for your invoices.

It is intentionally short and focused. For a high‑level overview, see [README](../README.md). For client configuration, see [Clients](../docs/clients.md).

---

## 1. Prerequisites

You need:

* **Docker** (or a compatible container runtime) installed on your machine
* A directory on the host where invoice data should live

The image includes:

* a recent Python runtime
* MAD invoiceMCP and its Python dependencies
* a recent TeX Live installation

No external database is required – invoices are stored as JSON files inside the mounted directory.

---

## 2. Build the image

From the repository root, build the image:

```bash
docker build -t mad-invoice-mcp .
```

You only need to rebuild when dependencies or the application code change.

If you prefer a different image name, replace `mad-invoice-mcp` with your own tag and adjust the commands below accordingly.

---

## 3. Run the web UI + API

The default way to run the container is to expose the built‑in web UI on port `8000` and mount a host directory for invoice data.

### 3.1 Basic run command (Linux/macOS)

From the repository root:

```bash
docker run --rm \
  -p 8000:8000 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  -e MCP_ENABLE_WRITES=1 \
  mad-invoice-mcp
```

* `-p 8000:8000` – maps container port 8000 to host port 8000
* `-v $(pwd)/.mad_invoice:/app/.mad_invoice` – persists invoice data under `.mad_invoice/` in your current directory
* `-e MCP_ENABLE_WRITES=1` – enables write‑capable tools (creating and updating invoices)
* `--rm` – removes the container when it exits

Then open the invoices overview in your browser:

```text
http://localhost:8000/invoices
```

### 3.2 Adjusting the volume path (Windows)

On Windows, you can use an absolute path for the data directory, for example:

```bash
docker run --rm -p 8000:8000 \
  -v C:/Users/YourName/mad_invoices/.mad_invoice:/app/.mad_invoice \
  -e MCP_ENABLE_WRITES=1 \
  mad-invoice-mcp
```

Adjust the host path (`C:/Users/YourName/...`) to where you want your invoices stored.

---

## 4. Using Docker with MCP clients (overview)

Some MCP clients can launch the server **inside Docker** instead of using a local Python installation. In these cases, the client runs `docker run` under the hood.

The general pattern looks like this:

```json
{
  "mcpServers": {
    "mad-invoice": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/absolute/path/to/.mad_invoice:/app/.mad_invoice",
        "-e", "MCP_ENABLE_WRITES=1",
        "mad-invoice-mcp",
        "python", "-m", "bridge", "--transport", "stdio"
      ]
    }
  }
}
```

* `docker run` starts the container when the client needs it.
* The host directory is mounted into `/app/.mad_invoice` so invoices persist between runs.
* `python -m bridge --transport stdio` starts the MCP server over stdio inside the container.

For concrete, tested snippets per client (Claude Desktop, Cline, Continue, …), see [Clients](../docs/clients.md).
