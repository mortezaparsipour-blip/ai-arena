# راهنمای Deploy بر روی Railway

## مرحله ۱: ثبت‌نام
1. برو: https://railway.app
2. ثبت‌نام کن با **GitHub account**

---

## مرحله ۲: Connect GitHub Repo
1. داخل Dashboard، کلیک کن **New Project**
2. انتخاب کن **Deploy from GitHub repo**
3. GitHub authorization انجام بده
4. ریپوی خود را انتخاب کن: `mortezaparsipour-blip/asbdavani`

---

## مرحله ۳: تنظیمات Railway
Railway خودکار **Dockerfile** رو detect می‌کنه و شروع به build می‌کنه.

### Environment Variables (Optional)
در بخش **Variables** اینها رو بذار:
```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

---

## مرحله ۴: Deploy!
1. کلیک کن **Deploy**
2. منتظر بمان تا build و start شه (۲-۵ دقیقه)
3. وقتی **Deployment succeeded** شد، URL بهت داده می‌شه

**آدرس نهایی:** چیزی شبیه:
```
https://asbdavani-production.up.railway.app
```

---

## مرحله ۵: دسترسی
- دسترسی **فقط تو** (private repo)
- برای public کردن: Settings → Visibility = Public

---

## خودکار Updates
هر بار commit و push کنی:
- Railway خودکار re-deploy می‌کنه
- هیچ کد اضافی لازم نیست!

---

## مشکل: Database/Models گم شد؟

اگه پیغام‌های خطا گرفتی درباره `asbdavani.db` یا `models/`:

### حل ۱: Railway Volumes استفاده کن
```bash
# Railway CLI نصب کن
npm i -g @railway/cli

# Persist data
railway volume add --mount /app/models --name asbdavani-models
railway volume add --mount /app --name asbdavani-db
```

### حل ۲: ساخت Database ابتدایی
یک `init_db.py` بساز در root:
```python
from pathlib import Path
Path("asbdavani.db").touch()
Path("auth.db").touch()
Path("models").mkdir(exist_ok=True)
```

سپس در Dockerfile اضافه کن:
```dockerfile
RUN python init_db.py
```

---

## مرحله ۶: مانیتورینگ

در Railway Dashboard:
- **Logs** → مشاهدهٔ logs real-time
- **Metrics** → CPU/Memory/Network
- **Deployments** → history

---

## نکات مهم

✅ **Private repo** ← Railway پشتیبانی می‌کنه  
✅ **Auto-redeploy** ← بعد از git push  
✅ **Free tier** ← ۵۰۰ ساعتِ compute‌/ماه  
⚠️ **Database persistent** ← نیاز به volumes  

---

## اگه دوست داری ریپو رو Public کنی:

1. GitHub → Settings → Change repository visibility
2. Make it **Public**
3. بعد Streamlit Cloud هم می‌تونه deploy کنه (ساده‌تر است)

---

**سوالی داری؟ راهنمای Railway:** https://docs.railway.app