# 🚀 Quick Start Guide: AI Arena

## فارسی (Persian)

### گام ۱: Clone پروژه

```bash
git clone https://github.com/mortezaparsipour-blip/ai-arena.git
cd ai-arena
```

### گام ۲: محیط مجازی (Virtual Environment) ایجاد کنید

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate.bat

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### گام ۳: Dependencies نصب کنید

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### گام ۴: فایل `.env` را کپی و تنظیم کنید

```bash
cp .env.example .env
```

**فایل `.env` را باز کنید و API keys خود را وارد کنید:**

```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENROUTER_API_KEY=sk-or-your-key-here
```

### گام ۵: اپلیکیشن را اجرا کنید

```bash
streamlit run run.py
```

**اپلیکیشن باز می‌شود:** `http://localhost:8501`

---

## 🌐 Streamlit Cloud Deploy

### پیش‌نیاز:
- حساب GitHub (برای login)
- حساب Streamlit Cloud (رایگان!)
- API keys برای OpenAI/Anthropic/OpenRouter

### مراحل:

1. **برو به** [Streamlit Cloud](https://streamlit.io/cloud)
2. **Sign in با GitHub**
3. **کلیک کن روی** "New app"
4. **انتخاب کن:**
   - Repository: `mortezaparsipour-blip/ai-arena`
   - Branch: `main`
   - Main file: `run.py`
5. **کلیک کن "Deploy"** و صبر کن ۳۰-۶۰ ثانیه

### API Keys را روی Streamlit Cloud اضافه کنید:

1. **بعد از Deploy**, کلیک کن روی **☰ (Menu)** → **Settings**
2. **برو به Secrets** و paste کن:

```toml
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
OPENROUTER_API_KEY = "sk-or-..."
```

3. **Save کن** و اپ خودکار restart می‌شود ✅

---

## 🔄 Local ↔ Cloud Sync

### Workflow:

```bash
# 1. کد خودت رو بنویس
vim ai_arena/some_file.py

# 2. Local test کن
streamlit run run.py

# 3. اگه خوب بود, commit کن
git add .
git commit -m "توضیح تغییر"

# 4. Push کن به GitHub
git push origin main

# 5. Streamlit Cloud خودکار deploy می‌کنه! ✨
```

**Cloud auto-redeploy می‌شه در ۳۰-۶۰ ثانیه از push**

---

## 📁 پروژه Structure

```
ai-arena/
├── ai_arena/
│   ├── ui/              # Streamlit UI
│   ├── engine/          # Orchestrator
│   ├── providers/       # LLM providers
│   ├── models/          # Data models
│   └── tools/           # Agent tools
├── sys_prompts/         # System prompts
├── contexts/            # Runtime contexts
├── run.py               # Entry point
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── DEPLOYMENT.md        # Deployment guide
└── .streamlit/
    ├── config.toml      # Streamlit config
    └── secrets.toml     # API keys (local only)
```

---

## 🐛 Troubleshooting

### Local اپ شروع نمی‌شود؟

```bash
# Cache رو پاک کن
rm -rf ~/.streamlit

# Dependencies رو دوباره نصب کن
pip install --upgrade pip
pip install -r requirements.txt

# دوباره تست کن
streamlit run run.py
```

### API keys کار نمی‌کنند روی Cloud؟

1. برو **Settings → Secrets**
2. چک کن که keys دقیق copy شدند (بدون space)
3. **Reboot script** رو بزن

### Git push بعد از deploy, تغییر ظاهر نمی‌شود؟

```bash
# Streamlit cache رو پاک کن
git add .
git commit -m "Clear cache"
git push origin main

# صبر کن 60 ثانیه و refresh کن
```

---

## 📚 اسناد بیشتر

- 📖 **Full Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- 📘 **Streamlit Docs:** https://docs.streamlit.io
- 🔐 **Secrets Management:** https://docs.streamlit.io/deploy/streamlit-cloud/manage-your-app/secrets-management
- 🚀 **Deploy Docs:** https://docs.streamlit.io/deploy/streamlit-cloud

---

## ❓ سوالات رایج

**Q: میتونم locally development کنم و بعد cloud deploy کنم؟**  
A: بله! Git branch رو بسازید، develop کنید، test کنید، بعد PR merge کنید به main و خودکار deploy می‌شود.

**Q: API keys من leak نمی‌شند؟**  
A: خیر! `.env` و `.streamlit/secrets.toml` در `.gitignore` هستند. هرگز commit نمی‌شوند.

**Q: میتونم database بیافزایم؟**  
A: بله! پروژه کاملا extensible است. Docs رو ببینید برای adding new providers/tools.

---

## 🎯 Next Steps

1. ✅ API keys رو دریافت کن (OpenAI/Anthropic)
2. ✅ `.env` فایل رو تنظیم کن
3. ✅ Locally اجرا کن و test کن
4. ✅ روی Streamlit Cloud deploy کن
5. ✅ Share کن با دنیا! 🌍

Happy Hacking! 🚀

---

**Questions?** Check `DEPLOYMENT.md` or create an issue on GitHub!
