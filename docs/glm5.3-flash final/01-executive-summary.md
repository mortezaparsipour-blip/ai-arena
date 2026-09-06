# 01 — جمع‌بندی مدیریتی (Executive Summary)

**تاریخ:** 2026-09-05 · **روش:** خواندن کامل تک‌تک فایل‌های سورس (بدون limit/offset) + تحلیل ایستا · **هیچ تغییری در کد اعمال نشد.**

## کارنامه ۰ تا ۱۰۰

| محور | نمره | توضیح |
|------|:----:|-------|
| معماری و طراحی | **78** | لایه‌بندی تمیز (models / providers / tools / engine / ui)، جداسازی خوب نگرانی‌ها، الگوی middleware و «one-shot per turn» انتخاب درستی است. کسر نمره: مسیر retry مرده، سندباکس global mutable، docstringهای contradictory. |
| صحت رفتار (Bugs) | **55** | باگ P0 در advance بعد از tool-call؛ چند باگ latent دیگر (P1/P2). فیکس‌های قبلی (CHANGELOG ۱۵ باگ) خوب اعمال شده‌اند ولی رفکتور آخر یک رگرسیون مهم گذاشته. |
| امنیت | **50** | نوشتن سندباکس شده و خوب است؛ اما خواندن `.env` و `contexts/session_*.json` (کلیدها به‌صورت plaintext) آزاد است و کلیدها روی دیسک ذخیره می‌شوند — برخلاف ادعای مستندات. |
| UI/UX | **75** | پنل‌ها پولیش‌شده، token system و status bar حرفه‌ای. کسر: وابستگی autorefresh اعلام‌نشده در pyproject، وضعیت «Running» شبح‌وار بعد از switch session. |
| تست‌ها | **65** | پوشش رگرسیون خوب برای فیکس‌های قبلی (test_regression_v2 عالی است). کسر: دقیقاً روی همان نقطه‌ی باگ P0 نقطه‌کور است و cleanup تست‌ها داده‌ی واقعی کاربر را پاک می‌کند. |
| مستندات | **55** | حجم مناسب و ساختار خوب، اما در نقاط حساس از کد عقب افتاده (ادعای «کلیدها ذخیره نمی‌شوند»، توصیف retry قدیمی، defaults متفاوت). |
| کیفیت کد | **72** | خوانا، type-hintدار، کامنت‌گذاری هدفمند (گاهی منقضی). dead code و importهای بلااستفاده کم ولی موجود. |
| **میانگین کلی** | **64/100** | پایه‌ی سالم با یک مشکل جدی قابل‌حل در چند خط. |

## ۱۰ یافته‌ی برتر (به ترتیب اولویت)

