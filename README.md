# PPT Dashboard Builder

## Project Overview
A production-ready full-stack application for generating template-driven PowerPoint presentations from Excel datasets. It features a strict validation engine, a React-based control panel, and QA tools for ensuring export integrity.

## Repo Structure
- **/backend**: Python/FastAPI application. Handles business logic, validation, and PPTX generation.
- **/frontend**: React + Vite application. Provides the user interface for uploading and managing projects.
- **/docs**: Technical specifications, layout contracts, and design documents.

## Environment Variables

| Variable | Required | Description |
| :--- | :--- | :--- |
| **`PPT_TEMPLATE_PATH`** | **YES** | Absolute path to the master `.pptx` template. **Export fails if missing.** |
| `EXPORT_DEBUG` | No | Set to `true` to force debug overlays (bounding boxes) on all generated slides. |
| `DISABLE_DOCS` | No | Set to `true` in production to disable Swagger UI (`/docs`). |
| `VITE_API_URL` | No | (Frontend) Base URL for the backend API. Defaults to `http://localhost:8000`. |

## Running Locally

### Backend
Requirements: Python 3.10+

```bash
cd backend
# Create/Activate venv
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```
Server running at `http://localhost:8000`.

### Frontend
Requirements: Node.js 18+

```bash
cd frontend
npm install
npm run dev
```
UI running at `http://localhost:5173`.

## Production Build

### Frontend
Compile the React app to static files:
```bash
cd frontend
npm run build
```
Output located in `frontend/dist/`. Serve these files with Nginx or a static host.

### Backend
Run with a production server (e.g., Gunicorn or Uvicorn workers):
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## QA / Debug Mode
Development and QA teams can verify layout alignment and data mapping using Debug Mode.

- **Environment Flag**: Set `EXPORT_DEBUG=true` in the backend environment to force it always on.
- **On-Demand (Header)**: In the Frontend Export panel, toggle "Enable QA Mode". This sends the `X-EXPORT-DEBUG: true` header.
- **Visuals**:
    - **Blue Boxes**: Layout boundaries for charts.
    - **Yellow Notes**: Dataset name, Chart Family, and Min/Max values.

## Export Flow
1. **Upload**: User drags & drops an Excel file (`.xlsx`).
2. **Inspect**: Backend parses sheets; Frontend displays row counts and detected types.
3. **Validate**: System checks for empty data and schema compliance (e.g., missing `%` columns). Blocking errors prevent export.
4. **Export**: User clicks "Generate PowerPoint". Backend builds the PPTX and stamps it with a version/date footer.

## Common Errors

| Error Message | Cause | Resolution |
| :--- | :--- | :--- |
| `Configuration Error: PPT_TEMPLATE_PATH` | Server environment missing mandatory variable. | Set `PPT_TEMPLATE_PATH` to local `.pptx` file. |
| `Dataset ... has empty preview data` | Excel sheet contains no usable rows. | Populate the Excel sheet with data. |
| `... requires a percentage column` | Chart type (e.g., LO) needs `%` column but none found. | Ensure one column header contains "%" or "percent". |
