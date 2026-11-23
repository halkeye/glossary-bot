# Glossary Bot

Glossary Bot is a Slack bot that maintains a glossary of terms created by its users, and responds to requests with definitions.

It is a simple web app designed to be used as a [Slack app](https://api.slack.com/apps/).

![DemoGif](https://raw.githubusercontent.com/halkeye/glossary-bot/master/static/gloss-bot-demo.gif)

## Configuration

All Configuration is done by env variables

 * DATABASE_URL - Database url. Only postgresql:// and mysql:// are tested
 * SLACK_APP_TOKEN - [Slack app](https://api.slack.com/apps/) token.
    * Click **Basic Information > App-Level Tokens > Generate Token and Scopes**. Make sure `connections:write` and `authorizations:read` scopes are set. Copy this into `SLACK_APP_TOKEN` variable in Digital Ocean
 * SLACK_BOT_TOKEN - [Slack app](https://api.slack.com/apps/) bot token.
    * Click **OAuth && Permissions**. Copy the `Bot User OAuth Token` and paste the token into `SLACK_BOT_TOKEN` variable in Digital Ocean
 * SLACK_SIGNING_SECRET - [Slack app](https://api.slack.com/apps/) signing token.
    * Should be on the main screen as signing secret
 * SLASH_COMMAND - Listen to a different slash command. By default this is /glossary

The read-only [MCP server](#query-the-glossary-over-mcp) has its own variables:

 * MCP_AUTH_TOKEN - Static bearer token required by the MCP endpoint. The server refuses to start without it.
 * MCP_ALLOWED_HOSTS - Required. Comma-separated `Host` values accepted by the MCP server. Include `host:*` variants when a port may be present; the server refuses to start without it.
 * MCP_ALLOWED_ORIGINS - Optional. Comma-separated `Origin` values for browser-based MCP clients. Non-browser agents do not send an `Origin` header.
 * MCP_USER_NAME - Name recorded in the interactions table for MCP lookups. Defaults to `mcp`.
 * PORT - Port for the MCP server. Defaults to 8080 (Digital Ocean injects this for services).

## Deploy Glossary Bot

Glossary Bot is a [Slack Bolt](https://slack.dev/bolt-python/concepts/) app built to run on any hosting provider. Private or public. Digital Ocean Apps Platform instructions have been provided below. To install the bot locally for development and testing, read [INSTALL](INSTALL.md).

### Set Up on Slack

Glossary Bot uses the new socket support, so it is very easy to setup.

First [create a new app](https://api.slack.com/apps?new_app=1) by copying the [manifest.json](./manifest.json) into the manifest text box.

### Deploy on Digital Ocean

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/halkeye/glossary-bot/tree/master)

Click the button above to get started. In the form that loads, add a name for your bot in the **App Name** field, or leave it blank to have Digitalocean generate a unique name. You won't see this name in Slack, it'll just be part of the URL that Slack uses to communicate with the bot behind the scenes.

And now you're good to get glossing! Open up Slack and type `/glossary help` to start.

## Query the glossary over MCP

The repository also ships a **read-only** [Model Context Protocol](https://modelcontextprotocol.io/) server over Streamable HTTP. It exposes `lookup_term`, `search_terms`, `list_terms`, and `glossary_stats`, so agents can read the glossary without changing it. The Slack bot and the MCP server are separate processes sharing the same database.

### Run locally

```bash
createdb glossary-bot
alembic upgrade head
pip install .

DATABASE_URL=postgresql:///glossary-bot \
MCP_AUTH_TOKEN=test \
MCP_ALLOWED_HOSTS='localhost,localhost:*,127.0.0.1,127.0.0.1:*' \
python -m gloss.mcp_server
```

The endpoint is `http://127.0.0.1:8080/mcp`; `GET /healthz` is an unauthenticated health check. Every `/mcp` request needs `Authorization: Bearer $MCP_AUTH_TOKEN`.

### Deploy on Digital Ocean

The app spec (`.do/deploy.template.yaml`) includes a `glossary-mcp` service alongside the Slack worker. For an already-deployed app, add the service component in the Digital Ocean console:

* Run command: `python -m gloss.mcp_server`
* HTTP port: `8080`
* Health check: `GET /healthz`
* `DATABASE_URL`: the database's **private** URL (same app/VPC)
* `MCP_AUTH_TOKEN`: a secret generated with `openssl rand -hex 32`
* `MCP_ALLOWED_HOSTS`: the generated `<app>.ondigitalocean.app` hostname (and its custom domain, if any)
* `MCP_ALLOWED_ORIGINS`: only needed for browser-based MCP clients (for example `http://localhost:6274` for MCP Inspector); leave empty for CLI agents

Requests will return `421 Invalid Host header` until `MCP_ALLOWED_HOSTS` contains the public hostname. The service refuses to start if either `MCP_AUTH_TOKEN` or `MCP_ALLOWED_HOSTS` is unset, so a misconfigured deployment fails its health check instead of serving a broken endpoint.

Keep `instance_count: 1`: Streamable HTTP sessions are held in process memory. Set `stateless_http=True` in `streamable_http_app()` before scaling out.

### Connect an agent

Claude Code `.mcp.json`:

```json
{
  "mcpServers": {
    "glossary": {
      "type": "http",
      "url": "https://<app>.ondigitalocean.app/mcp",
      "headers": { "Authorization": "Bearer ${GLOSSARY_MCP_TOKEN}" }
    }
  }
}
```

Set `GLOSSARY_MCP_TOKEN` in the environment; never commit the token. Other MCP clients use the same URL and `Authorization` header.

## Releasing

Run the release job

https://github.com/halkeye/glossary-bot/actions/workflows/release.yaml
