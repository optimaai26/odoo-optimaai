# OptimaAI - Business Intelligence Platform for Odoo

OptimaAI is a comprehensive, state-of-the-art Business Intelligence and Predictive Analytics module for Odoo 19. It transforms raw data into actionable insights using AI-powered analysis, automated KPIs, and an interactive data workflow canvas.

## 🚀 Features

*   **Dataset Management:** Upload, parse, and analyze datasets securely.
*   **Predictive Analytics:** Run AI predictions (classification, regression, clustering) on your datasets.
*   **Automated Insights:** Generate and track anomalies, trends, and patterns with priority levels.
*   **KPI Tracking:** Real-time metrics dashboard with trend indicators.
*   **Visual Canvas:** Build workflows and custom dashboards using drag-and-drop blocks.
*   **Public Dashboard:** A public-facing QWeb website layout for stakeholders.
*   **Modern Frontend:** Built with Odoo's OWL (Odoo Web Library) framework.
*   **Full REST API:** Secure endpoints for external integrations.

---

## 🏗️ Architecture

OptimaAI is structured as a standard Odoo module but leverages both backend and frontend (website) capabilities.

### 1. Models (`/models`)
Core business logic and database tables using Odoo ORM.
*   `dataset.py`, `prediction.py`, `insight.py`, `kpi.py` — Core entities.
*   `canvas.py`, `canvas_block.py` — Workflow management.
*   `security_mixin.py` — Custom row-level access control.

### 2. Controllers (`/controllers`)
Routing and API endpoints.
*   `main.py` — Backend dashboard AJAX endpoints.
*   `api.py` — Secure REST API (`/api/v1/...`) protected by API keys.
*   `website.py` — Routes serving QWeb public pages (`website=True`).
*   `webhook.py` — Ingestion endpoints for external data sources.

### 3. Views (`/views` & `/data/pages`)
XML definitions for the UI.
*   `/views` — Backend Odoo views (Tree, Form, Kanban, Search) and Menus.
*   `/data/pages/dashboard.xml` — Public-facing website QWeb page.

### 4. Static Assets (`/static`)
Frontend logic and styling.
*   **JavaScript:** Uses **OWL Framework** ES modules (`src/js/optimaai.js`). Legacy `odoo.define` is strictly prohibited.
*   **SCSS:** Structured modular styling (`src/scss/optimaai.scss`). Includes website theme overrides (`primary_variables.scss`, `bootstrap_overridden.scss`).
*   **XML Templates:** OWL component templates (`src/xml/optimaai_templates.xml`).

---

## 🔌 REST API Integration

OptimaAI exposes a secured REST API for system integration.

**Authentication:** 
Passed via the `X-API-Key` HTTP header. Manage keys in the Odoo backend under *Configuration > Integrations*.

**Key Endpoints:**
*   `GET /api/v1/datasets`
*   `POST /api/v1/predictions/queue`
*   `GET /api/v1/insights/active`
*   `GET /api/v1/kpis`

---

## 🛠️ Installation & Setup

1. Add the `optimaai` directory to your Odoo `addons-path`.
2. Ensure external Python dependencies are installed:
   ```bash
   pip install requests pandas openpyxl
   ```
3. Update the App List in Odoo and install **OptimaAI**.
4. (Optional) Install demo data by starting Odoo with `-d <your_db> -i optimaai` on an environment with demo data enabled.

---

## 🛡️ Security & Access Control

Access is strictly managed via Odoo Groups (`security.xml`):
*   **OptimaAI User:** Can read and interact with data.
*   **OptimaAI Manager:** Can configure integrations, manage API keys, and approve access requests.
*   **Row-level Security:** Handled by `ir.model.access.csv` and the `optimaai.security.mixin`.
