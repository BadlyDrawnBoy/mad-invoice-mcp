# MCP Client Configuration

These examples show how to wire MAD invoiceMCP into common MCP clients for everyday and development workflows.

## Claude Desktop (Local)

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

```json
{
      "mcpServers": {
        "mad-invoice": {
          "command": "python",
          "args": ["-m", "bridge", "--transport", "stdio"],
          "cwd": "/absolute/path/to/mad-invoice-mcp",
          "env": {
            "MCP_ENABLE_WRITES": "1"
      }
    }
  }
}
```

**Note:** Replace `/absolute/path/to/mad-invoice-mcp` with your actual project path.

## Claude Desktop (Docker)

For Docker-based setup (no local TeX Live needed):

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

**Important:**
- Build the image first: `docker build -t mad-invoice-mcp .`
- Replace `/absolute/path/to/.mad_invoice` with where you want invoices stored
- On Windows, use: `C:/Users/YourName/.mad_invoice:/app/.mad_invoice`

## Cline / Continue.dev

Similar stdio configuration in your MCP settings:

```json
{
  "mad-invoice": {
    "command": "python",
    "args": ["-m", "bridge", "--transport", "stdio"],
    "cwd": "/absolute/path/to/mad-invoice-mcp",
    "env": {
      "MCP_ENABLE_WRITES": "1"
    }
  }
}
```
