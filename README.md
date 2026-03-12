# OptimaAI — Business Intelligence Platform for Odoo

> AI-powered analytics, predictive insights, and KPI tracking — built natively for Odoo 19.

![Odoo 19](https://img.shields.io/badge/Odoo-19.0-875A7B?style=flat-square)
![License](https://img.shields.io/badge/License-LGPL--3-blue?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Dataset Management** | Upload, parse, and analyze datasets with quality scoring |
| **Predictive Analytics** | Run AI predictions (classification, regression, clustering) |
| **Automated Insights** | Detect anomalies, trends, and patterns with priority levels |
| **KPI Tracking** | Real-time metrics dashboard with trend indicators and targets |
| **Visual Canvas** | Drag-and-drop workflow builder for data pipelines |
| **Interactive Dashboard** | Premium dashboard with Chart.js charts and colored KPIs |
| **Notification System** | Real-time alerts via systray bell widget |
| **REST API** | Secured endpoints for external integrations |
| **Public Dashboard** | Website-facing analytics page for stakeholders |

---

## 🛠️ Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

```bash
# 1. Clone the project
git clone <repo-url> odoo
cd odoo

# 2. Start the stack
docker compose up -d

# 3. Access Odoo
open http://localhost:8069

# 4. Install the module
# Navigate to Apps → Update Apps List → Search "OptimaAI" → Install
```

### Development Mode

```bash
# Enable live reload for JS/SCSS/XML changes:
# In config/odoo.conf, set: dev_mode = all
docker restart odoo-web
```

---

## 📚 Documentation

| Doc | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Complete technical reference — models, controllers, frontend, security |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Setup, coding standards, Git workflow, testing |
| [BACKEND_REQUIREMENTS.md](BACKEND_REQUIREMENTS.md) | API contracts — what the frontend expects from the backend |

---

## 🏗️ Architecture Overview

OptimaAI is a **full-stack Odoo 19 module** — backend (Python) and frontend (OWL/JS) in one package.

```
optimaai/
├── models/          ← 16 Python models (Dataset, Prediction, Insight, KPI, Canvas, ...)
├── controllers/     ← JSON-RPC + REST API endpoints
├── views/           ← Odoo XML views + menus
├── security/        ← Groups + ACLs
├── static/src/      ← OWL components, SCSS, QWeb templates
└── __manifest__.py  ← Module manifest
```

**Data flow:**
```
OWL Component → JSON-RPC → Controller → ORM → PostgreSQL
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full entity diagram, API routes, and frontend component map.

---

## 🔌 REST API

External systems can integrate via the REST API:

```bash
# Example: List all KPIs
curl -H "X-API-Key: <your-key>" http://localhost:8069/api/v1/kpis
```

| Resource | Endpoint |
|---|---|
| Datasets | `/api/v1/datasets` |
| Predictions | `/api/v1/predictions` |
| Insights | `/api/v1/insights` |
| KPIs | `/api/v1/kpis` |

See [BACKEND_REQUIREMENTS.md](BACKEND_REQUIREMENTS.md) for the full API specification.

---

## 🛡️ Security

| Group | Access |
|---|---|
| OptimaAI User | Read + create records |
| OptimaAI Manager | Full CRUD + configuration |

API access is controlled via `X-API-Key` headers mapped to Odoo users.

---

## 📄 License

[LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html)
