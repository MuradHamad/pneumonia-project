# Database Schema — Pneumonia Severity Assessment System

**Stack:** Django 5.x + SQLite
**Source of truth:** Class diagram (GP2)

---

## 1. `users`

Extends Django's `AbstractUser`. Single table, role-based.

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `name` | VARCHAR(100) | NOT NULL |
| `email` | VARCHAR(150) | UNIQUE, NOT NULL |
| `password` | VARCHAR(255) | NOT NULL (hashed by Django) |
| `role` | VARCHAR(10) | NOT NULL, CHECK IN ('ADMIN', 'CLINICIAN') |
| `must_change_password` | BOOLEAN | NOT NULL, default TRUE |
| `created_at` | DATETIME | auto-set on create |

**Notes:**
- Use Django's `AbstractUser` as the base class.
- `must_change_password` forces password reset on first login for admin-created clinicians.

---

## 2. `patients`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `national_id` | VARCHAR(20) | UNIQUE, NOT NULL |
| `full_name` | VARCHAR(150) | NOT NULL |
| `date_of_birth` | DATE | NOT NULL |
| `gender` | VARCHAR(6) | NOT NULL, CHECK IN ('MALE', 'FEMALE') |
| `phone_number` | VARCHAR(20) | nullable |
| `registered_by_id` | Integer | FK → `users.id`, NOT NULL |
| `created_at` | DATETIME | auto-set on create |

**Notes:**
- `registered_by_id` points to the clinician who first registered the patient.
- Age is computed from `date_of_birth` at runtime, not stored.

---

## 3. `clinical_data`

One-to-one with `patient_cases`. Represents vitals/labs at time of diagnosis.

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `age` | Integer | NOT NULL |
| `spo2` | FLOAT | NOT NULL |
| `blood_pressure` | VARCHAR(15) | NOT NULL |
| `respiratory_rate` | Integer | NOT NULL |
| `temperature` | FLOAT | NOT NULL |
| `urea` | FLOAT | NOT NULL |
| `ph` | FLOAT | NOT NULL |
| `wbc_count` | FLOAT | NOT NULL |
| `confusion` | BOOLEAN | NOT NULL |

**Notes:**
- `age` is stored here as a clinical snapshot (age at time of case), distinct from the patient's current age.
- `confusion` is the CURB-65 confusion flag.

---

## 4. `patient_cases`

Core entity. Each row is one diagnosis session.

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `patient_id` | Integer | FK → `patients.id`, NOT NULL |
| `clinician_id` | Integer | FK → `users.id`, NOT NULL |
| `clinical_data_id` | Integer | FK → `clinical_data.id`, UNIQUE, NOT NULL |
| `xray_image_path` | VARCHAR(255) | NOT NULL |
| `severity_score` | FLOAT | nullable |
| `risk_class` | VARCHAR(3) | nullable, CHECK IN ('I', 'II', 'III', 'IV', 'V') |
| `heatmap_path` | VARCHAR(255) | nullable |
| `confidence_score` | FLOAT | nullable |
| `status` | VARCHAR(10) | NOT NULL, default 'PENDING', CHECK IN ('PENDING', 'DONE') |
| `created_at` | DATETIME | auto-set on create |

**Notes:**
- AI output fields (`severity_score`, `risk_class`, `heatmap_path`, `confidence_score`) are NULL until fusion model finishes and status flips to `DONE`.
- `xray_image_path` and `heatmap_path` are relative paths inside Django's `MEDIA_ROOT`.

---

## 5. `reports`

Generated on demand by the clinician. FK lives here (not on PatientCase) because reports are optional.

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `patient_case_id` | Integer | FK → `patient_cases.id`, UNIQUE, NOT NULL |
| `simplified_text` | TEXT | NOT NULL |
| `medication_instructions` | TEXT | NOT NULL |
| `format` | VARCHAR(3) | NOT NULL, CHECK IN ('PDF', 'CSV') |
| `generated_at` | DATETIME | auto-set on create |

**Notes:**
- One report per case (UNIQUE on `patient_case_id`).
- Created only when the clinician clicks "Generate Report."

---

## 6. `chat_messages`

Stores RAG conversation history, scoped per patient case.

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `patient_case_id` | Integer | FK → `patient_cases.id`, NOT NULL, INDEXED |
| `sender` | VARCHAR(10) | NOT NULL, CHECK IN ('CLINICIAN', 'BOT') |
| `content` | TEXT | NOT NULL |
| `timestamp` | DATETIME | auto-set on create, INDEXED |

**Notes:**
- Chatbot reads prior messages in the same case as conversational context.
- No FK to User on sender — `sender` is an enum because 'BOT' is not a user.

---

## Relationships
User(CLINICIAN) (1) ──registers──< (N) Patient
User(CLINICIAN) (1) ──creates────< (N) PatientCase
Patient (1) ──has─────< (N) PatientCase
PatientCase (1) ──◆─── (1) ClinicalData
PatientCase (1) ──◆─── (0..1) Report
PatientCase (1) ──◆──< (N) ChatMessage

`◆` = composition (child cannot exist without parent)

---

## Services (NOT database tables)

- **FusionModel** — stateless service, called during diagnosis
- **ChatBot** — stateless service, called during chat

These are in the class diagram but do NOT map to tables.

---

## Implementation order for Claude Code

1. `users` (custom User model extending AbstractUser)
2. `patients`
3. `clinical_data`
4. `patient_cases`
5. `reports`
6. `chat_messages`

Create in this order to respect FK dependencies.