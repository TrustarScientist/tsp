# Trustar School Platform (TSP)

**One platform. Many schools. Zero per-school deployments.**

TSP is the shared infrastructure behind two Trustar products:

- **School Websites** — public, themed marketing/admissions sites for partner schools
- **SchoolOS** — the operational backend (students, attendance, grading, timetabling, communications) that schools use once they're active partners

Both share **one Next.js frontend** and **one Django/DRF backend**. A school's public site and its operational dashboard are the same application, scoped by tenant — not two separate products bolted together.

This README is the entry point for anyone — human or AI — joining this codebase. Read it before touching code.

---

## 1. Core Architectural Principle

> **There is only ever ONE deployment of TSP.** Every school — whether on a free Trustar subdomain or a paid custom domain — is served by the same running application, the same database, the same codebase. Nothing is duplicated per school.

A school's own domain (e.g. `www.maasmodern.com`) is connected via a DNS **CNAME record** pointing at Trustar's infrastructure. There is no redirect — the browser's address bar stays on the school's own domain permanently. The backend reads the incoming **Host header** to determine which tenant (school) is being requested, and serves that school's data and theme accordingly. TLS auto-provisions via Let's Encrypt once DNS is pointed correctly.

This is what makes the platform commercially viable: adding a new school costs one DNS instruction and one database row — not a new deployment.

---

## 2. Product Boundary: Front Door vs. SchoolOS

| | **Front Door (School Websites)** | **SchoolOS** |
|---|---|---|
| Audience | Public — prospective parents/students | Enrolled school staff, students, parents |
| Access | No login required | Login-gated |
| Visual identity | Fully themed per school (registry-based theme engine) | Trustar-neutral everywhere — only the school's logo/name shows |
| Status | **Active — being built now** | **Gated** — see §3 |
| Backend apps | `content`, `admissions`, `payments` | `schoolos/*` (students, attendance, grading, timetabling, communications, cbt) |

**Discipline rule:** `schoolos/*` app folders exist in the backend as reserved namespaces, but stay empty (or near-empty) until SchoolOS is actually being built. Do not add real SchoolOS functionality ahead of the gate below — this is a deliberate scope boundary, not an oversight.

---

## 3. Gates (do not build ahead of these)

- **SchoolOS SaaS build:** begins once **3+ schools are waitlisted OR the ₦300k/month revenue gap is closed.** Maas Modern serves as a pilot/testing ground under a separate contractor arrangement — it does **not** replace this gate.
- **CBT / Virtual Labs Sync Service:** a separate, standalone fourth project (not part of this repo) — offline-first, multi-user, multi-frontend, built outside Django (likely Go). Begins once SchoolOS is running **AND 2+ schools request it.**
- **ZiniCoin:** spans CBT/Sync, Ksharer, and potentially the wider ecosystem. Needs its own ledger design and its own sequencing gate — not assumed into any single project's timeline.

If you're an AI assistant reading this to help with a task: check these gates before writing SchoolOS-, CBT-, or ZiniCoin-specific code. If the task seems to be jumping ahead of a gate, flag it rather than proceeding.

---

## 4. Tech Stack

**Backend:** Python / Django / Django REST Framework / PostgreSQL
**Frontend:** Next.js / TypeScript / React
**Auth:** Django JWT (single scheme for all roles — no dual-auth)
**Payments:** Paystack
**Hosting:** Render (Web Services) + PostgreSQL (single instance, multiple databases across Trustar projects — see `docs/infrastructure.md`)
**TLS/Domains:** Let's Encrypt (auto-provisioned per custom domain)

Ecosystem-wide stack philosophy (applies beyond this repo too):
- **Python/Django** is the default for all backend work across Trustar, SchoolOS, and Ksharer.
- **Go** is used only for named services with a specific, measured concurrency/offline/sync bottleneck (e.g. the CBT/Sync Service) — never as a general Django alternative.
- **FastAPI was evaluated and explicitly rejected** as a general backend framework — it would break reuse of Django's auth/tenancy/RBAC/Admin.

