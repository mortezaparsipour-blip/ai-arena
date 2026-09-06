# 02 — گزارش باگ‌ها (Bug Report)

**تاریخ:** 2026-09-05 · بازبینی کامل کد؛ هیچ تغییری اعمال نشد.
اولویت‌ها: P0 = بحرانی، P1 = بالا، P2 = متوسط، P3 = پایین.

---

## P0-1 · بعد از tool-call، حلقه به ایجنت بعدی advance نمی‌کند (خطر حلقه‌ی بی‌نهایت و دوبرابر شدن هزینه)

- **مکان:** `ai_arena/engine/orchestrator.py:368-371` (return None از `run_turn`) و `orchestrator.py:634-636` (advance شرطی در `step`).
- **شرح:** در فلوی one-shot، وقتی پاسخ ایجنت شامل tool-call است، `_process_tool_calls` پیام envelope را ثبت و `(None, last_result)` برمی‌گرداند؛ `run_turn` هم `None` برمی‌گرداند. در `step()`:
  ```python
  message = self.run_turn(session)
  if message:
      session.advance()
  ```
  پس برای turnهای tool-call دار **advance رخ نمی‌دهد** — همان ایجنت با اندیس فعلی دوباره صدا زده می‌شود.
- **چرا بحرانی است:** پیام کاربرِ هر turn صراحتاً می‌گوید «Call write_file with the COMPLETE new content». مدلِ پیرو پرامپت دوباره write می‌کند → دوباره None → دوباره همان ایجنت. چون `current_round` فقط در `advance()` زیاد می‌شود، `is_complete()` هرگز True نمی‌شود و `run_loop` تا Stop دستی ادامه می‌دهد؛ هر تکرار یک call پولی API است. حتی در حالت خوش‌بینانه (پاسخ prose در تکرار دوم) هر turnِ نوشتن **دو برابر** call مصرف می‌کند و شمارش round‌ها خراب می‌شود. توجه: turnهای **شکست خورده‌ی** tool (error envelope) هم به همین مسیر می‌روند.
- **تناقض با مستندات خود کد:** docstring `_process_tool_calls` می‌گوید «The next agent then gets a fresh user message with the (possibly updated) file content» (`orchestrator.py:421-423`)؛ `docs/architecture.md` گام ۶ و `docs/tools.md` گام ۶ هم «Advance to next agent» را وعده می‌دهند.
- **نقطه‌کور تست:** `test_one_shot_flow.py` و `test_regression_v2.py` فقط assert می‌کنند که `msg is None`؛ هیچ تستی advance بعد از tool-call را چک نمی‌کند. تست‌های dry-run همه prose برمی‌گردانند.
- **رفع پیشنهادی (بدون اعمال):** envelope message را از `run_turn` برگردانید (بدون append دوم در `step`/صرفاً بازگرداندن مرجع همان envelope_msg) یا در `step` به‌جای `if message` از یک سیگنال صریح (مثلاً tuple یا بررسی `session.messages` طول جدید) استفاده کنید.

---

## P1-1 · وضعیت «Running» شبح‌وار هنگام switch session با حلقه‌ی زنده

- **مکان:** `ai_arena/ui/app.py:197-212` (دکمه Start) + `ai_arena/engine/orchestrator.py:670-687` (`start_background`).
- **شرح:** اگر session A در حال اجرا باشد و کاربر بدون Stop، از سایدبار به session B سوییچ کند و Start بزند، `start_session(B)` وضعیت B را به `is_running=True` می‌برد ولی `start_background` چون thread قبلی (که A را اجرا می‌کند) زنده است، **همان thread را برمی‌گرداند**. نتیجه: B در UI «Running» نشان داده می‌شود اما هیچ worker‌ای آن را پردازش نمی‌کند؛ A هم به کارش ادامه می‌دهد. کاربر می‌تواند با Pause خارج شود ولی تجربه گمراه‌کننده است.
- **رفع پیشنهادی:** قبل از Start، اگر `is_loop_alive()` و session فعالِ thread فعلی متفاوت است، اول stop/pause؛ یا در `start_background` هویت session در حال اجرا را نگه دارید و reject/جایگزینی آگاهانه.

## P1-2 · docstring `_save_session` با پیاده‌سازی تناقض دارد (نوشتن غیراتمی)

- **مکان:** `ai_arena/engine/session.py:279-314`.
- **شرح:** docstring ادعای «Writes to session_<id>.json.tmp first, then renames… atomic on both POSIX and Windows» را دارد؛ ولی بدنه پس از کامنتی درباره‌ی PermissionError ویندوز، **مستقیم** روی فایل مقصد می‌نویسد. پیامد: crash/kill وسط نوشتن → JSON ناقص → `_load_from_disk` بی‌صدا آن را skip می‌کند → **از دست رفتن کل تاریخچه‌ی session**.
- **نکته‌ی تست:** `tests/test_fixes.py::test_save_session_atomic` (P1-6 قدیمی) دیگر اتمی بودن را نمی‌سنجد — فقط نبودن `.tmp` را چک می‌کند؛ تست با پیاده‌سازی فعلی همیشه پاس می‌شود.
- **رفع پیشنهادی:** یا docstring اصلاح شود (پذیرش ریسک)، یا replace اتمی با الگوی temp+`os.replace` با مدیریت `PermissionError` ویندوز (retry کوتاه) پیاده شود.

