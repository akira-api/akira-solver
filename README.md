# Akira Solver

> Cloudflare Turnstile solver API, built for the [Akira API](https://github.com/akira-api) ecosystem.

Akira Solver is a Python-based Cloudflare Turnstile bypass project from the Akira group.
It is a separate implementation from [akira-turnstile](https://github.com/akira-api/akira-turnstile), which was written in Go.

This version is intentionally simple, readable, and easy to maintain.
It uses `pydoll` to control Chromium and return cookies after solving a target page.

## Highlights

- Python implementation
- Clear and easy-to-follow code
- Chromium automation through `pydoll`
- FastAPI docs at `/docs` and `/redoc`
- Docker Compose support with `cloudflared`

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker Compose

```bash
docker compose up --build
```

Set `CLOUDFLARED_TOKEN` and `API_KEY` in `.env` before starting Compose.

All `/api/*` requests must include `x-api-key` or `x-api-keys` with the value from `API_KEY`.

## Without Cloudflare Tunnel

By default, the compose stack runs a `cloudflared` sidecar alongside the solver.

> **Why `cloudflared`?**  
> NAT VPS, no public IP, no open ports. `cloudflared` handles ingress so we do not have to.  
> If your server has a real public IP, skip the tunnel entirely.

To expose the port directly instead, make two changes in `docker-compose.yml`.

**1. Replace `expose` with `ports` on the `solver` service.**

```yaml
# tunnel mode (default) - port stays private, cloudflared handles ingress
expose:
  - "8000"

# direct port mode - bind straight to the host
ports:
  - "8000:8000"
```

**2. Remove or comment out the `cloudflared` service block.**

```yaml
# cloudflared:
#   image: cloudflare/cloudflared:latest
#   container_name: solver-cloudflared
#   restart: unless-stopped
#   depends_on:
#     - solver
#   command: tunnel --no-autoupdate run --token ${CLOUDFLARED_TOKEN}
#   networks:
#     - akira-net
```

> You can also drop `CLOUDFLARED_TOKEN` from your `.env` - it will not be referenced.

## License

See [LICENSE](LICENSE).
