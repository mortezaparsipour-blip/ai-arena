# 04 — معماری، کیفیت کد، تست‌ها و ممیزی مستندات

**تاریخ:** 2026-09-05 · بازبینی کامل؛ هیچ تغییری اعمال نشد.

---

## ۱) معماری

### نقاط قوت
- **لایه‌بندی تمیز:** `models` (داده‌ی خالص) ← `providers` (سوا of LLM) ← `tools` (توانایی فایل) ← `engine` (orchestration) ← `ui` (Streamlit). وابستگی‌ها یک‌طرفه و بدون چرخه‌اند.
- **تصمیم «one-shot per turn» درست است:** حذف حلقه‌ی re-call بعد از tool call ریشه‌ی باگ «read loop» قبلی را قطع کرده و تزریق محتوای فایل در user message (`_build_messages` — `orchestrator.py:149-211`) تضمین می‌کند مدل همیشه state را می‌بیند. docstring این بخش از بهترین‌های کدبیس است.
- **فایل روی دیسک به‌عنوان single source of truth** با seed ساختاریافته (`# Shared Context / ## Initial Task / ## Working Draft`)، بکاپ `.bak.md` قبل از overwrite (`_backup_context_if_needed`) و diff per-turn — طراحی خوب و قابل دیباگ.
- **Thread safety آگاهانه:** `threading.Event` برای stop، قفل وضعیت برای flagها، قفل per-session برای save با `setdefault` (بدون TOCTOU)، و بازنشانی stale flags هنگام load (`_load_from_disk`).
- **Provider abstraction** با الگوی یکسان و error mapping اختصاصی OpenRouter (AuthenticationError/RateLimitError/…) — نمونه‌ی خوب برای providerهای بعدی.
- **Guardهای عملیاتی:** توقف بعد از N خطای متوالی provider (`record_provider_error`)، clamp مقادیر ورودی (`max_rounds >= 1` و…)، گارد «no enabled agents».

### نقاط ضعف ساختاری
1. **سیگنال بازگشت `run_turn` دوپهلو است** — `None` هم به معنی «tool call پردازش شد» و هم «stop شد». همین ابهام ریشه‌ی باگ P0-1 (عدم advance) و گره‌خوردگی `step()` است. یک نوع بازگشت صریح (TurnResult dataclass) ابهام را می‌زداید.
2. **سندباکس process-wide** (global `_active_context_path`) به‌جای per-turn context object — محدودیت چند-session و تست‌پذیری را پایین می‌آورد (conftest مجبور است بین تست‌ها reset کند).
3. **مسیر retry مرده** — مکانیزم `tool_result_envelope` + `ToolExecutor._execute_with_retry` (اجرای مجدد همان arguments در خطا، که برای خطاهای deterministic کاری بیهوده است) از فلوی فعلی جدا افتاده‌اند؛ یا باید حذف شوند یا دوباره معنا پیدا کنند.
4. **Orchestrator به متد private `session_manager._save_session`** دسترسی دارد و در هر turn دو بار save می‌کند — نشانه‌ی مرز نادرست بین دو کلاس.
5. **دو روایت متناقض در کامنت‌های خود کد** درباره‌ی `initial_prompt` (بند P2-5 در 02-bug-report).

### جریان داده (واقعیت فعلی کد، برای مرجع)
```
Start → seed فایل (Initial Task + Working Draft)
هر turn:
  system = agent.system_prompt ({ctx_path} جایگزین شده) + tool manual
  user   = محتوای فعلی فایل در fenced block + دستور write_file
  پاسخ بدون tool call  → پیام ایجنت + [WARNING] → advance
  پاسخ با tool call    → اجرای tool (سندباکس) → ثبت envelope (system msg) + diff
                          → run_turn برمی‌گرداند None → بدون advance  ← باگ P0-1
خطای provider → پیام [ERROR] + شمارنده؛ ۳ خطای متوالی = توقف
پایان: current_round >= max_rounds (فقط از مسیر advance)
```

---

## ۲) کیفیت کد

- **خوانایی و تایپ‌ها:** بالا. type hints تقریباً همه‌جا، dataclassها به‌جای dict، نام‌گذاری منسجم.
- **کامنت‌ها:** متراکم و هدفمند — اما چندجا «تاریخچه‌ی باگ» به‌جای قرارداد (مثلاً docstring `_build_messages` عالی، ولی docstring کلاس `Orchestrator` و `run_turn` هنوز فلوی قدیمی را توصیف می‌کنند).
- **Importهای مرده:** `orchestrator.py` → `datetime`, `config`, `build_tool_result_envelope`, `ToolCallParseError`, `parse_tool_call`؛ `session.py` → `os`؛ `cerebras_provider.py` → `ChatCompletion`. (ruff با select فعلی `["E","F","W","I"]` باید اینها را بگیرد — ظاهراً آخرین اجرا روی کد فعلی نبوده.)
- **UI:** جداسازی خوب (tokens.py به‌عنوان منبع واحد رنگ‌ها، icons.py کتابخانه‌ی SVG، stepper به‌صورت pure function قابل تست `compute_step`). نکته‌ها: docstring نادرست autorefresh، دو پیاده‌سازی متفاوت برای status badge، بازسازی محتوای export در هر rerun.
- **Parser (`tool_parser.py`):** قوی‌ترین ماژول از نظر مهندسی — سه استراتژی لایه‌ای (fence اختصاصی → fence JSON → raw_decode سراسری) + ترمیم خطای رایج LLM (backslash ویندوز، trailing comma). کامنت «previous regex couldn't match nested arguments» سابقه را خوب ثبت کرده.
- **مقایسه‌ی pyproject با requirements.txt:** pyproject فاقد `streamlit-autorefresh`؛ requirements.txt شامل `pydantic` است که **هیچ‌جا import نشده** (و README هم آن را در tech stack آورده — نادرست).

