# Security and Privacy — Leftover Chef

## 1. Threat Model

| Threat | Vector | Mitigation Implemented | Verification |
| :--- | :--- | :--- | :--- |
| **SQL Injection (SQLi)** | Malicious ingredient strings or search query parameters | Parameterised SQLAlchemy 2.0 ORM queries; zero string-concatenated SQL | Verified in **TC-46** |
| **Cross-Site Scripting (XSS)** | Malicious HTML/JS in profile names, units, or storage notes | Server-side `html.escape` sanitization (`app/core/security.py`) + React automatic JSX escaping | Verified in **TC-47** |
| **Broken Object Level Authorization (BOLA / IDOR)** | User A attempting to read/modify User B's pantry, favourites, or shopping list | Every query filters by validated `user_id`; protected namespaces (`private_*`) require HMAC-verified `X-Access-Token` | Verified in **TC-34**, **TC-49** |
| **Denial of Service (Oversized Payload)** | Huge JSON payloads or thousands of ingredients | Request body size limit middleware (`64 KB` max) + Pydantic field validators (`max 1000 chars`, `max 50 ingredients`) | Verified in **TC-09** |
| **Secret Exposure** | Leaking API keys or signing secrets in health endpoints, logs, or Git | `.env` excluded in `.gitignore`; `.env.example` contains placeholders only; `/api/v1/health` exposes no secrets | Verified in **TC-48** |

## 2. Security Checklist
- [x] Input validation at all API boundaries using Pydantic v2.
- [x] Output encoding / HTML escaping for user-entered strings.
- [x] SQL injection prevention via SQLAlchemy ORM.
- [x] Security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`).
- [x] Request body size limit enforcement (`HTTP 413`).
- [x] Salted HMAC-SHA256 authentication reference hashing (`hash_auth_secret`).
- [x] Data minimisation: no sensitive personal data (phone numbers, addresses, payment details) collected.

---
**Developed by Anil Biradar**
