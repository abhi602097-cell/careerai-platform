# Free Deployment Guide — CareerAI Platform
# Get a live public URL in under 15 minutes

---

## ARCHITECTURE

```
  YOUR LAPTOP
      │
      ├── frontend/index.html  ──►  Netlify (FREE)  ──►  https://careerai.netlify.app
      │
      └── backend/             ──►  Render  (FREE)  ──►  https://careerai-backend.onrender.com
                                         │
                                    best_model.pkl
                                    (uploaded to repo)
```

Both are 100% free. No credit card needed.

---

## OPTION 1 — RENDER (Backend) + NETLIFY (Frontend)
### Best choice. Free tier. Permanent URL.

---

### STEP 1 — Push to GitHub

1. Go to https://github.com → Sign in (or create free account)
2. Click "New repository" → Name it: `careerai-platform` → Public → Create
3. On your computer, unzip the downloaded ZIP, then run:

```bash
cd CareerAI_Platform

# Initialize git
git init
git add .
git commit -m "Initial commit — CareerAI Platform"

# Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/careerai-platform.git
git branch -M main
git push -u origin main
```

⚠️  The ML model files (.pkl) are ~5MB. If git push fails due to size:
```bash
# Install Git LFS (one time)
git lfs install
git lfs track "*.pkl"
git add .gitattributes
git add .
git commit -m "Add LFS tracking"
git push -u origin main
```

---

### STEP 2 — Deploy Backend on Render (FREE)

1. Go to https://render.com → Sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account → Select `careerai-platform` repo
4. Fill in the settings:

```
Name:          careerai-backend
Region:        Singapore (closest for India)
Branch:        main
Root Directory: backend
Runtime:       Python 3
Build Command:  pip install -r requirements.txt
Start Command:  gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 "app:create_app()"
Plan:          Free
```

5. Click **"Create Web Service"**
6. Wait 3–5 minutes for first deploy
7. Your backend URL will be:
   ```
   https://careerai-backend.onrender.com
   ```
8. Test it: open `https://careerai-backend.onrender.com/api/v1/health`
   → Should return: `{"status":"success","data":{"status":"healthy"}}`

⚠️  Free tier sleeps after 15 minutes of inactivity. First request takes ~30s to wake up.
    Upgrade to $7/month Starter plan to keep it always-on.

---

### STEP 3 — Connect Frontend to Backend

1. Open `frontend/index.html` in any text editor
2. Find this line near the top (around line 200):
   ```javascript
   const API_BASE = null;
   ```
3. Change it to your Render URL:
   ```javascript
   const API_BASE = 'https://careerai-backend.onrender.com/api/v1';
   ```
4. Save the file

---

### STEP 4 — Deploy Frontend on Netlify (FREE)

**Method A — Drag and Drop (easiest, 30 seconds):**
1. Go to https://netlify.com → Sign up free
2. Drag and drop the `frontend/` folder onto the Netlify dashboard
3. Done! You get a URL like: `https://wonderful-mcclintock-abc123.netlify.app`

**Method B — From GitHub (auto-deploys on every push):**
1. Go to https://netlify.com → "Add new site" → "Import from Git"
2. Select `careerai-platform` repo
3. Settings:
   ```
   Base directory:    frontend
   Build command:     (leave empty)
   Publish directory: frontend
   ```
4. Click "Deploy site"

**Custom domain (optional, free):**
- Site settings → Domain management → Add custom domain
- Works with any domain you own

---

### STEP 5 — Set CORS on Backend

In Render dashboard → Your service → Environment:
Add environment variable:
```
Key:   ALLOWED_ORIGINS
Value: https://your-site-name.netlify.app
```
Click "Save Changes" → Render redeploys automatically.

---

## YOUR LIVE URLS

After completing the steps above:

| Service   | URL |
|-----------|-----|
| Frontend  | `https://your-site.netlify.app` |
| Backend   | `https://careerai-backend.onrender.com` |
| API docs  | `https://careerai-backend.onrender.com/` |
| Health    | `https://careerai-backend.onrender.com/api/v1/health` |
| Predict   | `POST https://careerai-backend.onrender.com/api/v1/predict` |

---

## OPTION 2 — RAILWAY (Backend + Frontend in one place)
### Slightly simpler. $5 free credits/month.

1. Go to https://railway.app → Sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select `careerai-platform`
4. Railway auto-detects Python → Set root to `backend/`
5. Add env var: `PORT=8080`
6. Your URL: `https://careerai-backend.up.railway.app`

For frontend on Railway:
1. Add new service → Static site
2. Root: `frontend/`
3. Done.

---

## OPTION 3 — VERCEL (Frontend) + FLY.IO (Backend)
### Best performance. Free tier available.

**Vercel (Frontend):**
```bash
npm install -g vercel
cd frontend
vercel
# Follow prompts → get URL instantly
```

**Fly.io (Backend):**
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

cd backend
fly launch    # auto-detects Python, creates fly.toml
fly deploy
# Get URL: https://careerai-backend.fly.dev
```

---

## OPTION 4 — GOOGLE COLAB (Temporary URL for testing)
### No setup. Share with anyone for ~12 hours.

```python
# Run this in a Google Colab notebook:
!pip install flask scikit-learn pandas numpy joblib openpyxl pyngrok

from pyngrok import ngrok
import subprocess, threading

# Upload your backend folder to Colab first, then:
def run_flask():
    subprocess.run(["python", "backend/app.py"])

thread = threading.Thread(target=run_flask)
thread.start()

public_url = ngrok.connect(5000)
print(f"Backend URL: {public_url}")
# Share this URL! Works for ~12 hours.
```

---

## TROUBLESHOOTING

### "Model file not found" error on Render
The .pkl files may not be committed to git (they're in .gitignore).
Fix:
```bash
# Remove .pkl from gitignore, commit them
echo "" >> .gitignore
git add backend/models/
git commit -m "Add model artifacts"
git push
```

### CORS error in browser
Add this env var in Render:
```
ALLOWED_ORIGINS = *
```
(Use `*` for development, set your Netlify URL for production)

### Free tier cold start (30s delay)
Render free tier sleeps. To wake it up before users visit:
- Add a "ping" service using https://cron-job.org (free)
- Set it to ping your `/api/v1/health` endpoint every 10 minutes

### Frontend shows mock data even after setting API_BASE
Open `frontend/index.html`, search for `API_BASE`, make sure it's set to your
full backend URL including `/api/v1`:
```javascript
const API_BASE = 'https://careerai-backend.onrender.com/api/v1';  // ← correct
const API_BASE = 'https://careerai-backend.onrender.com';          // ← missing /api/v1
```

---

## SUMMARY — FASTEST PATH TO LIVE URL

```
Total time: ~10 minutes

1. GitHub  →  Push code           (3 min)
2. Render  →  Deploy backend      (5 min)  → https://careerai-backend.onrender.com
3. Netlify →  Drop frontend folder (2 min) → https://your-site.netlify.app
```

