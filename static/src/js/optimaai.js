/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

// ==========================================
// Notification Bell — Systray Widget
// ==========================================

export class NotificationBell extends Component {
    static template = "optimaai.NotificationBell";

    setup() {
        this.rpc = rpc;
        this.action = useService("action");
        this.state = useState({
            count: 0,
            panelOpen: false,
            notifications: [],
        });

        onWillStart(async () => {
            await this._updateNotificationCount();
        });

        onMounted(() => {
            // Poll for new notifications every 30 seconds
            this._pollInterval = setInterval(
                () => this._updateNotificationCount(),
                30000
            );
        });
    }

    async _updateNotificationCount() {
        try {
            const result = await this.rpc("/optimaai/notifications/count", {});
            this.state.count = result.count || 0;
        } catch (e) {
            // Silently fail if endpoint doesn't exist yet
            console.debug("OptimaAI: Could not fetch notification count", e);
        }
    }

    get formattedCount() {
        return this.state.count > 99 ? "99+" : String(this.state.count);
    }

    async togglePanel() {
        this.state.panelOpen = !this.state.panelOpen;
        if (this.state.panelOpen) {
            await this._loadNotifications();
        }
    }

    async _loadNotifications() {
        try {
            const result = await this.rpc("/optimaai/notifications/list", {
                limit: 20,
            });
            this.state.notifications = result.notifications || [];
        } catch (e) {
            console.debug("OptimaAI: Could not load notifications", e);
        }
    }

    getTypeIcon(type) {
        const icons = {
            info: "fa-info-circle",
            success: "fa-check-circle",
            warning: "fa-exclamation-triangle",
            error: "fa-times-circle",
        };
        return icons[type] || "fa-bell";
    }

    async onNotificationClick(notification) {
        // Mark as read
        try {
            await this.rpc("/optimaai/notifications/mark_read", {
                id: notification.id,
            });
            notification.is_read = true;
        } catch (e) {
            // ignore
        }

        // Navigate to related record if available
        if (notification.res_model && notification.res_id) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: notification.res_model,
                res_id: notification.res_id,
                views: [[false, "form"]],
                target: "current",
            });
            this.state.panelOpen = false;
        }
    }

    async markAllRead() {
        try {
            await this.rpc("/optimaai/notifications/mark_all_read", {});
            await this._loadNotifications();
            await this._updateNotificationCount();
        } catch (e) {
            // ignore
        }
    }

    closePanel() {
        this.state.panelOpen = false;
    }

    __destroy() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
        }
    }
}

// Register in systray
registry.category("systray").add("optimaai.NotificationBell", {
    Component: NotificationBell,
}, { sequence: 25 });


// ==========================================
// KPI Card Component
// ==========================================

export class KPICard extends Component {
    static template = "optimaai.KPICard";
    static props = {
        kpi: { type: Object },
        onCardClick: { type: Function, optional: true },
    };

    get trendIcon() {
        if (this.props.kpi.trend_direction === "up") return "fa-arrow-up";
        if (this.props.kpi.trend_direction === "down") return "fa-arrow-down";
        return "fa-minus";
    }

    get trendClass() {
        if (this.props.kpi.trend_direction === "up") return "o_kpi_trend_up";
        if (this.props.kpi.trend_direction === "down") return "o_kpi_trend_down";
        return "o_kpi_trend_stable";
    }

    onClick() {
        if (this.props.onCardClick) {
            this.props.onCardClick(this.props.kpi);
        }
    }
}


// ==========================================
// Dataset Preview Component
// ==========================================

export class DatasetPreview extends Component {
    static template = "optimaai.DatasetPreview";
    static props = {
        datasetId: { type: Number, optional: true },
        data: { type: Array, optional: true },
        columns: { type: Array, optional: true },
        limit: { type: Number, optional: true },
        onRowSelect: { type: Function, optional: true },
    };

    setup() {
        this.rpc = rpc;
        this.state = useState({
            data: this.props.data || [],
            columns: this.props.columns || [],
        });

        onWillStart(async () => {
            if (!this.state.data.length && this.props.datasetId) {
                await this._loadData();
            }
        });
    }

    async _loadData() {
        try {
            const result = await this.rpc("/optimaai/dataset/preview", {
                dataset_id: this.props.datasetId,
                limit: this.props.limit || 10,
            });
            this.state.data = result.data || [];
            this.state.columns = result.columns || [];
        } catch (e) {
            console.debug("OptimaAI: Could not load dataset preview", e);
        }
    }

    onRowClick(row, index) {
        if (this.props.onRowSelect) {
            this.props.onRowSelect({ row, index });
        }
    }
}


