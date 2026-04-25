# Database Schema — Pneumonia Severity Assessment System

**Stack:** Django 5.x + SQLite
**Source of truth:** Class diagram (GP2) + trained DenseNet121 fusion model

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

---

## 3. `clinical_data` ⚠️ UPDATED FOR PHASE 11

Fields match the trained DenseNet121 model's expected inputs (MIMIC-CXR dataset).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK, auto-increment | |
| `age` | Integer | NOT NULL | Years |
| `bun` | FLOAT | NOT NULL | Blood Urea Nitrogen, mg/dL |
| `hr` | Integer | NOT NULL | Heart Rate, bpm |
| `sys_bp` | Integer | NOT NULL | Systolic Blood Pressure, mmHg |
| `rr` | Integer | NOT NULL | Respiratory Rate, breaths/min |
| `temp_fahrenheit` | FLOAT | NOT NULL | Temperature stored as Fahrenheit (model-native unit) |
| `spo2` | FLOAT | NOT NULL | Oxygen Saturation, % |
| `gcs_total` | Integer | NOT NULL, CHECK 3 ≤ gcs_total ≤ 15 | Glasgow Coma Scale total |

**Notes:**
- The form accepts Celsius OR Fahrenheit via a unit toggle; values are stored in Fahrenheit.
- Field order matters: Age, BUN, HR, SysBP, RR, Temp, SpO2, GCS_Total — this is the exact order the scaler and model expect.
- No `urea`, `ph`, `wbc_count`, or `confusion` fields. Those were in the old placeholder schema; the trained model does not use them.

---

## 4. `patient_cases` ⚠️ UPDATED FOR PHASE 11

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | Integer | PK, auto-increment | |
| `patient_id` | Integer | FK → `patients.id`, NOT NULL | |
| `clinician_id` | Integer | FK → `users.id`, NOT NULL | |
| `clinical_data_id` | Integer | FK → `clinical_data.id`, UNIQUE, NOT NULL | |
| `xray_image_path` | VARCHAR(255) | NOT NULL | Relative path under `MEDIA_ROOT` |
| `heatmap_path` | VARCHAR(255) | nullable | Grad-CAM overlay image path |
| `diag_probability` | FLOAT | nullable, range 0.0–1.0 | Sigmoid output: P(pneumonia) |
| `severity_probability` | FLOAT | nullable, range 0.0–1.0 | Sigmoid output: P(severe) |
| `has_pneumonia` | BOOLEAN | nullable | Derived: diag_probability > 0.5 |
| `is_severe` | BOOLEAN | nullable | Derived: severity_probability > 0.5 |
| `status` | VARCHAR(10) | NOT NULL, default 'PENDING', CHECK IN ('PENDING', 'DONE', 'FAILED') | |
| `created_at` | DATETIME | auto-set on create | |

**Notes:**
- All AI output fields stay NULL until model inference completes. Status flips to 'DONE' on success or 'FAILED' on error.
- `has_pneumonia` and `is_severe` are derived booleans for easy querying/display; the raw probabilities remain the source of truth.
- **Removed from old schema:** `severity_score` (float 0-1), `risk_class` (I–V enum), `confidence_score`. The model does not produce a CURB-65 risk class directly — it produces two binary probabilities.

---

## 5. `reports`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `patient_case_id` | Integer | FK → `patient_cases.id`, UNIQUE, NOT NULL |
| `simplified_text` | TEXT | NOT NULL |
| `medication_instructions` | TEXT | NOT NULL |
| `format` | VARCHAR(3) | NOT NULL, CHECK IN ('PDF', 'CSV') |
| `generated_at` | DATETIME | auto-set on create |

No changes from previous version.

---

## 6. `chat_messages`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `patient_case_id` | Integer | FK → `patient_cases.id`, NOT NULL, INDEXED |
| `sender` | VARCHAR(10) | NOT NULL, CHECK IN ('CLINICIAN', 'BOT') |
| `content` | TEXT | NOT NULL |
| `timestamp` | DATETIME | auto-set on create, INDEXED |

No changes.

---

## Relationships

```
User (1) ──registers──< (N) Patient
User (1) ──creates────< (N) PatientCase
Patient (1) ──has─────< (N) PatientCase
PatientCase (1) ──◆─── (1) ClinicalData
PatientCase (1) ──◆─── (0..1) Report
PatientCase (1) ──◆──< (N) ChatMessage
```

---

## Services (NOT database tables)

- **FusionModel** — loads `p3_best_densenet.pth` + `clinical_scaler.joblib`, runs inference, generates Grad-CAM heatmap
- **ChatBot** — stateless, called during chat

---

## Migration notes (Phase 11)

Moving from the placeholder schema to this one requires:
1. Drop old columns from `clinical_data`: `blood_pressure`, `respiratory_rate`, `temperature`, `urea`, `ph`, `wbc_count`, `confusion`
2. Add new columns: `bun`, `hr`, `sys_bp`, `rr`, `temp_fahrenheit`, `gcs_total`
3. Drop old columns from `patient_cases`: `severity_score`, `risk_class`, `confidence_score`
4. Add new columns: `diag_probability`, `severity_probability`, `has_pneumonia`, `is_severe`
5. Add 'FAILED' to the `status` CHECK constraint
6. Existing test data will be lost — that's acceptable since the schema change is fundamental. Delete old patient_cases and clinical_data rows.
