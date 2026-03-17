# Deployment Guide — AI Student Intelligence Platform

## Local Development (Quick Start)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

### Frontend
```bash
# Option A: Open directly (no build needed)
open frontend/index.html

# Option B: With Vite dev server
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Production Deployment

### Option 1: VPS / Cloud VM (Recommended)

**Backend with Gunicorn + Nginx:**
```bash
# Install
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()" --daemon

# Nginx config (/etc/nginx/sites-available/careerai)
server {
    listen 80;
    server_name yourdomain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /var/www/careerai/frontend;
        try_files $uri /index.html;
    }
}
```

### Option 2: Docker
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["5000:5000"]
    environment:
      - FLASK_ENV=production
    volumes:
      - ./ml_pipeline/models:/app/models

  frontend:
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./frontend:/usr/share/nginx/html
```

```bash
docker-compose up -d
```

### Option 3: Cloud Platforms

**Backend → Render / Railway / Fly.io**
```bash
# render.yaml
services:
  - type: web
    name: careerai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
```

**Frontend → Vercel / Netlify**
```bash
# Just drop the frontend/index.html into Vercel
# Or build with Vite:
cd frontend && npm run build
# Upload dist/ to Vercel
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:
```env
FLASK_ENV=production
PORT=5000
DATABASE_URL=postgresql://user:pass@host:5432/careerai
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## PostgreSQL Setup (Production)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE careerai;
CREATE USER careerai_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE careerai TO careerai_user;
\q

# Run schema
psql -U careerai_user -d careerai -f docs/DATABASE_SCHEMA.md
```

---

## Performance Tips

- Load ML model once at startup (already implemented via singleton)
- Cache scholarship queries with Redis (add flask-caching)
- Use PostgreSQL for production instead of in-memory data
- Enable gzip compression in Nginx
- Serve static files via CDN (Cloudflare)

---

## Monitoring

```bash
# Check backend logs
journalctl -u careerai-backend -f

# Health check
curl http://localhost:5000/api/v1/health
```
