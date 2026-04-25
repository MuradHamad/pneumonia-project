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

# Phase 11 — Real Model Integration (REPLACES old Phase 11 in phases.md)

**Goal:** Replace placeholder fusion model with the trained DenseNet121 multi-task model. This phase requires schema migration first because the trained model uses different clinical fields than the placeholder.

---

## 11.A — Schema migration

1. Update `ClinicalData` model per new `docs/schema.md`:
   - REMOVE: `blood_pressure`, `respiratory_rate`, `temperature`, `urea`, `ph`, `wbc_count`, `confusion`
   - ADD: `bun`, `hr`, `sys_bp`, `rr`, `temp_fahrenheit`, `gcs_total`
   - Keep: `age`, `spo2`
2. Update `PatientCase` model per new schema:
   - REMOVE: `severity_score`, `risk_class`, `confidence_score`
   - ADD: `diag_probability`, `severity_probability`, `has_pneumonia`, `is_severe`
   - Add `'FAILED'` to status choices
3. Delete existing test data (old `PatientCase` and `ClinicalData` rows) — schema change is incompatible
4. Create migration, run it
5. Update all templates and views that reference removed fields

## 11.B — Form update

1. Update case creation Step 2 (clinical data form) to collect the 8 new fields in this exact order: Age, BUN, HR, SysBP, RR, Temp, SpO2, GCS_Total
2. Add a temperature unit toggle (°C / °F). Default °F. Convert Celsius → Fahrenheit on save: `F = C × 9/5 + 32`
3. Add helper text under each field with normal ranges (e.g., SpO2 95–100%, HR 60–100 bpm, GCS 15 for normal)
4. Server-side validation for reasonable clinical ranges

## 11.C — Service dependencies

1. Add to `requirements.txt`:
   - `torch>=2.0`
   - `torchvision`
   - `joblib`
   - `opencv-python-headless` (for Grad-CAM colormap)
2. Add artifacts folder `models/` at project root (gitignored):
   - `models/p3_best_densenet.pth` (unzip the provided checkpoint)
   - `models/clinical_scaler.joblib`
3. Do NOT commit these files to git — add to `.gitignore`

## 11.D — Model service rewrite

Rewrite `services/fusion_model.py` completely.

**1. Model class** (copy this exact class — checkpoint was saved with these attribute names):

```python
import torch
import torch.nn as nn
import torchvision.models as models

class MultiTaskPneumoniaModel(nn.Module):
    def __init__(self, num_clinical_features=8, num_classes=2):
        super().__init__()
        densenet = models.densenet121(weights=None)
        self.vision_features = densenet.classifier.in_features
        densenet.classifier = nn.Identity()
        self.vision_model = densenet
        
        self.clinical_mlp = nn.Sequential(
            nn.Linear(num_clinical_features, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.3),
        )
        fusion_dim = self.vision_features + 32
        self.fc = nn.Linear(fusion_dim, num_classes)
    
    def forward(self, img, clinical):
        img_features = self.vision_model(img)
        clin_features = self.clinical_mlp(clinical)
        fused = torch.cat((img_features, clin_features), dim=1)
        out = self.fc(fused)
        # Split into two heads — match training output convention
        return out[:, 0].unsqueeze(1), out[:, 1].unsqueeze(1)
```

**2. Singleton loader** — load model + scaler ONCE on Django startup, not per request. Use module-level variables or `AppConfig.ready()`.

**3. Preprocessing** — exactly as provided:

```python
from torchvision import transforms as T

preprocess = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
```

**4. Clinical scaling** — use the provided scaler:

```python
import joblib
scaler = joblib.load('models/clinical_scaler.joblib')
# clinical_array shape: (1, 8) in order [age, bun, hr, sys_bp, rr, temp_f, spo2, gcs]
scaled = scaler.transform(clinical_array)
```

**5. `diagnose()` function** — new signature:

```python
def diagnose(xray_path: str, clinical_data: dict) -> dict:
    """
    Returns:
        {
            "diag_probability": float 0.0-1.0,
            "severity_probability": float 0.0-1.0,
            "has_pneumonia": bool,
            "is_severe": bool,
            "heatmap_path": str (relative to MEDIA_ROOT),
        }
    """
    # 1. Load + preprocess image
    # 2. Build clinical tensor in exact order, scale it
    # 3. Model forward pass (torch.no_grad for inference)
    # 4. Apply sigmoid to both logits → probabilities
    # 5. Generate Grad-CAM heatmap (requires separate gradient pass, see 11.E)
    # 6. Save heatmap to MEDIA_ROOT/heatmaps/<uuid>.png
    # 7. Return dict
```

Field order in clinical_data dict must be: `age, bun, hr, sys_bp, rr, temp_fahrenheit, spo2, gcs_total`.

## 11.E — Grad-CAM integration

Create `services/grad_cam.py` with a `DenseNetGradCAM` class. Base it on project2.ipynb Cell 11, **with these required fixes** (the notebook version has bugs):

1. Hook target layer: use `self.model.vision_model.features[-1]` — the last block of the DenseNet features (`norm5`). The notebook references `self.model.img_extractor[-1]` which doesn't exist on our class.
2. Hook registration should be in `__init__` (same as notebook)
3. In `generate_heatmap`, the model returns a tuple `(p_diag, p_sev)` — don't use `p_diag[0]` directly. Use `p_diag.squeeze()` to get a scalar before calling `.backward()`.
4. Accept `target` parameter: `'diag'` or `'severity'`. Default to `'diag'`.

Then in the service flow:
- After getting predictions, run the Grad-CAM pass to get a 224×224 heatmap
- Overlay with `cv2.applyColorMap(cam, cv2.COLORMAP_JET)` and `cv2.addWeighted(original, 0.6, heatmap, 0.4, 0)` (see project2.ipynb Cell 12)
- Save as PNG to `MEDIA_ROOT/heatmaps/<case_id>.png`

## 11.F — Wire it up

1. On case submission (case review step), call `diagnose()` synchronously
2. Save all 5 result fields to the PatientCase
3. On failure (model exception), set `status='FAILED'`, log the error with full traceback. Do NOT crash the view — show a user-friendly error page.
4. Update case detail page to display:
   - **Diagnosis result:** "Pneumonia detected" or "No pneumonia" with `diag_probability` as a percentage + confidence bar
   - **If `has_pneumonia`:** also show severity — "Severe" or "Non-severe" with `severity_probability`
   - **Grad-CAM overlay:** tab switcher between "Original X-Ray" and "AI Focus (Heatmap)"
5. Update report generation (from Phase 7) — replace all references to `risk_class` and `severity_score` with the new fields. Report text should reference pneumonia probability + severity probability.

## 11.G — Testing

Before marking done:
- [ ] Upload a real chest X-ray + realistic clinical values → case completes with status='DONE'
- [ ] `diag_probability` and `severity_probability` both between 0.0 and 1.0
- [ ] Grad-CAM heatmap file exists in `MEDIA_ROOT/heatmaps/`
- [ ] Case detail page displays both probabilities correctly
- [ ] Heatmap tab shows the overlay image
- [ ] Report page no longer references `risk_class` or `severity_score`
- [ ] Temperature unit toggle works (enter 37°C → stored as 98.6°F)
- [ ] Failure test: rename `p3_best_densenet.pth` → submit case → status='FAILED', error logged, no crash
- [ ] Note inference time (expect 2-10s on CPU)

**Done when:** A real submitted case produces a real AI diagnosis with heatmap, all stored and displayed correctly. No references to old placeholder fields remain anywhere in the codebase.
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
