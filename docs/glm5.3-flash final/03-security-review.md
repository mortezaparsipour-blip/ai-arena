# 03 — بازبینی امنیت (Security Review)

**تاریخ:** 2026-09-05 · بازبینی ایستا؛ هیچ تغییری اعمال نشد.
**مدل تهدید:** ایجنت‌های LLM (که محتوای دلخواه/احتمالاً prompt-injected شده از فایل اشتراکی می‌بینند) ابزارهای فایل را روی ماشین محلی اجرا می‌کنند. کاربر محلی قابل اعتماد فرض می‌شود؛ تمرکز روی «ایجنت سرکش یا آلوده» است.

## آنچه خوب انجام شده ✅

1. **سندباکس نوشتن به‌درستی محدود است** — `_enforce_write_scope` (`ai_arena/tools/file_tools.py:71-98`) هر write/append/patch را به `set_active_context_path` مقید می‌کند که orchestrator در ابتدای هر turn ست می‌کند (`orchestrator.py:316`). write به `.env` یا هر مسیر دیگر با error envelope رد می‌شود. تست‌های `TestP0_2_FileToolSandbox` این را خوب پوشش می‌دهند.
2. **Path traversal کلاسیک بسته است** — resolve با `Path.resolve()` و مقایسه‌ی مسیر مطلق؛ `..` و symlinkها تا حد زیادی خنثی می‌شوند.
3. **`patch_file` با `old_text` خالی رد می‌شود** (`file_tools.py:260-264`) — جلوگیری از تخریب کل فایل (فیکس قبلی، هنوز سر جایش).
4. **کلیدها در UI به‌صورت password input** و هشدار mismatch پیشوند کلید (`config_panel.py:87-129`) — کاهش خطای انسانی.
5. `contexts/` و `.env` در `.gitignore` هستند — کلیدها به git نمی‌روند.

## یافته‌ها ⚠️

### SEC-1 (بالا) — read_file هر راز داخل project root را می‌خواند
- **مکان:** `_enforce_read_scope` — `ai_arena/tools/file_tools.py:101-127`.
- **سناریو:** ایجنت (یا محتوای تزریق‌شده در context از turn قبل) دستور می‌دهد:
  ```tool_call
  {"tool": "read_file", "arguments": {"path": ".env"}}
  ```
  چون `.env` داخل root است، خواندن موفق می‌شود. سپس همان ایجنت می‌تواند محتوا را در `write_file` به فایل context (که write مجازش هست) بریزد؛ نتیجه در UI، در `Export` و در session JSON بعدی قابل خروج است. اهداف مشابه: `contexts/session_<id>.json` (کلیدهای API همه‌ی ایجنت‌ها — SEC-2)، `.streamlit/secrets.toml`، `.git/config` (توکن‌های remote)، `.venv`، `graphify-out/`.
- **تناقض docstring:** کامنت خودِ تابع می‌گوید هدفش جلوگیری از exfiltrate شدن `~/.ssh/id_rsa` است؛ ولی گنج‌های واقعی (`.env`، session JSONها) داخل root و مجازند.
- **رفع پیشنهادی:** deny-list صریح حتی داخل root: هر مسیری که resolve شود به `.env*`، `contexts/session_*.json`، `contexts/audit_*.log`، `.streamlit/`، `.git/`، `.venv/` → رد؛ یا allow-list پسوند/دایرکتوری.

### SEC-2 (بالا) — کلیدهای API به‌صورت plaintext روی دیسک
- **مکان:** `Agent.to_dict` (`ai_arena/models/agent.py:53`) → `SessionManager._save_session` (`ai_arena/engine/session.py:290`) → `contexts/session_*.json`.
- **شرح:** هر save کلیدهای همه‌ی ایجنت‌ها را می‌نویسد. `docs/configuration.md:41` ادعای خلاف («Keys are not persisted to disk — they are stored only in the Streamlit session state») می‌کند — **ادعا نادرست است**. پیامد دوگانه: (۱) نشت از طریق SEC-1، (۲) ماندگاری طولانی‌مدت کلید روی دیسک بدون نیاز.
- **رفع پیشنهادی:** هنگام serialize، کلید را با placeholders جایگزین کنید (مثلاً `""` + پرچم `key_from_env`) و در `from_dict` کلید را از `config.get_api_key(provider)` دوباره resolve کنید؛ یا رمزنگاری با کلید ماشین (keyring).

