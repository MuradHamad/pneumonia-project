# Pneumonia Severity Assessment System

A multi-modal AI web application that assesses pneumonia severity from chest X-rays combined with clinical data (vitals, labs). Clinicians upload cases, receive AI-generated severity scores and heatmaps, chat with an RAG-powered assistant, and export clinical reports.

**Graduation Project (GP2) — University of Petra, Software Engineering — Sadeen Al-Kalili Qais Qasem Murad Hamad**

---

## Features

- **Authentication** — Session-based login, forced password reset for admin-created accounts
- **Patient management** — Register patients, view case history per patient
- **Case creation** — 3-step flow: upload X-ray → enter clinical data → review & submit
- **AI diagnosis** — Fusion model combines visual + clinical features, returns severity score, risk class (I–V), heatmap, confidence
- **RAG chatbot** — Per-case conversational assistant with access to case context and history
- **Report generation** — AI-simplified clinical reports, exportable as PDF or CSV
- **Admin panel** — Manage clinician accounts, system overview

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x (Python 3.11+) |
| Database | SQLite |
| Frontend | Django templates + Tailwind CSS (CDN) |
| AI Model | PyTorch (trained separately, plugged in as `.pt`) |
| Auth | Django sessions, AbstractUser |

---

## Project structure

```
pneumonia-project/
├── CLAUDE.md              # Instructions for Claude Code
├── README.md              # This file
├── requirements.txt
├── manage.py
├── pneumonia/             # Django project settings
├── apps/
│   ├── accounts/          # User, Admin, Clinician
│   ├── patients/          # Patient
│   ├── cases/             # PatientCase, ClinicalData
│   ├── reports/           # Report
│   └── chat/              # ChatMessage
├── services/
│   ├── fusion_model.py    # AI diagnosis service
│   └── chatbot.py         # RAG chatbot service
├── templates/
├── static/
├── media/                 # Uploaded X-rays, heatmaps
└── docs/
    ├── schema.md
    ├── ui-design.md
    ├── phases.md
    └── diagrams/
```

---

## Documentation

- [`docs/schema.md`](docs/schema.md) — Database schema (every table, field, constraint)
- [`docs/ui-design.md`](docs/ui-design.md) — UI design system, pages, components
- [`docs/phases.md`](docs/phases.md) — Implementation phases
- [`docs/diagrams/`](docs/diagrams/) — UML diagrams (class, use case, sequence)

---

## Getting started

```bash
# Clone and set up
git clone <repo>
cd pneumonia-project

# Virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
```

App runs at `http://localhost:8000`.

---

## Status

In active development. See [`docs/phases.md`](docs/phases.md) for current progress.

---

## License

Academic project — University of Petra, 2026.
