# OptimaAI - Backend Requirements & API Specification

This document details exactly what the frontend (OWL components and public website) requires from the Odoo backend models and controllers to function correctly. 

If you are developing or modifying the backend of OptimaAI, you must ensure these data contracts and endpoints are maintained.

---

## 1. Internal AJAX API Requirements
These endpoints are used by the OWL JavaScript components within the Odoo backend interface. They use Odoo's JSON-RPC system.

### 1.1 Dashboard Data
*   **Route:** `/optimaai/dashboard/data`
*   **Used By:** `OptimaAIDashboard` (OWL Component)
*   **Expected Response (JSON):**
    ```json
    {
      "datasets": { "total": 12, "by_status": {"active": 10, "archived": 2} },
      "predictions": { "total": 5, "by_status": {"completed": 4, "pending": 1} },
      "insights": { "total": 8, "by_priority": {"high": 2, "medium": 6} },
      "kpis": { "total": 4, "by_status": {"active": 4} },
      "recentKpis": [...],
      "activeInsights": [...]
    }
    ```

### 1.2 Notifications
*   **Routes:** 
    *   `/optimaai/notifications/count` (Returns: `{ "count": integer }`)
    *   `/optimaai/notifications/list` (Requires: `{ "limit": integer }`, Returns array of notification objects)
    *   `/optimaai/notifications/mark_read` (Requires: `{ "id": integer }`)
    *   `/optimaai/notifications/mark_all_read`
*   **Required Notification Object Fields:**
    `id`, `name`, `message`, `notification_type` ('info', 'success', 'warning', 'error'), `is_read` (boolean), `create_date`, `res_model` (optional), `res_id` (optional).

### 1.3 Canvas & Datasets
*   **Canvas Load:** `/optimaai/canvas/load`
    *   Requires: `{ "canvas_id": integer }`
    *   Returns: `{ "blocks": [ {"id": int, "name": str, "block_type": "kpi"|"chart"|"insights"|"table", "width": int, "height": int, ...} ] }`
*   **Dataset Preview:** `/optimaai/dataset/preview`
    *   Requires: `{ "dataset_id": integer, "limit": integer }`
    *   Returns: `{ "columns": ["col1", "col2"], "data": [ {"col1": "val", "col2": "val"} ] }`

---

## 2. Public Website Requirements (QWeb)

The public-facing dashboard (`/optimaai/public-dashboard`) relies on the backend models passing specific context dictionary variables to the QWeb template (`data/pages/dashboard.xml`).

### Required Context Variables:
The `OptimaAIWebsiteController` must pass these variables to `request.render('optimaai.page_public_dashboard', values)`:

*   `dataset_count` (Integer)
*   `prediction_count` (Integer)
*   `insight_count` (Integer)
*   `kpi_count` (Integer)
*   `top_kpis` (Recordset of `optimaai.kpi`)
    *   **Required Fields:** `name`, `value` (float/string), `unit` (string), `trend_direction` ('up', 'down', 'stable'), `trend_percentage` (float).
*   `active_insights` (Recordset of `optimaai.insight`)
    *   **Required Fields:** `name`, `description`, `insight_type` ('pattern', 'anomaly', etc.), `priority` ('low', 'medium', 'high', 'critical').
*   `recent_datasets` (Recordset of `optimaai.dataset`)
    *   **Required Fields:** `name`, `data_source`, `status`, `row_count` (integer), `create_date`.

---

## 3. External REST API Requirements (`/api/v1/*`)

External systems interacting with OptimaAI rely on these RESTful endpoints. All endpoints require the `X-API-Key` header.

### 3.1 Authentication
*   **Header:** `X-API-Key: <valid_api_key>`
*   **Backend Mechanism:** The `@api_key_required` decorator checks the `res.users.api.key` model.

### 3.2 Required Endpoints (CRUD)

| Entity | GET (List) | GET (Single) | POST (Create) | PUT (Update) | DELETE |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Datasets** | `/api/v1/datasets` | `/api/v1/datasets/<id>` | `/api/v1/datasets` | `/api/v1/datasets/<id>` | `/api/v1/datasets/<id>` |
| **Predictions** | `/api/v1/predictions`| `/api/v1/predictions/<id>`| `/api/v1/predictions` | (Status only) | `/api/v1/predictions/<id>`|
| **Insights** | `/api/v1/insights` | `/api/v1/insights/<id>` | - (AI Gen only)| `/api/v1/insights/<id>` | `/api/v1/insights/<id>` |
| **KPIs** | `/api/v1/kpis` | `/api/v1/kpis/<id>` | `/api/v1/kpis` | `/api/v1/kpis/<id>` | `/api/v1/kpis/<id>` |

### 3.3 Specific Action Endpoints
*   **Predictions:**
    *   `POST /api/v1/predictions/<id>/queue` (Changes status to queued)
    *   `POST /api/v1/predictions/<id>/process` (Triggers manual processing)
*   **Insights:**
    *   `POST /api/v1/insights/<id>/activate`
    *   `POST /api/v1/insights/<id>/dismiss`

---

## 4. Model Constraints & Assumptions

The frontend assumes the following about the Odoo models:

1.  **State/Status Fields:** Fields like `status` or `state` use strict string selections (e.g., `'draft'`, `'pending'`, `'completed'`, `'error'`). The frontend CSS (SCSS) maps directly to these exact string values (e.g., class `o_status_completed`). If backend selections change, frontend SCSS must be updated.
2.  **Date Formats:** Dates returned by JSON endpoints should be standard ISO 8601 strings or Odoo standard datetime strings format.
3.  **Permissions:** The frontend assumes the current user's security groups (`security.xml`) correctly limit the recordsets returned by RPC calls. The backend controllers MUST use `sudo()` carefully, preferring the user's current environment `request.env` to enforce ACLs.