## P1-3 · اولویت fallback کلید OpenRouter برعکس

- **مکان:** `ai_arena/config.py:93-102`.
- **شرح:** برای `provider="openrouter"`، `env_keys.insert(0, "OPENAI_API_KEY")` باعث می‌شود در صورت ست‌بودن **هر دو** متغیر، کلید OpenAI به OpenRouter داده شود و 401 بگیرد. کلید اختصاصی provider باید اولویت داشته باشد.
- **تسکینpartial:** هشدار prefix در `config_panel.py:95-129` این خطای رایج را در UI نشان می‌دهد، ولی مسیر برنامه‌ای (و حالت «کاربر فیلد را خالی گذاشته») همچنان اشتباه resolve می‌شود.

## P1-4 · مسیر retry envelope در orchestrator مرده است (dead path)

- **مکان:** `orchestrator.py:149-211` (`_build_messages` با `tool_result_envelope`) و `_call_provider` — هیچ call-site‌ای `tool_result_envelope` را پاس نمی‌دهد.
- **شرح:** کل منطق «برگرداندن نتیجه‌ی tool به همان ایجنت» که docstring کلاس (`orchestrator.py:33-39`) و Tool manual هنوز توصیفش می‌کنند، عملاً اجرا نمی‌شود. علاوه بر گمراهی مدل، `inject_tools = not tool_result_envelope` رفتار مرده دارد و `RateLimiter`-باگ‌های احتمالی این مسیر تست نمی‌شوند.
- **رفع پیشنهادی:** حذف پارامتر و ساده‌سازی `_build_messages`، یا بازگرداندن معنا به این مسیر.

---

## P2-1 · `streamlit-autorefresh` در pyproject اعلام نشده + docstring از fallback دروغ می‌گوید

- **مکان:** `ai_arena/ui/app.py:341-360`، `pyproject.toml:13-19`، `requirements.txt:8`.
- **شرح:** در venv محلی پکیج نصب است (`streamlit_autorefresh-1.0.1`)، ولی نصب از طریق `pip install .` (pyproject) آن را نمی‌گیرد → ImportError → `pass` → **لایو-ریفرش به‌کل غیرفعال** و UI هنگام اجرای حلقه بدون rerun خودکار می‌ماند. docstring مدعی fallback «st.fragment» است که در کد وجود ندارد.

## P2-2 · defaultهای ناسازگار (rate limit و max_tokens)

- rate limit: `config.py:42` → 60، `docs/configuration.md` → «Default: 60»، ولی `session_state.py:47` → 5 و `config_panel.py:164` → 5. کاربر UI مقدار ۵ می‌بیند؛ مستندات ۶۰ می‌گوید.
- max_tokens: `agent.py:40` → 20000، `config_panel.py:294` → 10000. (برای Anthropic هم P3-2 را ببینید.)

## P2-3 · Tool manual و پرامپت‌ها: قرارداد «error → retry» دیگر برقرار نیست

- **مکان:** `ai_arena/engine/tool_registry.py:86-92` و بخش Tool Result Format (خطوط 119-129).
- **شرح:** manual می‌گوید «اگر tool call شکست خورد error می‌گیرید و باید retry کنید»؛ در فلوی one-shot، همان ایجنت هرگز envelope را نمی‌بیند (envelope فقط در message log ثبت می‌شود). مدل ممکن است منتظر نتیجه بماند که هرگز در کانتکستش نمی‌آید. پرامپت‌های `sys_prompts/*` به‌درستی به‌روز شده‌اند («Do NOT call read_file») — فقط manual عقب است.
- ضمناً `has_tool_call` برای fence خراب True برمی‌گرداند ولی parse fail در نهایت به مسیر prose+warning می‌رود؛ رفتار gracefully است ولی با وعده‌ی manual نمی‌خواند.

## P2-4 · تست‌ها دایرکتوری runtime واقعی را پاک می‌کنند

- **مکان:** `tests/test_comprehensive.py:21-24`، `tests/test_dryrun_5rounds.py:53-57`، `tests/test_openrouter.py:99-102`.
- **شرح:** حذف **همه‌ی** `session_*.json` و `*.md` از `contexts/` (مسیر واقعی پروژه، نه tmp). اجرای عادی pytest، sessionها و contextهای کاربر را نابود می‌کند. باید به `tmp_path` منتقل شوند.