1. **[P0] بعد از turn شامل tool-call، حلقه advance نمی‌کند** — `Orchestrator.run_turn` برای turnهای tool-call دار `None` برمی‌گرداند و `step()` فقط وقتی `advance()` می‌کند که message برگردد (`ai_arena/engine/orchestrator.py:368-371` و `:634-636`). نتیجه: همان ایجنت بلافاصله دوباره صدا زده می‌شود. چون پرامپت کاربر صراحتاً می‌خواهد «write_file بزن»، مدل compliant دوباره write می‌کند → `current_round` هیچ‌وقت زیاد نمی‌شود → `is_complete()` هرگز True نمی‌شود → **حلقه‌ی بی‌نهایت با هزینه‌ی API در هر تکرار** تا کاربر دستی Stop بزند. با docstring خودِ کد (`_process_tool_calls`: «The next agent then gets a fresh user message») و `docs/architecture.md` و `docs/tools.md` هم تناقض دارد.
2. **[P1] scope خواندن، اسرار داخل project root را می‌خواند** — `_enforce_read_scope` (`ai_arena/tools/file_tools.py:101-127`) فقط خروج از root را می‌بندد؛ ولی `.env`، `contexts/session_<id>.json` (کلیدهای API در plaintext) و `.streamlit/secrets.toml` **داخل** root هستند. ایجنت می‌تواند آنها را read و سپس (با write مجاز به ctx) داخل فایل اشتراکی تزریق کند و از طریق Export خارج شود.
3. **[P1] کلیدهای API به‌صورت plaintext روی دیسک ذخیره می‌شوند** — `Agent.to_dict` کلید را serialize می‌کند (`ai_arena/models/agent.py:53`) و `SessionManager._save_session` آن را در `contexts/session_*.json` می‌نویسد. `docs/configuration.md:41` صراحتاً ادعای خلاف آن را می‌کند («Keys are not persisted to disk»).
4. **[P1] وضعیت Running شبح‌وار بعد از switch session با حلقه‌ی زنده** — `start_background` اگر thread قبلی زنده باشد همان را برمی‌گرداند (`orchestrator.py:670-687`)؛ session جدید `is_running=True` می‌شود ولی worker آن را پردازش نمی‌کند.
5. **[P2] `_save_session` اتمی نیست در حالی که docstring اتمی بودن را وعده می‌دهد** — نوشتن مستقیم روی فایل مقصد (`session.py:310-314`)؛ crash وسط نوشتن = JSON خراب = drop بی‌صدای session در load بعدی. تست `test_save_session_atomic` دیگر واقعاً اتمی بودن را تست نمی‌کند.
6. **[P2] اولویت کلید OpenRouter برعکس است** — `config.get_api_key("openrouter")` با `insert(0, "OPENAI_API_KEY")` (`config.py:97`) وقتی هر دو متغیر ست باشند، کلید OpenAI را به OpenRouter می‌فرستد.
7. **[P2] `streamlit-autorefresh` در pyproject اعلام نشده** — فقط در requirements.txt است؛ نصب از طریق `pip install .` لایو-ریفرش را بی‌صدا از کار می‌اندازد. docstring `app.py:341-360` از fallback «st.fragment» حرف می‌زند که در کد وجود ندارد.
8. **[P2] Tool manual مدل را گمراه می‌کند** — می‌گوید «اگر tool call شکست خورد، error می‌گیرید و باید retry کنید» (`tool_registry.py:86-92`) در حالی که در فلوی one-shot هیچ‌وقت error envelope به همان ایجنت نمی‌رسد. مسیر `tool_result_envelope` در `_build_messages`/`_call_provider` عملاً dead code است.
9. **[P2] تست‌ها `contexts/` واقعی را پاک می‌کنند** — سه تست فایل‌های `session_*.json` و `*.md` را از دایرکتوری runtime حذف می‌کنند (`test_comprehensive.py:21-24`, `test_dryrun_5rounds.py:53-57`, `test_openrouter.py:99-102`)؛ اجرای suite = از دست رفتن sessionهای کاربر.
10. **[P2] doc-rot گسترده** — README ادعای Pydantic (هیچ‌جا import نشده)، defaults ناسازگار rate-limit (۶۰ در docs/config.py در برابر ۵ در UI/SessionState)، docstring کلاس Orchestrator هنوز فلوی قدیمی «retry loop» را توصیف می‌کند، کامنت‌های `initial_prompt` دو روایت متناقض دارند.

## توصیه‌ی ترتیب اقدام

1. فوری: رفع P0 (بعد از turn tool-call دار هم advance شود — مثلاً برگرداندن envelope message از `run_turn` بدون append تکراری، یا advance مبتنی بر سیگنال غیر از None).
2. همین هفته: بستن read scope روی `.env` / `session_*.json` / `.streamlit/` / `.git`، حذف api_key از serialization (یا نگاشت به env در زمان load)، sync docstring با واقعیت `_save_session`.
3. بعدی: sync مستندات (keys، defaults، retry)، افزودن streamlit-autorefresh به pyproject، غیرمخرب‌کردن cleanup تست‌ها (tmp_path).