---

## ۳) بازبینی تست‌ها

### وضعیت کلی: ۱۰ فایل، ~۱۹۰۰ خط، اجرای ترکیبی pytest + اسکریپت مستقیم

| فایل | ارزیابی |
|------|---------|
| `test_regression_v2.py` | **عالی** — ۱۰ فیکس قبلی را با fixtureهای تمیز (tmp_path، providers جعلی) پوشش می‌دهد. الگوی `_make_orch` با `__new__` کمی شکننده است ولی کار می‌کند. |
| `test_one_shot_flow.py` | خوب — فلوی one-shot را قفل می‌کند؛ اما نقطه‌کورش دقیقاً advance بعد از tool-call است (P0-1). |
| `test_fixes.py` | خوب؛ فقط `test_save_session_atomic` دیگر ادعایش را نمی‌سنجد (بند P1-2). |
| `test_openrouter.py` | خوب — mapping خطاها با mock کامل. |
| `test_providers_live.py` | الگوی درست gating با `AI_ARENA_LIVE_TESTS`. |
| `test_comprehensive.py` / `test_dryrun_5rounds.py` / `test_openrouter.py` (بخش integration) | **مخرب** — `contexts/` واقعی را خالی می‌کنند (P2-4). |
| `test_middleware.py` | مسیر temp هاردکد کاربر (P3). |
| `test_quick.py` | اسکریپت دودی با `sys.path` وابسته به CWD؛ ارزش کم. |

### شکاف‌های پوشش
1. **advance بعد از tool-call** — هیچ تستی وجود ندارد (همان P0-1).
2. **UI** — فقط import-level (P2-1 ددکد و P2-3 duplicated logic در `test_regression_v2::TestP2_3` منطق را کپی می‌کند نه اینکه تابع واقعی را صدا بزند).
3. **`SessionManager` هم‌زمانی** (دو thread save) و `_load_from_disk` با فایل خراب — پوشش ندارد.
4. **سناریوی multi-session سندباکس** — پوشش ندارد.

---

## ۴) ممیزی مستندات (docs vs code)

| سند | ادعا | واقعیت کد | داوری |
|-----|------|-----------|-------|
| `README.md:23` | «Pydantic — data validation» در tech stack | هیچ import pydantic در کل کدبیس نیست؛ در requirements.txt هست ولی استفاده نمی‌شود | ❌ حذف/اصلاح |
| `docs/configuration.md:41` | «Keys are not persisted to disk» | کلیدها در `session_*.json` ذخیره می‌شوند | ❌ نادرست و مهم |
| `docs/configuration.md:16` | rate limit default 60 | UI و `SessionState` → 5 | ❌ ناسازگار |
| `docs/tools.md:92-93` | «Retry: return error envelope to the same agent» | در one-shot هیچ برگشتی به همان ایجنت نیست | ❌ منقضی |
| `docs/tools.md:243-246` | «No path traversal outside the project directory» | write فقط ctx (سخت‌گیرانه‌تر از ادعا)، read کل root (بار امنیتی SEC-1) | ⚠️ نیمه‌درست |
| `docs/adding_agents.md:65-66` | نمونه‌ی پرامپت «Always use read_file first» | فلوی فعلی read_file را منع می‌کند (`sys_prompts/*` به‌روز است) | ❌ نمونه‌ی ضدالگو |
| `docs/folder_structure.md` | فهرست ui و tests | `ui/icons.py`, `ui/stepper.py`, `ui/tokens.py` و ۶ فایل تست ذکر نشده‌اند؛ `tests/__init__.py` هم وجود ندارد | ⚠️ به‌روز نیست |
| `docs/architecture.md` | فلوی one-shot و نکات طراحی | منطبق — جز گام ۶ که advance بعد از tool-call را وعده می‌دهد (باگ P0-1) | ⚠️ تا رفع باگ |
| `CHANGELOG.md` | فیکس‌های 2026-07-20 | همه در کد برقرار و تست‌شده | ✅ |
| `sys_prompts/*` | قرارداد one-shot، منع read_file | کاملاً منطبق با کد | ✅ |

## ۵) نمره‌های جزئی

| زیرسیستم | نمره | یادداشت |
|----------|:----:|---------|
| engine/orchestrator | 60 | باگ P0 + docstring قدیمی؛ در غیر این صورت ساختار خوب |
| engine/session | 72 | پایدار؛ اتمی‌بودن و رشد فایل مشکل دارد |
| engine/tools (parser/executor/registry) | 80 | parser قوی؛ retry مرده |
| models | 85 | ساده و درست |
| providers | 78 | یکدست؛ سقف max_tokens Anthropic و اولویت کلید OpenRouter |
| tools/file_tools | 65 | write سندباکس خوب؛ read scope و سقف حجم ضعیف |
| ui | 75 | پولیش بالا؛ دو مشکل رفتاری (autorefresh، phantom running) |
| tests | 65 | رگرسیون قوی، gap حیاتی، cleanup مخرب |
| docs | 55 | پرحجم ولی با ادعاهای نادرست |
