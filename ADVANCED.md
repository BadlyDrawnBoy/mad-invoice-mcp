# Advanced Usage – mad-invoice-mcp

This document covers advanced deployment scenarios, alternative transports, and production considerations.

For basic setup, see [README.md](README.md).

---

## Table of Contents

- [SSE Transport (HTTP-based MCP)](#sse-transport-http-based-mcp)
- [OpenWebUI Integration](#openwebui-integration)
- [Production Deployment](#production-deployment)
- [Multi-Client Scenarios](#multi-client-scenarios)
- [Performance Tuning](#performance-tuning)
- [Security Considerations](#security-considerations)

---

## SSE Transport (HTTP-based MCP)

The SSE (Server-Sent Events) transport allows MCP clients to connect over HTTP instead of stdio.

### Starting the SSE Server

```bash
# Local setup
MCP_ENABLE_WRITES=1 python -m bridge.cli --transport sse --host 127.0.0.1 --port 8100

# Docker setup
docker run --rm -p 8100:8100 \
  -e MCP_ENABLE_WRITES=1 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  mad-invoice-mcp \
  python -m bridge.cli --transport sse --host 0.0.0.0 --port 8100
```

### MCP Client Configuration

For clients that support HTTP/SSE:

```json
{
  "mcpServers": {
    "mad-invoice": {
      "url": "http://localhost:8100/sse"
    }
  }
}
```

**Use cases:**
- Remote MCP server access
- Load balancing across multiple servers
- Integration with web-based LLM frontends

---

## OpenWebUI Integration

OpenWebUI supports MCP servers via the `x-openwebui-mcp` extension. The shim proxies MCP protocol directly - no schema conversion needed!

### Setup

**1. Start the MCP server with SSE transport:**

```bash
MCP_ENABLE_WRITES=1 python -m bridge.cli --transport sse
```

This starts:
- **MCP SSE Server** on `http://127.0.0.1:8099` (internal)
- **OpenWebUI Shim** on `http://127.0.0.1:8081` (for OpenWebUI)

**Custom ports:**
```bash
MCP_ENABLE_WRITES=1 python -m bridge.cli --transport sse \
  --mcp-port 8199 \
  --shim-port 8181
```

**2. Configure OpenWebUI:**

In OpenWebUI, add a new MCP connection:
- **URL**: `http://127.0.0.1:8081/openapi.json`
- **Name**: `MAD Invoice MCP`
- **Description**: `Create and manage invoices with PDF generation`

OpenWebUI will:
1. Fetch `/openapi.json` and detect `x-openwebui-mcp` extension
2. Connect via MCP protocol to `/sse` and `/messages` endpoints
3. Automatically discover all available tools

### Available Tools in OpenWebUI

Once connected, you'll have access to:
- `create_invoice_draft` - Create new invoice
- `update_invoice_draft` - Edit draft invoices
- `delete_invoice_draft` - Remove draft invoices
- `update_invoice_status` - Change status (draft→final, open→paid)
- `render_invoice_pdf` - Generate PDF from invoice
- `generate_invoice_number` - Get next invoice number
- `get_invoice_template` - View example invoice structure

### Docker Setup

```bash
# Build image
docker build -t mad-invoice-mcp .

# Run with SSE transport
docker run --rm -p 8081:8081 -p 8099:8099 \
  -e MCP_ENABLE_WRITES=1 \
  -v $(pwd)/.mad_invoice:/app/.mad_invoice \
  mad-invoice-mcp \
  python -m bridge.cli --transport sse \
    --mcp-host 0.0.0.0 \
    --shim-host 0.0.0.0
```

Connect OpenWebUI to `http://localhost:8081/openapi.json`

### Usage Example

In OpenWebUI chat:

```
You: Create an invoice for Acme Corp for 5 hours of consulting at €120/hour

AI: [calls create_invoice_draft tool]
    Created invoice 2025-0003 for Acme Corp.
    Subtotal: €600.00

You: Generate the PDF

AI: [calls render_invoice_pdf tool]
    PDF generated at: .mad_invoice/build/2025-0003/invoice.pdf
```

---

## Production Deployment

### Environment Variables

```bash
# Required
MCP_ENABLE_WRITES=1          # Enable write operations

# Optional
MAD_INVOICE_ROOT=/data/invoices    # Custom storage location
PDFLATEX_PATH=/usr/bin/pdflatex   # Override pdflatex discovery
```

### Systemd Service (Local)

Create `/etc/systemd/system/mad-invoice-mcp.service`:

```ini
[Unit]
Description=MAD Invoice MCP Server
After=network.target

[Service]
Type=simple
User=invoice
WorkingDirectory=/opt/mad-invoice-mcp
Environment="MCP_ENABLE_WRITES=1"
Environment="MAD_INVOICE_ROOT=/var/lib/mad-invoice"
ExecStart=/opt/mad-invoice-mcp/.venv/bin/python -m bridge.cli --transport sse --host 127.0.0.1 --port 8100
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mad-invoice-mcp
sudo systemctl start mad-invoice-mcp
```

### Docker Compose

```yaml
version: '3.8'

services:
  mad-invoice-mcp:
    image: mad-invoice-mcp:latest
    build: .
    ports:
      - "8100:8100"
    volumes:
      - ./invoices:/app/.mad_invoice
    environment:
      - MCP_ENABLE_WRITES=1
      - UVICORN_HOST=0.0.0.0
      - UVICORN_PORT=8100
    restart: unless-stopped
    command: python -m bridge.cli --transport sse --host 0.0.0.0 --port 8100
```

Start with:
```bash
docker-compose up -d
```

### Reverse Proxy (nginx)

For exposing SSE endpoint behind nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name invoice-mcp.example.com;

    ssl_certificate /etc/letsencrypt/live/invoice-mcp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/invoice-mcp.example.com/privkey.pem;

    location /sse {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE specific
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }

    location /invoices {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Multi-Client Scenarios

The invoice system uses file-based locking to handle concurrent access safely.

### Concurrency Guarantees

✅ **Safe operations:**
- Multiple clients reading invoices simultaneously
- Concurrent invoice creation (with unique IDs)
- Invoice number generation (atomic with `.sequence.lock`)
- Index rebuilds (atomic with `.index.lock`)

⚠️ **Potential conflicts:**
- Two clients editing the same draft simultaneously (last write wins)
- High-frequency invoice number generation (lock contention possible)

### Recommended Patterns

**Single-Writer, Multiple-Readers:**
```bash
# Production: One MCP server handles all writes
MCP_ENABLE_WRITES=1 python -m bridge.cli --transport sse --port 8100

# Read-only clients can connect via Web UI
python -m uvicorn bridge.app:create_app --factory --port 8000
```

**Load Balancing (Read-Heavy):**
- Multiple Web UI instances (read-only)
- Single MCP server for write operations
- Shared storage via NFS/network mount

---

## Performance Tuning

### Invoice Storage

For large invoice volumes (>10,000 invoices), consider:

1. **Separate storage backend** (currently file-based JSON)
2. **Index caching** (rebuild on demand instead of every write)
3. **Archival strategy** (move finalized invoices older than X years)

### PDF Generation

pdflatex can be slow for complex templates. Optimizations:

1. **Use Docker image** (TeX Live 2025 is faster than 2022)
2. **Parallel rendering** (if generating multiple PDFs)
3. **Pre-compile fonts** (lmodern is already optimized)

### Lock Contention

If you see timeout errors with concurrent invoice number generation:

1. Increase timeout in `with_sequence_lock()` (default: 5s)
2. Batch invoice creation instead of one-by-one
3. Consider pre-allocated number ranges per client

---

## Security Considerations

### Write Access Control

The `MCP_ENABLE_WRITES` environment variable is a basic safety mechanism. For production:

1. **Use authentication** on SSE endpoint (nginx basic auth, API keys)
2. **Restrict network access** (bind to 127.0.0.1 for local-only)
3. **Validate invoice data** (models use Pydantic with strict validation)

### Data Privacy

Invoices contain sensitive business data:

1. **Encrypt storage volume** (LUKS, dm-crypt for Linux)
2. **Backup strategy** (regular encrypted backups of `.mad_invoice/`)
3. **Access logging** (track who creates/modifies invoices)

### PDF Security

Generated PDFs may contain:
- Personal information (names, addresses)
- Tax IDs and bank details
- Business transaction details

Consider:
1. **PDF encryption** (not currently implemented - future feature)
2. **Watermarking** for drafts vs. final invoices
3. **Access control** for PDF files on disk

---

## Troubleshooting

### Lock Timeouts

```
portalocker.exceptions.LockException: Failed to acquire lock
```

**Cause:** Another process holds the lock for >5 seconds.

**Solutions:**
- Check for stuck processes: `ps aux | grep bridge.cli`
- Remove stale locks: `rm .mad_invoice/.*.lock`
- Increase timeout in code (edit `invoices_storage.py`)

### pdflatex Errors

```
ToolError: pdflatex failed with exit code 1
```

**Debug steps:**
1. Check `.mad_invoice/build/<invoice-id>/invoice.log` for LaTeX errors
2. Test pdflatex manually: `pdflatex invoice.tex`
3. Verify TeX Live installation: `pdflatex --version`

### Storage Permission Issues

```
PermissionError: [Errno 13] Permission denied: '.mad_invoice/invoices/...'
```

**Solutions:**
- Check directory ownership: `ls -la .mad_invoice`
- Fix permissions: `chmod -R u+rw .mad_invoice`
- For Docker: ensure volume mount has correct UID/GID

---

## Contributing

See main [README.md](README.md) for development setup and contribution guidelines.

For questions or issues with advanced configurations, open an issue on GitHub.
