# Contributing to OptimaAI

Welcome to the OptimaAI development team! This document outlines the standards, processes, and guidelines for contributing to the OptimaAI Odoo module.

---

## 🚀 Getting Started

1. **Clone the repository** into your Odoo custom addons directory.
2. **Setup your dev environment:**
   Launch Odoo with the `--dev=all` flag to ensure XML, JS, and CSS changes are reloaded without restarting the server:
   ```bash
   ./odoo-bin -c odoo.conf -u optimaai --dev=all
   ```

---

## 📐 Coding Standards

### 1. JavaScript (OWL Framework)

OptimaAI targets **Odoo 19** and strictly uses the modern **OWL framework**. 

*   **🚫 NO Legacy Code:** Never use `odoo.define()` or `require()`.
*   **ES Modules:** Use standard ES6 imports (`import { Component } from "@odoo/owl";`).
*   **Module Declaration:** Every JS file must start with `/** @odoo-module **/`.
*   **Registries:** Register all components, systray items, and actions via `@web/core/registry`.

**Example:**
```javascript
/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MyCustomCard extends Component {
    static template = "optimaai.MyCustomCard";
    setup() {
        this.state = useState({ value: 0 });
    }
}

registry.category("actions").add("optimaai_custom_card", MyCustomCard);
```

### 2. Styling (SCSS)

*   **🚫 NO Plain CSS:** Never write `.css` files. Always use `.scss`.
*   **Variables:** Use Odoo's built-in CSS variables (`var(--o-color-1)`) for theme consistency, or the variables defined in `src/scss/primary_variables.scss`.
*   **Dark Mode:** Use the `.o_dark_mode` class selector to target dark mode themes. Do not use `@media (prefers-color-scheme)`.
*   **File Structure:** Keep files modular. If adding generic styles, add them to `optimaai.scss`. If overriding Bootstrap, use `bootstrap_overridden.scss`.

### 3. Python (Odoo Models & Controllers)

*   **PEP 8:** Follow standard Python PEP 8 style guidelines.
*   **Odoo Guidelines:** 
    *   Use `[('field', '=', value)]` standard domain structures.
    *   Avoid using raw SQL queries unless absolutely necessary for performance. Always prefer the ORM (`self.env['...'].search()`).
    *   Log errors properly using `import logging; _logger = logging.getLogger(__name__)`.

---

## 🧪 Testing

All new features and bug fixes must include tests.

1. **Location:** Place tests in the `tests/` directory.
2. **Framework:** Use Odoo's `TransactionCase` (`from odoo.tests import common, tagged`).
3. **Tags:** Always tag tests with `@tagged('post_install', '-at_install')`.
4. **Running tests:**
   ```bash
   ./odoo-bin -c odoo.conf -i optimaai --test-enable -d <test_db>
   ```

---

## 🔄 Pull Request Process

1. **Create a branch:** `feature/your-feature-name` or `fix/issue-description`.
2. **Update Documentation:** If your change modifies the API or architecture, update `README.md`.
3. **Commit Messages:** Write clear, concise commit messages. Prefix with the area (e.g., `[JS] Migrate notification bell to OWL`, `[API] Add pagination to datasets`).
4. **Review:** Request a review from a core maintainer. Ensure your code passes all Python unit tests and compiles without SCSS/JS errors in the browser console.

Thank you for contributing to OptimaAI!
