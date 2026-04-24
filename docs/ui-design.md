# UI Design — Pneumonia Severity Assessment System

**Stack:** Django templates + Tailwind CSS (CDN)
**Style:** Clinical / medical, clean whites, blue accents
**Layout:** Fixed left sidebar, main content area
**Language:** English only (LTR)

---

## 1. Design System

### 1.1 Color Palette

| Token | Hex | Use |
|---|---|---|
| `primary` | `#1E40AF` | Primary buttons, active nav, links |
| `primary-hover` | `#1E3A8A` | Button hover states |
| `primary-light` | `#DBEAFE` | Active nav background, info banners |
| `surface` | `#FFFFFF` | Cards, panels, main background |
| `background` | `#F8FAFC` | Page background behind cards |
| `border` | `#E2E8F0` | Borders, dividers |
| `text-primary` | `#0F172A` | Headings, body text |
| `text-secondary` | `#64748B` | Labels, helper text |
| `text-muted` | `#94A3B8` | Disabled, timestamps |
| `success` | `#16A34A` | Normal/Low severity, success toasts |
| `warning` | `#F59E0B` | Moderate severity |
| `danger` | `#DC2626` | High severity, errors, destructive actions |
| `info` | `#0891B2` | Informational states |

### 1.2 Severity / Risk Class Colors

| Class | Color | Hex |
|---|---|---|
| I (low) | Green | `#16A34A` |
| II | Lime | `#65A30D` |
| III | Amber | `#F59E0B` |
| IV | Orange | `#EA580C` |
| V (highest) | Red | `#DC2626` |

### 1.3 Typography

- **Font family:** `Inter, system-ui, sans-serif` (Google Fonts CDN)
- **H1:** 30px / bold / `text-primary`
- **H2:** 24px / semibold / `text-primary`
- **H3:** 18px / semibold / `text-primary`
- **Body:** 15px / normal / `text-primary`
- **Small:** 13px / normal / `text-secondary`
- **Label:** 12px / medium / uppercase / `text-secondary`

### 1.4 Spacing

Tailwind default scale. Page padding: `p-6` or `p-8`. Card padding: `p-6`. Gap between cards: `gap-6`.

### 1.5 Component Styles

**Buttons**
- Primary: `bg-primary text-white rounded-lg px-4 py-2 font-medium hover:bg-primary-hover`
- Secondary: `bg-white border border-border text-text-primary rounded-lg px-4 py-2 hover:bg-background`
- Danger: `bg-danger text-white rounded-lg px-4 py-2 hover:opacity-90`
- Ghost: `text-primary hover:bg-primary-light rounded-lg px-3 py-2`

**Inputs**
- `bg-white border border-border rounded-lg px-3 py-2 focus:border-primary focus:ring-2 focus:ring-primary-light`

**Cards**
- `bg-surface rounded-xl border border-border p-6 shadow-sm`

**Badges**
- `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium`
- Color based on severity class or status

---

## 2. Layout Shell

### 2.1 Sidebar (fixed left, 240px wide)

**Top:**
- Logo + product name: "PneuDx" (or chosen name)
- Below logo: user's name + role badge

**Nav items (CLINICIAN):**
- Dashboard (home icon)
- Patients (users icon)
- Cases (file-text icon)
- New Case (plus icon) — highlighted button style
- Reports (document icon)

**Nav items (ADMIN only, shown in addition):**
- Divider labeled "ADMIN"
- Clinicians (user-cog icon)
- System Overview (chart icon)

**Bottom:**
- Settings (gear icon)
- Logout (logout icon)

**Active state:** `bg-primary-light text-primary` with left border accent `border-l-4 border-primary`.

### 2.2 Main content area

- Header bar (64px): page title on left, optional action buttons on right, user avatar dropdown far right
- Content below header: `p-8 bg-background min-h-screen`
- Max width for content: `max-w-7xl mx-auto`

### 2.3 Toast notifications

- Top-right, auto-dismiss after 4s
- Success (green), error (red), info (blue)

---

## 3. Pages

### 3.1 Login — `/login`

**Access:** Public
**Purpose:** Authenticate user

**Layout:** Centered card on full-height background (no sidebar).

**Components:**
- Centered card (max-width 400px)
- Logo at top
- H2: "Sign in to your account"
- Email input
- Password input
- "Sign in" primary button (full width)
- Small text below: "Contact your administrator if you forgot your password"

**Behavior:**
- On success: redirect to dashboard
- On failure: inline error above form
- If `must_change_password = true`: redirect to `/change-password` forced

---

### 3.2 Change Password (forced) — `/change-password`

**Access:** Logged-in users with `must_change_password = true`
**Purpose:** Force password reset on first login

**Layout:** Same centered card pattern as login.

**Components:**
- H2: "Set a new password"
- Info banner (blue): "You must change your temporary password before continuing."
- Current password input
- New password input
- Confirm new password input
- "Update password" primary button

**Behavior:**
- On success: set `must_change_password = false`, redirect to dashboard
- Show inline validation (min 8 chars, etc.)