// ==========================================
// Prediction Result Component
// ==========================================

export class PredictionResult extends Component {
    static template = "optimaai.PredictionResult";
    static props = {
        confidence: { type: Number, optional: true },
        data: { type: Object, optional: true },
        metrics: { type: Object, optional: true },
    };

    get confidenceClass() {
        const c = this.props.confidence || 0;
        if (c >= 0.8) return "o_confidence_high";
        if (c >= 0.6) return "o_confidence_medium";
        return "o_confidence_low";
    }

    get confidencePercent() {
        return Math.round((this.props.confidence || 0) * 100);
    }
}


// ==========================================
// Insight Card Component
// ==========================================

export class InsightCard extends Component {
    static template = "optimaai.InsightCard";
    static props = {
        insight: { type: Object },
        onActivate: { type: Function, optional: true },
        onDismiss: { type: Function, optional: true },
    };

    setup() {
        this.rpc = rpc;
    }

    get insightClass() {
        return "o_insight_" + (this.props.insight.insight_type || "info");
    }

    get priorityClass() {
        return "o_priority_" + (this.props.insight.priority || "medium");
    }

    async onDismiss(ev) {
        ev.stopPropagation();
        try {
            await this.rpc("/optimaai/insight/dismiss", {
                id: this.props.insight.id,
            });
            if (this.props.onDismiss) {
                this.props.onDismiss(this.props.insight.id);
            }
        } catch (e) {
            // ignore
        }
    }

    onActivate(ev) {
        ev.stopPropagation();
        if (this.props.onActivate) {
            this.props.onActivate(this.props.insight.id);
        }
    }
}


// ==========================================
// Canvas Dashboard Component
// ==========================================

export class CanvasDashboard extends Component {
    static template = "optimaai.CanvasDashboard";
    static props = {
        canvasId: { type: Number, optional: true },
        blocks: { type: Array, optional: true },
        layoutConfig: { type: Object, optional: true },
    };

    setup() {
        this.rpc = rpc;
        this.state = useState({
            blocks: this.props.blocks || [],
        });

        const layoutConfig = this.props.layoutConfig || {
            columns: 3,
            rows: 4,
            gap: 16,
        };
        this.gridStyle = `
            grid-template-columns: repeat(${layoutConfig.columns}, 1fr);
            gap: ${layoutConfig.gap}px;
        `;

        onWillStart(async () => {
            if (this.props.canvasId) {
                await this._loadCanvas();
            }
        });
    }

    async _loadCanvas() {
        try {
            const result = await this.rpc("/optimaai/canvas/load", {
                canvas_id: this.props.canvasId,
            });
            this.state.blocks = result.blocks || [];
        } catch (e) {
            console.debug("OptimaAI: Could not load canvas", e);
        }
    }

    getBlockStyle(block) {
        return `grid-column: span ${block.width || 1}; grid-row: span ${block.height || 1};`;
    }

    getBlockTypeIcon(blockType) {
        const icons = {
            kpi: "fa-tachometer",
            chart: "fa-bar-chart",
            insights: "fa-lightbulb-o",
            table: "fa-table",
        };
        return icons[blockType] || "fa-cube";
    }

    async removeBlock(blockId) {
        try {
            await this.rpc("/optimaai/canvas/remove_block", {
                block_id: blockId,
            });
            this.state.blocks = this.state.blocks.filter(
                (b) => b.id !== blockId
            );
        } catch (e) {
            // ignore
        }
    }
}


// ==========================================
// OptimaAI Dashboard Client Action
// ==========================================

export class OptimaAIDashboard extends Component {
    static template = "optimaai.Dashboard";
    static components = { KPICard, InsightCard };

    setup() {
        this.rpc = rpc;
        this.action = useService("action");
        this.state = useState({
            loading: true,
            datasets: { total: 0, by_status: {} },
            predictions: { total: 0, by_status: {} },
            insights: { total: 0, by_priority: {} },
            kpis: { total: 0, by_status: {} },
            recentKpis: [],
            activeInsights: [],
        });

        onWillStart(async () => {
            await this._loadDashboardData();
        });
    }

    async _loadDashboardData() {
        try {
            const result = await this.rpc("/optimaai/dashboard/data", {});
            Object.assign(this.state, result);
            this.state.loading = false;
        } catch (e) {
            this.state.loading = false;
            console.debug("OptimaAI: Could not load dashboard data", e);
        }
    }

    navigateTo(action) {
        this.action.doAction(action);
    }
}

// Register dashboard as a client action
registry.category("actions").add("optimaai_dashboard", OptimaAIDashboard);