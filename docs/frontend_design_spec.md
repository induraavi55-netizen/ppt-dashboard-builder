# Frontend Design Specification: PPT Dashboard Control Panel

## 1. Executive Summary
A lightweight, reliable, and production-ready implementation of a control panel for the PPT Export Engine. 
**Goal:** Empower school admins/analysts to run exports reliably without developer assistance.

## 2. Technology Stack
**Reasoning:** Optimized for reliability, speed of development, and seamless integration with the existing Python/FastAPI backend.

- **Framework:** **React + Vite** (Single Page Application)
    - *Why?* Fast build, simple deployment (static files served by FastAPI or standalone), robust ecosystem.
- **Language:** **TypeScript**
    - *Why?* Catches errors early; types shared with API responses ensure contract safety.
- **Styling:** **TailwindCSS** + **Shadcn/UI** (or generic component library)
    - *Why?* Rapid development of professional-looking internal tools without custom CSS maintenance.
- **State Management:** **React Query (TanStack Query)**
    - *Why?* Handles caching, loading states, and API errors automatically.
- **HTTP Client:** **Axios**
    - *Why?* Standard, easy header management (for QA flags).

## 3. Screen Flow & Wireframes

### 1️⃣ Upload Screen (Home)
**Layout:** Centered Card.
- **Header:** "Dashboard Engine v1.2"
- **Input:** "Project Name" (Text, required).
- **Control:** "Upload Excel File" (File Drag & Drop area).
    - *Validation:* `.xlsx` only, max size 50MB.
- **Action:** "Start Upload" button (Primary).
- **Feedback:** Loading spinner with "Processing data structure..." textual updates.
- **Outcome:** Redirects to Inspector Screen on success.

### 2️⃣ Dataset Inspector Screen
**Layout:** Dashboard.
- **Top Bar:** Project Name | "Back to Upload"
- **Main Area:** Data Table.
    - Columns: Dataset Name | detected_type | Rows | Cols | Status (Green/Yellow/Red)
- **Detail View (Modal/Side-panel):**
    - Click row -> Shows first 5 rows (Preview).
    - Highlights `percent` column if detected.
    - Explicitly states: "Mapped Chart Family: [LO/SUMMARY/etc]".

### 3️⃣ Validation Panel
**Layout:** Sidebar or Bottom Section on Inspector Screen.
- **Header:** "Pre-flight Validations".
- **List:**
    - [x] Preview Data Check
    - [x] Column Requirements (Percent Check)
    - [x] Schema Validity
    - [?] LO Row Count Checks (Warning)
- **Behavior:**
    - Real-time validation against the preview data response.
    - **BLOCKING:** If critical errors exist, "Proceed to Export" button is Disabled.

### 4️⃣ Export Panel
**Layout:** Final Step / Sticky Header.
- **Controls:**
    - **Toggle:** `☐ Enable QA Debug Overlays` (Sends `X-EXPORT-DEBUG: true`).
- **Action:** "Generate PowerPoint" (Primary Button).
- **State:** 
    - *Idle*: Ready.
    - *Processing*: Spinner + "Generating slides..." (Disable inputs).
    - *Success*: "Download Ready" + Auto-download trigger.
    - *Error*: Red alert box with strict backend error message.

## 4. API Integration & Logic

### Headers
- **Global:** `Content-Type: application/json` (except upload).
- **QA Feature:** 
    - If "QA Debug Mode" checked: `X-EXPORT-DEBUG: true`
    - Backend must be updated to read this header in addition to/instead of ENV.

### Endpoints
| Screen | Action | Method | Endpoint | Payload | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Upload** | Upload File | `POST` | `/upload-data` | `Multipart` (file, project_name) | `{ project_id, datasets: [...] }` |
| **Export** | Trigger Export | `POST` | `/export/{project_id}` | JSON `{}` (optional overrides) | Blob (PPTX file) |

## 5. Backend Updates Required
To support the frontend design, the backend needs minor adjustments:
1.  **CORS**: Allow origin for local frontend dev (e.g., `http://localhost:5173`).
2.  **QA Flag**: Middleware or dependency to parse `X-EXPORT-DEBUG` header and set the context for `slide_builder` (overriding `os.environ`).
3.  **Validation Endpoint** (Optional but recommended): Does the backend expose validation results *before* export? 
    - *MVP Strategy:* Frontend validates based on the `datasets` metadata returned from upload (row counts, column names) before calling export. The Backend export will fail hard if invalid.

## 6. Folder Structure (Monorepo-style)
```
/root
  /backend (FastAPI)
  /frontend (React + Vite)
    /src
      /components (UI parts)
      /features (Upload, Inspector)
      /api (Axios client)
      /types (TS interfaces)
  /docs
```

## 7. Security & Environment
- **Env:**
    - `VITE_API_URL`: pointing to backend.
- **Security:**
    - File extension checks (.xlsx).
    - Size limit (client-side 50MB check).
    - Sanitize Project Name strings.

## 8. MVP Timeline
1.  **Phase 1: Setup**: Init Vite project, Tailwind, Axios.
2.  **Phase 2: Upload**: Implement File upload + Project ID state.
3.  **Phase 3: Inspector**: Render dataset table from upload response.
4.  **Phase 4: Export**: Wire up Export button + Download blob handling + QA Toggle.
5.  **Phase 5: Polish**: Error messages, Spinners, Validation feedback.