## P2-5 · کامنت‌های متناقض درباره‌ی `initial_prompt`

- **مکان:** `orchestrator.py:506-510` در برابر `models/session_state.py:40-43`.
- **شرح:** یک کامنت می‌گوید «prompt به‌عنوان اولین user message در round 0 ارسال می‌شود و فایل skeleton تمیز می‌ماند»؛ کامنت دیگر می‌گوید «در session ذخیره می‌شود تا در فایل نریزد». واقعیت کد (`start_session` خط 534-544): initial prompt **داخل فایل** seed می‌شود و `initial_prompt` هرگز مستقیم به مدل فرستاده نمی‌شود (`_build_messages` به آن ارجاع ندارد). رفتار درست است، ولی هر دو کامنت از واقعیت حرف می‌زنند.

---

## P3 — موارد جزئی

| # | مکان | شرح |
|---|------|-----|
| P3-1 | `engine/rate_limiter.py:26-46` | در `wait()`، `_last_call` **بعد از** sleep ست می‌شود؛ دو waiter هم‌زمان می‌توانند تقریباً با هم عبور کنند (تضمین فاصله‌ی سخت نیست). در عمل فقط یک thread loop وجود دارد. |
| P3-2 | `providers/anthropic_provider.py:64` | `max_tokens` پیش‌فرض 10000/20000 برای مدل‌های claude-3 که سقف ~8192 دارند → خطای 400. سقف per-model لازم است. |
| P3-3 | `engine/session.py:259-277` | `delete_session` فایل `.bak.md` و `audit_<id>.log` را حذف نمی‌کند → انباشت فایل‌های یتیم. |
| P3-4 | `orchestrator.py` کل | در هر turn دو بار `_save_session` زده می‌شود (داخل `_process_tool_calls` و داخل `run_turn`/`step`)؛ I/O اضافی. |
| P3-5 | `engine/session.py` کل | session JSON بدون سقف رشد می‌کند (messages + diffها هر turn) و `_load_from_disk` همه‌ی sessionها را کامل در حافظه load می‌کند. |
| P3-6 | معماری چند-tab | دو tab مرورگر = دو Orchestrator/SessionManager روی همان فایل‌ها؛ قفل‌های save per-instance هستند و `_active_context_path` سندباکس process-wide است → نوشتن‌های متقاطع رد/ناپایدار می‌شوند. |
| P3-7 | `pyproject.toml:29` | اسکریپت کنسول `ai-arena = "run:main"` خارج از `streamlit run` اجرا می‌شود → `ScriptRunContext` warnings / رفتار ناقص. فقط `streamlit run run.py` پشتیبانی واقعی است. |
| P3-8 | `ui/context_panel.py:19-27` در برابر `ui/app.py:101-113` | اولویت status badge متفاوت است (app: complete > running؛ context: running > complete). |
| P3-9 | `tools/file_tools.py:327-340` | `compute_diff` با `lineterm=""` + `keepends=True` خطوط خالی اضافی در انتهای diff تولید می‌کند (آرایشی). |
| P3-10 | `.gitignore:39` | قانون سراسری `*.json` باعث ignore شدن `pyrightconfig.json` شده (untracked). |
| P3-11 | `ui/app.py:290-322` | `_render_export_button` در هر rerun کل خروجی export را می‌سازد و فایل context را می‌خواند (بلا لازم نیست). |
| P3-12 | `models/agent.py:30` | فیلد `enabled` هیچ کنترل UI ندارد؛ گارد «zero enabled agents» از طریق UI قابل وقوع نیست. |

## Importهای بلااستفاده (ruff F401 آنها را می‌گیرد)

- `ai_arena/engine/orchestrator.py`: `datetime` (خط 12)، `config` (16)، `build_tool_result_envelope` (18)، `ToolCallParseError` و `parse_tool_call` (20) — هیچ‌کدام در فایل استفاده نشده‌اند.
- `ai_arena/engine/session.py`: `os` (خط 6).
- `ai_arena/providers/cerebras_provider.py`: `ChatCompletion` در TYPE_CHECKING بلااستفاده است.

## مسیر تست هاردکد شده

- `tests/test_middleware.py:46`: `C:/Users/Mahmoud/AppData/Local/Temp/kilo/...` — وابسته به کاربر/ماشین؛ باید `tmp_path` باشد.

## جمع‌بندی شمارش

- P0: 1 مورد · P1: 4 مورد · P2: 5 گروه · P3: 12 مورد + 3 import مرده + 1 تست هاردکد.
- باگ‌های گزارش‌شده در CHANGELOG قبلی (۱۵ مورد) همگی در کد فعلی برطرف به نظر می‌رسند و `test_regression_v2.py` آنها را پوشش می‌دهد — رگرسیون جدید P0-1 از رفکتور one-shot است.
