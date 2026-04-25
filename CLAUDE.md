# CLAUDE.md

Instructions for Claude Code working on this project. Read this file first on every session.

---

## Project

**Multi-Modal AI System for Pneumonia Severity Assessment**
Graduation Project (GP2) — University of Petra, Software Engineering
Author: Murad Hamad

A web application where clinicians upload chest X-rays + clinical data, an AI fusion model returns a severity score and risk class with a heatmap, and reports can be generated and exported.

---

## Stack (locked, do not change)

- **Backend:** Django 5.x (Python 3.11+)
- **Database:** SQLite
- **Frontend:** Django templates + Tailwind CSS (CDN, no build step)
- **AI model:** PyTorch, trained separately in Colab, plugged in as `.pt` file
- **Auth:** Django's built-in auth (AbstractUser)

Do not suggest Next.js, React, FastAPI, PostgreSQL, or any other replacement. These were deliberately chosen.

---

## Documentation (source of truth)

Always read these before making design decisions:

- `docs/schema.md` — database schema, every table, every constraint
- `docs/ui-design.md` — pages, components, colors, layout
- `docs/phases.md` — build order
- `docs/diagrams/` — UML diagrams (class, use case, 4 sequence diagrams)

**If the code ever conflicts with the diagrams or schema, the diagrams win. Ask before diverging.**

---

## Architectural principles

1. **MVC strictly.** Models in `models.py`, views in `views.py`, templates in `templates/`. No business logic in templates.
2. **Services are stateless.** `FusionModel` and `ChatBot` live in `services/` as plain Python classes/modules. They are NOT Django models and have NO database tables.
3. **Composition matters.** `PatientCase` owns `ClinicalData`, `Report`, and `ChatMessage`. Deleting a case cascades.
4. **AI output fields are nullable.** `severity_score`, `risk_class`, `heatmap_path`, `confidence_score` stay NULL until the fusion model finishes and status flips to `DONE`.
5. **Temp credentials flow.** Admin-created clinicians get `must_change_password=True`. Login middleware redirects them to `/change-password` until resolved.

---

## What to do

- Read `docs/schema.md` and `docs/ui-design.md` before writing any code.
- Use Django's `AbstractUser` for the User model, named `User`.
- Use `DecimalField` or `FloatField` consistently — match what's in schema.md.
- Use Tailwind utility classes directly in templates. No custom CSS files unless absolutely necessary.
- Use Django's `{% extends 'base.html' %}` pattern. Put the sidebar + header in `base.html`.
- Use Django forms (`ModelForm` where possible) for all user input.
- Use Django's messages framework for toasts.
- Write one migration per feature phase, not per model.
- Add docstrings on models and service classes.
- Use Lucide icons via CDN or inline SVG. No icon packages.
- Use Inter font from Google Fonts.

## What NOT to do

- Do not add libraries not already in `requirements.txt` without asking.
- Do not create a REST API (DRF, etc.) — forms post directly to views.
- Do not use JWT or custom auth — Django sessions only.
- Do not create tables for `FusionModel` or `ChatBot` — they are services.
- Do not use `localStorage` or `sessionStorage`.
- Do not "improve" the color palette or typography — it's locked in `ui-design.md`.
- Do not add features not in `docs/phases.md` without asking.
- Do not generate fake/placeholder medical data in migrations — leave tables empty or use a clearly-marked `seed.py` script.
- Do not run migrations automatically — always show the commands and let the user run them.

---

## Code style

- Follow PEP 8
- Use `black` formatting (line length 100)
- Use type hints on function signatures
- Use `snake_case` for Python, `kebab-case` for URLs, `camelCase` only in JS if any
- Model fields use `snake_case` (e.g., `must_change_password`) even though UML uses `camelCase`
- One class per file when a class exceeds ~100 lines
- Imports ordered: stdlib → Django → third-party → local

---

## Running the project

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser  # creates first admin

# Run
python manage.py runserver
```

App runs at `http://localhost:8000`.

---

## Model placeholder

# CLAUDE.md Addendum — Phase 11

Add these notes to the existing `CLAUDE.md` (or replace relevant sections).

---

## Updated: Model placeholder section

**REMOVE the entire "Model placeholder" section** in CLAUDE.md. The placeholder is gone as of Phase 11. Replace with:

### Real fusion model (Phase 11+)

The trained PyTorch model lives at `models/p3_best_densenet.pth`. It is loaded once at Django startup and held as a module-level singleton in `services/fusion_model.py`.

Critical facts:
- Architecture class: `MultiTaskPneumoniaModel` — DenseNet121 + 8-dim clinical MLP + fusion
- The checkpoint was saved with `self.vision_model = densenet`. Do NOT rename this attribute — it will break loading.
- Model outputs two logits: `(diag_logit, severity_logit)`. Both need `torch.sigmoid()` to get probabilities 0.0–1.0.
- Clinical input must be in exact order: age, bun, hr, sys_bp, rr, temp_fahrenheit, spo2, gcs_total
- Clinical inputs must be scaled with `models/clinical_scaler.joblib` BEFORE the forward pass
- Image preprocessing: resize 224×224, ToTensor, Normalize with ImageNet mean/std ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

---

## New rules

1. **Never load the model per-request.** It's a singleton. Use `AppConfig.ready()` or a module-level variable with lazy init.

2. **`torch.no_grad()` for inference.** Except during Grad-CAM (which needs gradients on the image input).

3. **Grad-CAM target layer is `model.vision_model.features[-1]`** — not `img_extractor`. The project2 notebook has a bug that references a nonexistent attribute.

4. **Temperature stored in Fahrenheit.** The model was trained on Fahrenheit. The form accepts either °C or °F with a toggle; conversion happens at form-clean time, never at inference.

5. **If the model file is missing, fail cleanly.** Don't crash Django on startup. Log a warning, set a module-level flag `MODEL_AVAILABLE = False`, and return `status='FAILED'` with an explanation for any diagnosis attempts.

6. **No medical recommendations.** CLAUDE.md already forbids inventing clinical logic. With the real model, this applies even more strictly. The model outputs probabilities; we display them honestly. Reports should say "pneumonia probability 73%" not "likely has pneumonia."

---

## Files that must not be committed

Add these to `.gitignore`:
```
models/*.pth
models/*.pt
models/*.joblib
media/heatmaps/
```
---

## ChatBot placeholder

Until RAG is wired up, `services/chatbot.py` returns a canned response that at least references the case context, so the UI flow works end-to-end:

```python
def process_query(query: str, case) -> str:
    return f"[Placeholder] Based on case #{case.id} (Risk Class {case.risk_class}), here is a response to: {query}"
```

---

## When stuck

- Check the relevant sequence diagram in `docs/diagrams/`
- Ask clarifying questions rather than guessing
- If a design decision isn't in the docs, flag it and wait for input
- Never invent medical logic or clinical thresholds — use the placeholder values
