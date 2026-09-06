# AI Arena — گزارش‌های بازبینی کامل (GLM-5.3-Flash)

**تاریخ بازبینی:** 2026-09-05
**محدوده:** کل کدبیس، فایل‌به‌فایل و کامل (بدون limit/offset — تک‌تک فایل‌ها با read_file از خط ۰ تا انتها خوانده شدند).

## وضعیت رفع (2026-09-05)

در همان روز، همه‌ی یافته‌های این گزارش‌ها اعمال شد (CHANGELOG.md ورودی کامل را دارد):

| یافته | وضعیت |
|-------|-------|
| P0-1 عدم advance بعد از tool-call | ✅ FIXED — envelope message از run_turn برگردانده می‌شود؛ step روی هر نتیجه‌ی غیر None کار advance دارد + تست رگرسیون |
| P1-1 Running شبح‌وار | ✅ FIXED — `ensure_startable`/`_loop_session_id` + پیام خطا در UI |
| P1-2 ذخیره‌ی غیراتمی session | ✅ FIXED — tmp + `os.replace` با retry ویندوز + هشدار روی JSON خراب |
| P1-3 اولویت کلید OpenRouter | ✅ FIXED — `OPENROUTER_API_KEY` اول؛ `OPENAI_API_KEY` فقط fallback + تست |
| P1-4 مسیر retry مرده | ✅ FIXED — پارامتر `tool_result_envelope` حذف؛ اجرای تک‌موردی tool؛ docstringها اصلاح |
| P2-1 autorefresh در pyproject | ✅ FIXED — به dependencies اضافه شد + warning در UI + docstring درست |
| P2-2 default نرخ ناسازگار | ✅ FIXED (بخش نرخ) — `config.default_rate_limit = 5` تک‌منبع؛ بخش max_tokens طبق خواسته_SKIP |
| P2-3 manual قدیمی | ✅ FIXED — قرارداد one-shot در manual و مستندات |
| P2-4 تست‌های مخرب | ✅ FIXED — همه‌ی cleanupها به tmp_path/tempfile منتقل شدند |
| P2-5 کامنت‌های متناقض | ✅ FIXED |
| P3-1..P3-4, P3-7..P3-12 | ✅ FIXED — rate limiter، orphanها، save واحد per-turn، اسکریپت کنسول، status مشترک (ui/status.py)، compute_diff، .gitignore، export memo، checkbox enabled |
| P3-2 سقف max_tokens Anthropic | ⏭ SKIPPED — به خواست شما (max tokens فعلاً لازم نیست) |
| P3-5 رشد نامحدود session JSON | ⏭ DEFERRED — معماری lazy-load لازم دارد؛ باگ کاربری امروز ندارد |
| P3-6 چند-tab (جز سندباکس) | ⏭ DEFERRED — بخش سندباکس با thread-local ✅ FIXED |
| SEC-1 خواندن مسیرهای حساس | ✅ FIXED — deny-list در config (`is_sensitive_read_path`) + تست |
| SEC-2 کلیدها روی دیسک | ⏭ SKIPPED — به انتخاب شما کلیدها در session JSON می‌مانند؛ به جایش SEC-1 بسته شد و ادعای نادرست مستندات اصلاح شد |
| SEC-3 audit log بی‌سقف | ✅ FIXED — truncate تا ۳۰۰ کاراکتر |
| SEC-4 سقف حجم write_file | ⏭ SKIPPED — به خواست شما (max file size فعلاً لازم نیست) |
| SEC-6 سندباکس process-wide | ✅ FIXED — `threading.local()` |
| importهای مرده + مسیر تست هاردکد | ✅ FIXED |
| مستندات (README، configuration، tools، adding_agents، folder_structure، architecture، CHANGELOG) | ✅ SYNCED |

## فایل‌های خوانده‌شده به‌صورت کامل

- `run.py`, `requirements.txt`, `pyproject.toml`, `pyrightconfig.json`, `.env.example`, `.gitignore`
- `ai_arena/__init__.py`, `ai_arena/config.py`
- `ai_arena/engine/` — همه‌ی ۷ فایل (`__init__`, `orchestrator.py`, `rate_limiter.py`, `session.py`, `tool_executor.py`, `tool_parser.py`, `tool_registry.py`)
- `ai_arena/models/` — همه‌ی ۴ فایل
- `ai_arena/providers/` — همه‌ی ۶ فایل
- `ai_arena/tools/` — همه‌ی ۳ فایل
- `ai_arena/ui/` — همه‌ی ۸ فایل
- `tests/` — همه‌ی ۱۰ فایل + `conftest.py`
- `sys_prompts/` — هر ۴ پرامپت
- `docs/` — هر ۷ سند
- `README.md`, `CHANGELOG.md`, `CLAUDE.md`, `shared_context.md`, `.streamlit/config.toml`, `.streamlit/secrets.toml.example`, `.devcontainer/Dockerfile`

هیچ فایلی از کد تغییر نکرد؛ فقط همین پوشه‌ی گزارش ساخته/به‌روز شد.

## فهرست گزارش‌ها

| فایل | محتوا |
|------|-------|
| [01-executive-summary.md](01-executive-summary.md) | جمع‌بندی مدیریتی، کارنامه‌ی ۰ تا ۱۰۰، ۱۰ یافته‌ی برتر |
| [02-bug-report.md](02-bug-report.md) | باگ‌های تأییدشده با اولویت P0–P3 و ارجاع دقیق به فایل/خط |
| [03-security-review.md](03-security-review.md) | سندباکس فایل، نشت کلید، مسیرهای افشای اطلاعات |
| [04-architecture-quality-docs.md](04-architecture-quality-docs.md) | معماری، کیفیت کد، doc-rot، بازبینی تست‌ها و مغایرت مستندات |

## خلاصه‌ی یک‌خطی

معماری تمیز و فرآیند فیکس‌های قبلی خوب است، اما رفکتور «one-shot per turn» یک **باگ P0 باقی گذاشته**: بعد از هر turnِ شامل tool-call، حلقه به ایجنت بعدی advance نمی‌کند و همان ایجنت دوباره صدا زده می‌شود — در بدترین حالت حلقه‌ی بی‌نهایت و سوزاندن اعتبار API. به‌علاوه scope خواندن فایل‌ها اجازه‌ی خواندن `.env` و فایل‌های session (حاوی کلید API به‌صورت plaintext) را می‌دهد.

**نمره‌ی کلی: 64/100** — جزئیات در 01-executive-summary.md