### SEC-3 (متوسط) — Audit log خودش می‌تواند حساس شود
- **مکان:** `AuditLogger` — `ai_arena/engine/tool_executor.py:86-137`.
- **شرح:** `log_tool_call` **arguments کامل** (از جمله `content` برای write_file — یعنی کل متن context) را لاگ می‌کند؛ خروجی tool فقط ۲۰۰ کاراکتر preview است ولی ورودی نامحدود. فایل `contexts/audit_<id>.log` بدون چرخش رشد می‌کند و اگر SEC-1 رخ دهد، محتوای مسروقه اینجا هم کپی می‌شود.

### SEC-4 (متوسط) — هیچ سقف حجمی برای write_file
- **مکان:** `WriteFileTool.execute` — `file_tools.py:176-190`.
- **شرح:** مدل می‌تواند چند مگابایت در یک call بنویسد (یا در حلقه‌ی باگ P0-1 بی‌نهایت تکرار کند)؛ نه سقف بایت و نه سقف turn وجود دارد. پیشنهاد: سقف پیکربندی‌پذیر برای طول `content` و سقف hard برای تعداد turnهای بدون advance.

### SEC-5 (پایین) — پیشوند کلید به‌عنوان «اعتبارسنجی»
- **مکان:** `validate_key` همه‌ی providerها.
- **شرح:** فقط prefix چک می‌شود (و در OpenAI هر `sk-...` پاس می‌شود)؛ صرفاً UX است و اشکالی ندارد، ولی نباید به‌عنوان امنیت حساب شود. (پروکسی‌های سفارشی با prefix متفاوت هم مسدود نمی‌شوند — رفتار درست.)

### SEC-6 (پایین) — عدم جداسازی بین sessionها در سندباکس
- `_active_context_path` یک global با lock است (`file_tools.py:35-48`)؛ در اجرای هم‌زمان دو session (دو tab)، مقیدسازی آخرین setter برنده می‌شود → یا writeهای مشروع رد می‌شوند یا (بدتر) write به ctxِ session دیگر در پنجره‌ی زمانی اشتباه مجاز می‌شود. ریسک واقعی کم (یک کاربر محلی) ولی معماری سندباکس باید per-session باشد نه process-wide.

## جدول ریسک

| شناسه | ریسک | احتمال | اثر | اولویت |
|-------|------|:------:|:---:|:------:|
| SEC-1 | خواندن `.env`/session JSON توسط ایجنت | متوسط | بالا | بالا |
| SEC-2 | ماندگاری plaintext کلیدها | قطعی | متوسط | بالا |
| SEC-3 | انباشت داده‌ی حساس در audit log | متوسط | متوسط | متوسط |
| SEC-4 | write بدون سقف / حلقه‌ی پولی | متوسط | متوسط | متوسط |
| SEC-5 | validate_key فقط prefix | — | — | اطلاعاتی |
| SEC-6 | سندباکس process-wide | پایین | متوسط | پایین |

## یادداشت روی claims مستندات

- `docs/tools.md:243-246` می‌گوید «No path traversal outside the project directory is allowed» — برای write دقیق‌تر این است که «فقط فایل context» و برای read «داخل root» است؛ و همان‌طور که SEC-1 نشان می‌دهد، داخل root بودن به معنای امن بودن نیست.
- `docs/configuration.md:41` (keys not persisted) — نادرست؛ بند SEC-2.
