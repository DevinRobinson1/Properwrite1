# Fund Flow OS / Properwrite — Audit Summary
**Last refreshed**: 2026-05-13
**Previous audit**: 2025-07-12 (now superseded — see `security-fixes-completed.md` and below)

> The original 2025-07-12 audit flagged three critical issues (hardcoded
> admin password, missing CSRF, missing rate limiting). All three were
> resolved in the months following that audit and are confirmed fixed in
> the current codebase. This document tracks the state as of today.

## 1. Status of items the original audit flagged as critical

| Original finding | Current state | Evidence |
| --- | --- | --- |
| Hardcoded admin password `admin123` | ✅ Resolved | `admin_routes_minimal.py:93-102` reads `ADMIN_PASSWORD_HASH` env var and verifies with `werkzeug.security.check_password_hash`. |
| No CSRF protection | ✅ Resolved | `CSRFProtect(app)` wired at `app_upgraded.py:70`. 14 explicit `@csrf.exempt` decorators on webhook/AJAX endpoints. |
| No rate limiting | ✅ Resolved | `Limiter` at `app_upgraded.py:73-78` with global `200/hour, 50/min` plus per-route limits on `/api/signup`, `/api/login`, `/api/jv-submit` (5/hour). |
| `SESSION_SECRET` fallback to `"your-secret-key-here"` | ✅ Resolved | `app_upgraded.py:58-64` generates `secrets.token_hex(32)` when env var is missing and logs a warning. |
| Coinbase webhook TODO | ✅ Resolved | `bitcoin_payment_service.py:131-144` implements HMAC-SHA256 with `compare_digest`. |

## 2. Issues found and fixed today (2026-05-13)

| Finding | Severity | Resolution |
| --- | --- | --- |
| `ADMIN_TOKEN` defaulted to `'admin123'` in 4 routes under `/jv-admin*` | High | `app_upgraded.py:2873/2909/2948/2979`: missing env var now returns 503; the redirect no longer echoes the token in the URL. |
| Coinbase `verify_webhook_signature` could `TypeError` when `X-CC-Webhook-Signature` header was absent | Medium | `bitcoin_payment_service.py:131`: treat `None` signature as failure; signature is now `Optional[str]`. |
| Property cache built keys from raw f-strings; empty fields produced colliding `valuation_____.json` files; case + state-name variants produced duplicates | Medium | `comprehensive_valuation_service._make_cache_key` normalizes (lowercased addr/city, uppercased state, stripped place_id/zip) and MD5-hashes. Returns `None` when inputs are too sparse so the cache is skipped instead of polluted. Four degenerate cache files removed. |
| `/api/jv-submit` only checked `if not data.get('property_address')`; typo data persisted to `jv_deals/index.json` ("Evening Flighjt", "Evnein FFlgh lan") | Medium | `app_upgraded.py:2789-2826`: require populated street/city/state/zip and call `google_places_service.validate_address`; fall through structurally if Google is unavailable rather than 5xx-ing the user. |
| Repo gutted: `.py` source missing, only `.pyc` in `__pycache__/` after Replit zip export | Build-blocker | Restored from `github.com/DevinRobinson1/Properwrite1` (commit `f6bd72b`). |
| `.git/` corrupt: only object prefixes `a9–ff` present, HEAD/config/index missing | Build-blocker | Replaced with the working clone's `.git/`; original kept at `.git.backup/`. |
| `main.py` ran a dead Flask app with its own `SQLAlchemy`/`LoginManager` setup, then shadowed `app` with `from app_upgraded import *` | Cleanup | `main.py` reduced to `from app_upgraded import app` + `__main__`. |
| Duplicate `User` model: both `models.User` and `billing_models.User` defined `__tablename__ = 'users'`. `admin_routes.py` did `from models import db` (no `db` exists in `models.py` — broken at import). Dead code only reachable through dead code. | Cleanup | Deleted `models.py`, `admin_models.py`, `admin_routes.py`. |
| `comprehensive_valuation_service_backup.py` had `IndentationError` on line 334 | Cleanup | Deleted (not imported anywhere). |
| `archived_files/` (old `app.py`, `app_simple.py`, four presentation HTMLs) targeted a previous architecture | Cleanup | Deleted (zero references). |
| Orphan templates/JS: `admin_dashboard_v2.html`, `static/script.js`, `static/script_clean.js`, `static/js/enhanced-google-autocomplete.js`, `static/js/google-autocomplete-new.js` | Cleanup | Deleted (zero references). |
| `.gitignore` missing | Cleanup | Added — covers `__pycache__/`, `.env`, `.venv/`, `.local/`, `.git.backup/`. |

## 3. Known follow-ups (not fixed today)

| Area | Notes |
| --- | --- |
| Stale `attached_assets/` | 473 Replit prompt `.txt` files (historical AI chat logs). Repo bloat, no runtime impact. Pending user decision before deletion. |
| Dependency versions | `pyproject.toml` predates the 7-month dormant period. Worth bumping Flask, SQLAlchemy, openai, stripe, etc. behind a smoke test. Pending user decision. |
| Console-side null checks | `audit/console-errors-log.md` calls out `listing-commission-value` / `buyer-commission-value` element-not-found warnings and a Google Autocomplete unhandled promise rejection. Cosmetic. |
| JWT expiry | `audit/security-report.md` flagged 30-day JWT in `auth_service.py`. The historical `auth_service.py` referenced is not present in the current tree — auth flows through `auth_middleware.py`/`auth_routes.py` + session cookies. Worth a re-look if/when JWTs are reintroduced. |
| `templates/index_upgraded.html` | 10,800+ lines in a single file. Maintenance hazard, not a bug. |
| XSS in templates | `audit/security-report.md` flagged user data rendered without explicit `\| e`. Jinja2 autoescapes HTML by default; would need a per-template review to confirm no `\| safe` filters on user-controlled paths. |

## 4. Environment variables required for production

(unchanged from `security-fixes-completed.md`)

- `SESSION_SECRET` — cryptographically secure random string
- `ADMIN_PASSWORD_HASH` — generate with `python generate_admin_password.py`
- `ADMIN_TOKEN` — required for `/jv-admin*` routes; without it those routes now return 503
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `COINBASE_COMMERCE_API_KEY`, `COINBASE_WEBHOOK_SECRET`
- `DATABASE_URL` — PostgreSQL with SSL
- `RAPIDAPI_KEY` (Zillow), `RENTCAST_API_KEY`, `GMAPS_API_KEY` — data sources
