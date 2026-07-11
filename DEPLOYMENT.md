# Deployment Guide: Streamlit Cloud + Local Sync

## 🚀 Streamlit Cloud Deployment

### Step 1: Prepare Your Repository

Ensure these files exist in your repo (already added):
- `.streamlit/config.toml` — UI configuration
- `.streamlit/secrets.toml.example` — template for secrets
- `requirements.txt` — all dependencies
- `run.py` — entry point for Streamlit

### Step 2: Create `.streamlit/secrets.toml` (Local Only)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and add your API keys:
```toml
OPENAI_API_KEY = "your-key-here"
ANTHROPIC_API_KEY = "your-key-here"
OPENROUTER_API_KEY = "your-key-here"
```

⚠️ **NEVER commit `.streamlit/secrets.toml` to GitHub!**

### Step 3: Add `.streamlit/secrets.toml` to `.gitignore`

Ensure this line is in your `.gitignore`:
```
.streamlit/secrets.toml
```

### Step 4: Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Sign in with GitHub
3. Click **"New app"**
4. Select:
   - Repository: `mortezaparsipour-blip/ai-arena`
   - Branch: `main`
   - Main file path: `run.py`
5. Click **"Deploy"**

### Step 5: Add Secrets to Streamlit Cloud

Once deployed:
1. Click the **"☰" menu** (top right of your app)
2. Go to **"Settings"** → **"Secrets"**
3. Paste the same content from your local `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-key-here"
   ANTHROPIC_API_KEY = "your-key-here"
   OPENROUTER_API_KEY = "your-key-here"
   ```
4. Click **"Save"** and the app will redeploy automatically

---

## 🔄 Local Sync: Keep Local & Cloud in Sync

### Recommended Workflow

#### When you make changes locally:

```bash
# 1. Pull latest from GitHub
git pull origin main

# 2. Make changes locally
# (edit files, test with: streamlit run run.py)

# 3. Commit and push
git add .
git commit -m "Description of changes"
git push origin main

# 4. Streamlit Cloud auto-deploys from main branch
# (Check your deployment in 30-60 seconds)
```

#### When Streamlit Cloud has updates:

Streamlit Cloud automatically redeploys when you push to `main`:
- Changes take ~30-60 seconds
- Check logs: App menu → "Manage app" → "Logs"

---

## 💻 Run Locally

```bash
# 1. Clone or pull updates
git clone https://github.com/mortezaparsipour-blip/ai-arena.git
cd ai-arena

# 2. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy secrets template and add your keys
cp .env.example .env
# Edit .env and add API keys

# 5. Run locally
streamlit run run.py
```

**Local app opens at:** `http://localhost:8501`

---

## 📋 Checklist Before First Deployment

- [ ] `.streamlit/config.toml` exists ✓
- [ ] `.streamlit/secrets.toml.example` exists ✓
- [ ] `.streamlit/secrets.toml` is in `.gitignore` ✓
- [ ] `requirements.txt` has all dependencies ✓
- [ ] `run.py` exists and imports from `ai_arena.ui.app` ✓
- [ ] GitHub repo is public (or you have Streamlit Cloud Pro)
- [ ] All API keys are ready (OpenAI, Anthropic, OpenRouter)

---

## 🔐 Secrets Management

### Local (`.env` and `.streamlit/secrets.toml`)
- Used when running locally with `streamlit run run.py`
- Never committed to GitHub

### Streamlit Cloud
- Use **Settings → Secrets** in your app dashboard
- Loaded automatically as environment variables
- Separate from local secrets (so they never leak)

### Accessing Secrets in Code

```python
import streamlit as st
import os

# From .env (local) or Streamlit Cloud secrets
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
```

---

## 🐛 Troubleshooting

### App crashes after deployment
1. Check **App menu → Logs** for errors
2. Ensure all imports are correct in `run.py`
3. Check that `requirements.txt` has all dependencies

### API keys not working on Streamlit Cloud
1. Go to **Settings → Secrets**
2. Verify keys are copied exactly (no extra spaces)
3. Redeploy: **Manage app → Reboot script**

### Local app won't start
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Try again
streamlit run run.py
```

---

## 📚 Useful Links

- [Streamlit Cloud Docs](https://docs.streamlit.io/deploy/streamlit-cloud)
- [Streamlit Secrets Management](https://docs.streamlit.io/deploy/streamlit-cloud/manage-your-app/secrets-management)
- [GitHub Integration](https://docs.streamlit.io/deploy/streamlit-cloud/get-started)
