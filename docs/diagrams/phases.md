# Implementation Phases

Build order for Claude Code. Each phase = one focused session. Finish and test before moving on.

---

## Phase 0 — Project Setup

**Goal:** Empty but runnable Django project with Tailwind.

Tasks:
1. Create Django project `pneumonia` and apps: `accounts`, `patients`, `cases`, `reports`, `chat`
2. Configure `settings.py`: SQLite, `MEDIA_ROOT`, `MEDIA_URL`, `STATIC_ROOT`, installed apps
3. Create `base.html` with Tailwind CDN, Inter font, Lucide icons, empty sidebar + header shell
4. Create `requirements.txt` with: Django, Pillow, reportlab (for PDF), python-dotenv
5. Add `.env` + `.gitignore`
6. Verify `python manage.py runserver` works and shows a blank dashboard page

**Done when:** Server runs, base template loads, sidebar shell visible.

---

## Phase 1 — User Model & Authentication

**Goal:** Login, logout, forced password change, role-based access.

Tasks:
1. Create custom `User` model extending `AbstractUser` with `role`, `must_change_password`, `name`, `created_at`
2. Update `AUTH_USER_MODEL` in settings
3. Build login view + template (`/login`)
4. Build logout view
5. Build forced change-password view + middleware that redirects users with `must_change_password=True`
6. Build settings page (`/settings`) with change-password form
7. Add login-required decorator on all protected views
8. Add role-check decorator (`@clinician_required`, `@admin_required`)
9. Create first admin via `createsuperuser`

**Done when:** Can log in as admin, forced to change password on first login, can log out.

---

## Phase 2 — Sidebar & Layout

**Goal:** Full left sidebar with role-based nav items.

Tasks:
1. Build sidebar in `base.html`: logo, user info, nav items, bottom actions
2. Show/hide admin-only nav items based on `user.role`
3. Highlight active nav item based on URL
4. Build dashboard shell (`/`) with placeholder stat cards
5. Build page header with title slot + action buttons slot

**Done when:** Sidebar matches `ui-design.md`, navigation between blank pages works.

---

## Phase 3 — Patient Management

**Goal:** CRUD for patients + search.

Tasks:
1. Create `Patient` model per `schema.md`
2. Migration
3. Build patients list page (`/patients`) with search by name and national ID
4. Build patient registration form (`/patients/new`) with duplicate-national-ID check
5. Build patient detail page (`/patients/<id>`) — info card + empty "Case History" table
6. Add "Register Patient" button in sidebar

**Done when:** Can register patients, search, view patient detail. National ID uniqueness enforced.

---

## Phase 4 — Case Creation Flow (Without AI)

**Goal:** 3-step wizard creates a case record with status=PENDING.

Tasks:
1. Create `ClinicalData` and `PatientCase` models per `schema.md`
2. Migrations
3. Step 1 view `/cases/new?patient_id=X` — upload X-ray (validate type, size), save file to `MEDIA_ROOT/xrays/`
4. Step 2 view — clinical data form (9 fields + confusion toggle)
5. Step 3 view — review + submit (sets status=PENDING)
6. Step indicator component (reusable)
7. Patient detail page now shows real case history

**Done when:** Can create a case end-to-end, X-ray uploads work, clinical data saves, case appears in patient history with PENDING status.

---

## Phase 5 — AI Fusion Service (Placeholder)

**Goal:** Plug in placeholder fusion model, flip status to DONE.

Tasks:
1. Create `services/fusion_model.py` with `diagnose(xray_path, clinical_data)` placeholder returning random realistic values
2. Create `services/__init__.py`
3. On case submission, call `diagnose()` synchronously, save results to `PatientCase`, set status=DONE
4. Build case detail page (`/cases/<id>`) showing X-ray, clinical data, diagnosis result card (risk class badge, severity score, confidence meter)
5. Handle PENDING state with loading placeholder
6. Build cases list page (`/cases`) with filters

**Done when:** Submitting a case returns a diagnosis, result page shows all fields correctly. Swapping `diagnose()` later will be a one-file change.

---

## Phase 6 — Chatbot (Placeholder)

**Goal:** Per-case chat interface with persisted history.

Tasks:
1. Create `ChatMessage` model per `schema.md`
2. Migration
3. Create `services/chatbot.py` with `process_query(query, case)` placeholder
4. Build chat view on case detail page (side drawer or inline panel)
5. Form posts query → save user ChatMessage → call `process_query()` → save bot ChatMessage → redirect/refresh
6. Optional: HTMX for smooth append without full page reload

**Done when:** Can chat on a case, messages persist, bot responds with placeholder text referencing case context.

---

## Phase 7 — Report Generation

**Goal:** Generate and export PDF/CSV reports.

Tasks:
1. Create `Report` model per `schema.md`
2. Migration
3. Add `generate_report()` utility that composes report content from case + clinical data + AI output
4. Build report preview page (`/cases/<id>/report`) — shows draft, "Generate Report" button if not yet created
5. Add PDF export using `reportlab`
6. Add CSV export
7. "Generate Report" button on case detail page

**Done when:** Can generate a report, preview it, export as PDF and CSV.

---

## Phase 8 — Admin Panel

**Goal:** Clinician management + system overview.

Tasks:
1. Build `/admin/clinicians` list
2. Build `/admin/clinicians/new` — generates temp password, sets `must_change_password=True`
3. Email temp credentials (use Django's console backend for dev)
4. Build `/admin/overview` — system stats + recent activity
5. Restrict all admin routes with `@admin_required`

**Done when:** Admin can create clinician accounts, view system stats. New clinicians forced to change password on first login.

---

## Phase 9 — Dashboard Widgets

**Goal:** Real data in the clinician dashboard.

Tasks:
1. Populate 4 stat cards with real counts
2. Recent Cases table with real data
3. Optional: severity distribution bar chart (use simple HTML/CSS bars, no chart library unless needed)
4. Empty states

**Done when:** Dashboard shows real counts and recent cases.

---

## Phase 10 — Polish & Edge Cases

**Goal:** Production-ready feel.

Tasks:
1. Form validation messages
2. Toast notifications for all success/error actions
3. Loading states on slow actions (AI diagnosis)
4. Empty states for every list
5. 404 and 500 pages
6. Responsive sidebar (hamburger on mobile)
7. Favicon + page titles

**Done when:** App feels finished, no unhandled states, visually matches `ui-design.md`.

---

## Phase 11 — Real Model Swap (After Colab training)

**Goal:** Replace placeholder with trained PyTorch model.

Tasks:
1. Export trained model from Colab as `pneumonia_model.pt`
2. Place in `models/` directory
3. Update `services/fusion_model.py` to load and run the real model
4. Handle preprocessing (image resize, normalization) matching training pipeline
5. Generate real heatmaps (Grad-CAM or similar)
6. Test end-to-end with real X-rays

**Done when:** Real model returns real predictions, heatmaps render on case detail page.

---

## Phase 12 — RAG Chatbot (If time permits)

**Goal:** Replace placeholder chatbot with real RAG.

Tasks:
1. Choose embedding approach (sentence-transformers or API)
2. Build context from case data + prior ChatMessages
3. Connect to LLM (Gemini, Claude API, or local model)
4. Update `services/chatbot.py` with real implementation

**Done when:** Chatbot gives grounded, context-aware responses.

---

## Notes

- Phases 1–10 are the core MVP. Ship this first.
- Phases 11–12 are the "real AI" phase — can be done after MVP demo.
- Each phase should end with a working, demoable state.
- Commit at the end of each phase with a clear message.
