# Tokyo Serene Days landing page

The landing page is intentionally separate from the sourcing system frontend.

- Sourcing system: <http://localhost:5173>
- Landing page: <http://localhost:5174>

## Start with Docker Compose

From the repository root:

```bash
cp .env.example .env # only needed if .env does not exist yet
docker compose up -d --build landing
```

Then open <http://localhost:5174>.

## If the browser says connection refused

`localhost refused to connect` means nothing is listening on port `5174` from the browser's point of view. Check the following in order.

### 1. Confirm the container is running

```bash
docker compose ps landing
```

Expected: the `landing` service is `Up` and maps `0.0.0.0:5174->80/tcp` or `127.0.0.1:5174->80/tcp`.

### 2. Check startup logs

```bash
docker compose logs --tail=80 landing
```

If the image was not built or nginx failed to start, the reason appears here.

### 3. Confirm the port is reachable locally

```bash
curl -i http://localhost:5174
```

Expected: `HTTP/1.1 200 OK` and the landing page HTML.

### 4. Check for a port conflict

```bash
lsof -i :5174
```

If another process already uses `5174`, either stop that process or change the host port in `docker-compose.yml`, for example `5175:80`, and open `http://localhost:5175`.

### 5. If using a remote server or Codespaces-style environment

Opening `http://localhost:5174` on your own computer only works when Docker is running on that same computer. If Docker is running on a remote VM or cloud workspace, use that environment's port-forwarding feature for port `5174`, or open the remote host URL instead of local `localhost`.

## Start without Docker for a quick preview

If Docker is not available, you can preview the static page with Python:

```bash
python3 -m http.server 5174 --directory landing
```

Then open <http://localhost:5174>.

## Verify port separation

After starting the stack, confirm that each port serves the expected page:

```bash
python scripts/check_frontend_identity.py --url http://localhost:5173/ --expect sourcing
python scripts/check_frontend_identity.py --url http://localhost:5174/ --expect landing
```

Expected:

- `http://localhost:5173` serves `JM Camera Sourcing AI`
- `http://localhost:5174` serves `Tokyo Serene Days`