---

### 3.3 Dashboard — `/` (clinician home)

**Access:** CLINICIAN (ADMIN sees admin dashboard instead)
**Purpose:** Overview + quick access

**Layout zones:**

**Row 1 — Stats cards (4 cards in a grid):**
- Total Patients (count + icon)
- Total Cases (count + icon)
- Cases This Week (count + trend arrow)
- Pending Diagnoses (count, warning color if > 0)

**Row 2 — Quick action:**
- Large call-to-action card: "Create New Case" button with description text

**Row 3 — Recent Cases (table card):**
- H3: "Recent Cases"
- Table with columns: Case ID, Patient Name, Risk Class (badge), Status (badge), Created, Actions (View button)
- Limit 10 rows
- "View all cases" link bottom-right

**Row 4 — Severity Distribution (optional chart card):**
- Bar chart showing count by risk class (I–V)

---

### 3.4 Patients List — `/patients`

**Access:** CLINICIAN, ADMIN
**Purpose:** Browse + search patients

**Layout:**
- Page header: "Patients" + "Register New Patient" primary button (top right)
- Search bar: input with placeholder "Search by name or national ID..."
- Filter dropdown (optional): gender
- Table:
  - Columns: Full Name, National ID, Date of Birth (age), Gender, Registered By, Actions
  - Actions: View, New Case
  - Pagination at bottom (25 per page)

**Empty state:** Centered message "No patients yet. Register your first patient."

---

### 3.5 Register Patient — `/patients/new`

**Access:** CLINICIAN, ADMIN
**Purpose:** Step 1 of case creation flow (or standalone)

**Layout:** Single-column form card.

**Components:**
- Breadcrumb: Patients > Register New
- H2: "Register New Patient"
- Form fields:
  - National ID (with inline check: "This ID already exists — [view patient]")
  - Full Name
  - Date of Birth (date picker)
  - Gender (radio buttons: Male / Female)
  - Phone Number (optional)
- "Cancel" secondary button + "Register & Create Case" primary button
- Secondary "Register only" ghost button

**Behavior:**
- Duplicate national ID → inline warning with link to existing patient
- On success with "Register & Create Case" → redirect to `/cases/new?patient_id=X`

---

### 3.6 Patient Detail — `/patients/<id>`

**Access:** CLINICIAN, ADMIN
**Purpose:** View patient info + case history

**Layout:**

**Top card — Patient Info:**
- Full name (H2)
- National ID, DOB (age), gender, phone
- Registered by + date
- "Edit" secondary button, "New Case" primary button

**Below — Case History table:**
- H3: "Case History"
- Columns: Case ID, Risk Class, Severity Score, Status, Created, Actions (View)
- Empty state: "No cases yet for this patient."

---

### 3.7 New Case — Step 1 — `/cases/new?patient_id=X`

**Access:** CLINICIAN
**Purpose:** Upload X-ray image

**Layout:**
- Breadcrumb: Cases > New
- Step indicator at top: **[1. X-Ray]** → [2. Clinical Data] → [3. Review]
- Patient info card (small, read-only): name, age, gender
- Upload card:
  - Drag-and-drop zone or "Browse files" button
  - Accepted: JPEG, PNG, DICOM (if supported)
  - Max size: 10 MB
  - Preview of uploaded image
- Bottom: "Back" secondary + "Next: Clinical Data" primary (disabled until file uploaded)

---

### 3.8 New Case — Step 2 — `/cases/new/<case_id>/clinical-data`

**Access:** CLINICIAN
**Purpose:** Enter clinical measurements

**Layout:**
- Step indicator: [1. X-Ray] → **[2. Clinical Data]** → [3. Review]
- Form card with 2-column grid:
  - Age (number)
  - SpO2 (%)
  - Blood Pressure (text, e.g. "120/80")
  - Respiratory Rate (breaths/min)
  - Temperature (°C)
  - Urea (mmol/L)
  - pH
  - WBC Count (×10⁹/L)
  - Confusion (toggle switch: Yes/No)
- Helper text under each field with normal ranges
- Bottom: "Back" + "Next: Review" primary

---

### 3.9 New Case — Step 3 — `/cases/new/<case_id>/review`

**Access:** CLINICIAN
**Purpose:** Review and submit for AI diagnosis

**Layout:**
- Step indicator: [1. X-Ray] → [2. Clinical Data] → **[3. Review]**
- Two-column layout:
  - **Left:** X-ray preview
  - **Right:** Clinical data summary (all values in a key-value list)
- Bottom: "Back" + "Submit for Diagnosis" primary button
- On submit: loading spinner overlay "Running AI diagnosis..." then redirect to result page

---

### 3.10 Case Detail / Result — `/cases/<id>`

**Access:** CLINICIAN, ADMIN
**Purpose:** View AI diagnosis output + chat + report actions

**Layout:**

**Top row — Case Header:**
- Patient name + link to patient
- Case ID + created date
- Status badge

**Main content — 2-column layout:**