---

## 5. Identity & Authorization Model

Vocabulary used throughout this codebase: **Identity → Context → Membership → Role → Permission → Object/Data Scope.**

- A **User** in this repo represents a canonical identity *for this deployment*. Products don't share a single User table across the ecosystem (Trustar website, TSP, and Ksharer are separate databases) — but all User models follow the same structural conventions (UUID PKs, same field shape), so a future centralized identity/SSO layer would be an extraction, not a rewrite.
- Roles are **never global** on the User model. A person's role is always scoped via `UserRoleAssignment` (user, tenant/school, role, campus — nullable campus means school-wide). One person can be a parent at School A and a teacher at School B.
- JWTs carry **identity + context only** — never a snapshot of permissions. Permissions are resolved per-request (cached per `user_id` + `campus_scope`, invalidated on role change) so a role change takes effect immediately, not after token expiry. Compromised/terminated-staff tokens are handled via a `RevokedToken` blacklist checked at refresh.
- Authorization resolves in four ordered layers: **tenant isolation → role permission → relationship/scope → sensitivity gate.**

---

## 6. Multi-Tenancy Model

- **School** = tenant. **Campus** = a scoping dimension *inside* a school tenant (not a separate tenant) — every school gets ≥1 auto-created "Main Campus." `campus_id` is required (never nullable) on operational models.
- Tenant resolution for **public/pre-login pages** happens via the Host header (`TenantMiddleware` on the backend; equivalent middleware on the Next.js frontend).
- Tenant resolution for **authenticated multi-school users** (e.g. a teacher at two partner schools) happens post-login via `UserRoleAssignment` — the user sees a school picker if they have more than one active assignment, setting an active-tenant scope for the session. This is a distinct mechanism from Host-header resolution.
- **Data sovereignty:** Campus carries a `country` field as a future partition key. Multi-region infrastructure is deferred, but the schema is structurally ready for it now.

---

## 7. Theming

- The theme engine applies **only** to Front Door public pages (marketing, admissions, blog, gallery). SchoolOS's authenticated screens are Trustar-neutral everywhere.
- Auth pages (login, signup, password reset) are Trustar-neutral and shared across all school domains — never themed.
- Themes are **registry-based**, not hard-capped at a fixed number. Each theme implements a shared TypeScript section contract (`NavProps`, `HeroProps`, `FooterProps`, `GalleryProps`, etc.) so any theme can render any school's content.
- `theme_slug` is stored server-side on the School/tenant model — the source of truth, fetched via API. The theme only controls layout/presentation; content (hero text, images, nav links) comes from the backend's Front Door endpoints.

---

## 8. Repository Structure

```
tsp/
├── backend/     Django/DRF — see backend/README.md for the full app-by-app breakdown
├── frontend/    Next.js — see frontend/README.md for route groups and feature structure
├── docs/        Architecture decision records, infrastructure notes, gate tracking
└── README.md    This file
```

---

## 9. Getting Started

See the setup steps in `docs/setup.md` (backend: virtualenv, Postgres, migrations, seed data; frontend: Node version, env vars, dev server). Both apps run locally against the same local Postgres instance; tenant resolution works locally via `.localhost` subdomains or a `/etc/hosts` override for testing custom-domain behavior.

---

## 10. Who Owns What (for the team)

- **Daniel** builds the architectural seams personally before delegating: tenant-resolution middleware, the theme contract, and the auth/permission skeleton. These are the pieces where a wrong decision is expensive to unwind later.
- **Frontend developer** builds feature UI inside the established route groups and theme contract once those seams exist.
- **AI collaborators (Claude, ChatGPT):** treat this README, and the gates in §3 especially, as binding context for any task in this repo — not just background reading.

---

*Last updated: August 2026. This file should be kept current as architecture evolves — it is the fastest way for a new team member or AI session to get correctly oriented.*