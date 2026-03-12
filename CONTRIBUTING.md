# Contributing to OptimaAI

Welcome to the OptimaAI development team! This guide covers everything you need to start contributing.

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose** — for running the Odoo + PostgreSQL stack
- **Git** — for version control
- A text editor (VS Code recommended)

### 1. Clone & Setup

```bash
# Clone the Odoo project (contains docker-compose.yml + the optimaai module)
git clone <repo-url> odoo
cd odoo
```

### 2. Start the Environment

```bash
# Start Odoo + PostgreSQL containers
docker compose up -d

# Check logs
docker logs -f odoo-web
```

Odoo will be available at `http://localhost:8069`.

### 3. Install/Upgrade the Module

1. Navigate to **Apps** in Odoo
2. Click **Update Apps List**
3. Search for **OptimaAI** and click **Install** (or **Upgrade** if already installed)

Alternatively, restart with upgrade:
```bash
docker restart odoo-web
```

### 4. Development Mode

For live-reloading of XML/JS/CSS changes, ensure Odoo runs with `--dev=all`:
```
# In config/odoo.conf, set:
dev_mode = all
```

Then restart:
```bash
docker restart odoo-web
```

> [!TIP]
> Python model changes always require a full restart + module upgrade. JavaScript and SCSS changes only need a browser hard refresh (Ctrl+Shift+R) with `dev_mode = all`.

---

## 📚 Tech Stack & Documentation

OptimaAI is built on modern enterprise tools. If you are new to the stack, bookmark these official resources:

| Technology | Purpose | Documentation Link |
|---|---|---|
| **Odoo 19 / Python** | Backend ORM, API, XML Views | [Odoo 19 Developer Docs](https://www.odoo.com/documentation/19.0/developer.html) |
| **OWL (JS)** | Frontend UI Components | [Odoo Web Library (OWL) Docs](https://github.com/odoo/owl) |
| **PostgreSQL 17** | Database | [PostgreSQL 17 Docs](https://www.postgresql.org/docs/17/index.html) |
| **Chart.js 4.4** | Dashboard Visualizations | [Chart.js Documentation](https://www.chartjs.org/docs/4.4.4/) |
| **Bootstrap 5** | Underlying SCSS Grid / Mixins | [Bootstrap 5 Docs](https://getbootstrap.com/docs/5.0/getting-started/introduction/) |
| **Docker Compose** | Local Environment | [Docker Compose Docs](https://docs.docker.com/compose/) |

---

## 📁 Project Structure

Before contributing, understand where things live:

```
optimaai/
├── models/                  ← Python data models (ORM)
├── controllers/             ← API & RPC endpoints
│   ├── main.py              ← Dashboard + internal JSON-RPC + REST API
│   └── website.py           ← Public website controller
├── views/                   ← Odoo XML views (form, tree, kanban, menus)
├── security/                ← Groups + ACL rules
├── static/src/
│   ├── js/optimaai.js       ← OWL frontend components
│   ├── xml/optimaai_templates.xml  ← QWeb templates
│   └── scss/                ← Styles
├── data/                    ← Default data, sequences
├── demo/                    ← Demo data
├── services/                ← Python service layer
├── wizard/                  ← Transient models
├── tests/                   ← Unit tests
├── __manifest__.py          ← Module manifest
├── ARCHITECTURE.md          ← Architecture reference
└── BACKEND_REQUIREMENTS.md  ← API contracts
```

> [!IMPORTANT]
> Read **ARCHITECTURE.md** before making structural changes. It documents all models, controllers, and component relationships.

---

## 📐 Coding Standards

### JavaScript (OWL Framework)

OptimaAI targets **Odoo 19** and uses the **OWL framework** exclusively.

| Rule | Details |
|---|---|
| 🚫 No legacy code | Never use `odoo.define()` or `require()` |
| ✅ ES Modules | `import { Component } from "@odoo/owl"` |
| ✅ Module header | Every JS file starts with `/** @odoo-module **/` |
| ✅ Registries | Register via `registry.category("actions").add(...)` |
| ✅ RPC | Use `rpc` from `@web/core/network/rpc` |

**Example component:**
```javascript
/** @odoo-module **/
import { Component, useState, onWillStart, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class MyWidget extends Component {
    static template = "optimaai.MyWidget";
    setup() {
        this.state = useState({ data: [] });
        onWillStart(async () => {
            this.state.data = await rpc("/optimaai/my-endpoint", {});
        });
    }
}

registry.category("actions").add("optimaai_my_widget", MyWidget);
```

### SCSS

| Rule | Details |
|---|---|
| 🚫 No plain CSS | Always use `.scss` files |
| ✅ Odoo variables | Use `var(--o-color-1)` or vars from `primary_variables.scss` |
| ✅ Dark mode | Use `.o_dark_mode` selector (not `prefers-color-scheme`) |
| ✅ Prefix classes | All custom classes start with `o_` (Odoo convention) |

### Python (Models & Controllers)

| Rule | Details |
|---|---|
| ✅ PEP 8 | Follow standard Python style |
| ✅ ORM first | Use `self.env['model'].search()`, avoid raw SQL |
| ✅ Logging | `import logging; _logger = logging.getLogger(__name__)` |
| ✅ Domains | Standard format: `[('field', '=', value)]` |
| 🚫 No sudo() abuse | Use `request.env` to enforce ACLs |

---

## 🧪 Testing

### Running Tests

```bash
# Run inside the Odoo container
docker exec odoo-web odoo -c /etc/odoo/odoo.conf -i optimaai --test-enable -d <test_db> --stop-after-init
```

### Writing Tests

```python
from odoo.tests import tagged, TransactionCase

@tagged('post_install', '-at_install')
class TestKPI(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Kpi = self.env['optimaai.kpi']
    
    def test_kpi_progress_calculation(self):
        kpi = self.Kpi.create({
            'name': 'Test KPI',
            'current_value': 75,
            'target_value': 100,
        })
        self.assertEqual(kpi.progress_percentage, 75.0)
```

Place tests in `tests/` and import them in `tests/__init__.py`.

---

## 🔄 Git Workflow

### Branch Naming

```
feature/add-chart-recommendations
fix/kpi-progress-calculation
refactor/clean-up-scss
docs/update-architecture
```

### Commit Messages

```
[MODELS] Add prediction_type field to prediction model
[JS] Integrate Chart.js dynamic loading for dashboard
[SCSS] Redesign KPI metric strip with colored cards
[API] Add pagination to dataset list endpoint
[FIX] Correct read_group compatibility for Odoo 19
[DOCS] Update ARCHITECTURE.md with new model catalog
```

### PR Checklist

- [ ] Code follows the coding standards above
- [ ] No SCSS/JS errors in browser console
- [ ] Python unit tests pass
- [ ] `ARCHITECTURE.md` updated if models/controllers/views changed
- [ ] `BACKEND_REQUIREMENTS.md` updated if API contracts changed

---

## ⚠️ Common Pitfalls

| Pitfall | How to Avoid |
|---|---|
| `menu_views.xml` must be loaded last | Never add new view files after `menu_views.xml` in `__manifest__.py` |
| `read_group` changed in Odoo 19 | Use `{field}_count` instead of `__count` |
| Chart.js loads from CDN | Ensure internet access in production; fallback to empty charts if offline |
| SCSS variables don't cascade | Import order in manifest matters — primary_variables → bootstrap overrides → main SCSS |

---

## 🗺️ Where to Find Things

| "I need to..." | Look at... |
|---|---|
| Add a new data model | `models/` → create file + add to `models/__init__.py` + add ACLs |
| Add a new API endpoint | `controllers/main.py` → `OptimaAIRPCController` class |
| Add a new OWL component | `static/src/js/optimaai.js` + `static/src/xml/optimaai_templates.xml` |
| Change dashboard layout | `static/src/xml/optimaai_templates.xml` → `optimaai.Dashboard` template |
| Change dashboard styles | `static/src/scss/optimaai.scss` |
| Add a menu item | `views/menu_views.xml` (always at the end of manifest data list) |
| Change security groups | `security/security.xml` + `security/ir.model.access.csv` |

---

Thank you for contributing to OptimaAI! 🚀