**Left column (60%):**
- **X-Ray + Heatmap card:**
  - Tabs: "Original" / "Heatmap"
  - Image viewer
- **Clinical Data card:**
  - Read-only key-value grid

**Right column (40%):**
- **Diagnosis Result card:**
  - Risk Class (large badge, colored)
  - Severity Score (large number)
  - Confidence (progress bar + %)
  - Timestamp
- **Actions card:**
  - "Generate Report" primary button
  - "Chat with AI" secondary button (opens chat panel)

**Loading state:** If status = PENDING, show "AI is analyzing..." skeleton loader instead of diagnosis card.

---

### 3.11 Chat Panel — `/cases/<id>/chat` (or side drawer)

**Access:** CLINICIAN
**Purpose:** RAG chat scoped to this case

**Layout (side drawer from right, 400px wide, OR full page):**
- Header: "AI Assistant — Case #<id>"
- Scrollable message list:
  - User messages: right-aligned, `bg-primary text-white` bubble
  - Bot messages: left-aligned, `bg-background` bubble with border
  - Timestamps below each message (small, muted)
- Input at bottom:
  - Textarea + "Send" button
  - Placeholder: "Ask about this case..."

**Empty state:** "Start a conversation about this case. I have access to the X-ray findings, clinical data, and diagnosis."

---

### 3.12 Report Preview — `/cases/<id>/report`

**Access:** CLINICIAN, ADMIN
**Purpose:** Preview generated report before export

**Layout:**
- Page header: "Report for Case #<id>" + "Export PDF" / "Export CSV" buttons
- Report content (styled as a printable document):
  - Patient info block
  - Diagnosis summary
  - Simplified text section
  - Medication instructions section
  - Generated date + clinician name
- If not yet generated: "Generate Report" CTA card instead

---

### 3.13 Cases List — `/cases`

**Access:** CLINICIAN (own cases), ADMIN (all cases)
**Purpose:** Browse all cases

**Layout:**
- Page header: "All Cases" + "New Case" primary button
- Filters row: search, risk class, status, date range
- Table:
  - Columns: Case ID, Patient, Risk Class, Severity Score, Status, Clinician (admin only), Created, Actions (View)
  - Pagination

---

### 3.14 Admin — Clinicians List — `/admin/clinicians`

**Access:** ADMIN only
**Purpose:** Manage clinician accounts

**Layout:**
- Page header: "Clinicians" + "Add Clinician" primary button
- Table: Name, Email, Created, Status, Actions (deactivate)

---

### 3.15 Admin — Add Clinician — `/admin/clinicians/new`

**Access:** ADMIN only
**Purpose:** Create clinician account (matches Sequence Diagram 1)

**Layout:**
- Form card:
  - Full Name
  - Email
- "Create Account" primary button
- On success: toast "Account created. Temporary credentials sent to <email>."

---

### 3.16 Admin — System Overview — `/admin/overview`

**Access:** ADMIN only
**Purpose:** System-wide stats

**Layout:**
- Stats cards: Total Clinicians, Total Patients, Total Cases, Cases Today
- Chart: Cases per day (last 30 days)
- Table: Recent system activity

---

### 3.17 Settings — `/settings`

**Access:** All users
**Purpose:** Change own password, view profile

**Layout:**
- Profile card (read-only info)
- Change Password card (form)

---

## 4. Reusable Components

### 4.1 Severity Badge

Small pill badge with risk class. Color based on class (see 1.2).
```
[ Class III ]   — amber background, white text
```

### 4.2 Status Badge

- `PENDING` — gray pill, "Pending"
- `DONE` — green pill, "Complete"

### 4.3 Confidence Meter

Horizontal bar + percentage. Color:
- <60% red, 60–80% amber, >80% green

### 4.4 Stat Card

- Icon (top left)
- Label (small, muted, uppercase)
- Value (large, bold)
- Optional trend indicator (arrow + %)

### 4.5 Step Indicator

Horizontal 3-step progress. Active step highlighted primary color.

### 4.6 Empty State

- Centered icon
- Heading
- Description
- Primary action button

### 4.7 Loading States

- Full page: centered spinner
- Card-level: skeleton placeholder
- Inline (buttons): spinner replaces text

---

## 5. Responsive Behavior

- **Desktop (≥1024px):** Full sidebar, multi-column layouts
- **Tablet (768–1023px):** Collapsible sidebar (hamburger), single-column content
- **Mobile (<768px):** Hamburger sidebar, stacked cards

Minimum viable: focus desktop first. Mobile is a nice-to-have.

---

## 6. Implementation notes for Claude Code

- Use Tailwind CSS via CDN — no build step
- Use Django template inheritance: `base.html` contains sidebar + header, other pages extend it
- Use Django's `{% block content %}` pattern
- Include Inter font via Google Fonts CDN in base.html
- For icons, use Lucide icons via CDN (`lucide-static` or inline SVG)
- All forms use Django's built-in form rendering + Tailwind classes via `django-widget-tweaks` or manual classes
- Chat messages should use HTMX for smooth appending without full page reload (optional enhancement)
