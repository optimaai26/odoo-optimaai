# -*- coding: utf-8 -*-
"""
KPI Model
=========
Key Performance Indicators tracking.
Equivalent to Next.js KPI components.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class KPI(models.Model):
    """KPI model for tracking performance metrics."""
    
    _name = 'optimaai.kpi'
    _description = 'Key Performance Indicator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Code',
        help='Unique identifier code'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    # Category
    category = fields.Selection([
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('customer', 'Customer'),
        ('growth', 'Growth'),
        ('quality', 'Quality'),
        ('custom', 'Custom'),
    ], string='Category',
        default='operational',
        required=True,
        index=True
    )
    
    # Measurement
    unit = fields.Selection([
        ('number', 'Number'),
        ('percentage', 'Percentage'),
        ('currency', 'Currency'),
        ('days', 'Days'),
        ('hours', 'Hours'),
        ('ratio', 'Ratio'),
    ], string='Unit',
        default='number'
    )
    
    # Values
    target_value = fields.Float(
        string='Target Value',
        required=True,
        tracking=True
    )
    
    current_value = fields.Float(
        string='Current Value',
        compute='_compute_current_value',
        store=True
    )
    
    previous_value = fields.Float(
        string='Previous Value',
        readonly=True
    )
    
    baseline_value = fields.Float(
        string='Baseline Value',
        default=0
    )
    
    # Thresholds
    warning_threshold = fields.Float(
        string='Warning Threshold',
        default=80,
        help='Percentage of target to trigger warning'
    )
    
    critical_threshold = fields.Float(
        string='Critical Threshold',
        default=50,
        help='Percentage of target to trigger critical alert'
    )
    
    # Computed status
    status = fields.Selection([
        ('on_track', 'On Track'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('exceeded', 'Exceeded'),
    ], string='Status',
        compute='_compute_status',
        store=True
    )
    
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        store=True
    )
    
    trend = fields.Selection([
        ('up', 'Improving'),
        ('down', 'Declining'),
        ('stable', 'Stable'),
    ], string='Trend',
        compute='_compute_trend',
        store=True
    )
    
    # Data source
    data_source_type = fields.Selection([
        ('manual', 'Manual Entry'),
        ('computed', 'Computed'),
        ('api', 'API'),
        ('dataset', 'Dataset'),
    ], string='Data Source',
        default='manual'
    )
    
    computation_formula = fields.Text(
        string='Computation Formula',
        help='Python expression for computed KPIs'
    )
    
    dataset_id = fields.Many2one(
        comodel_name='optimaai.dataset',
        string='Dataset Source'
    )
    
    insight_id = fields.Many2one(
        comodel_name='optimaai.insight',
        string='Related Insight'
    )
    
    # History
    history_ids = fields.One2many(
        comodel_name='optimaai.kpi.history',
        inverse_name='kpi_id',
        string='History'
    )
    
    # Display
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    color = fields.Char(
        string='Color',
        default='#4A90D9'
    )
    
    icon = fields.Char(
        string='Icon',
        default='fa-chart-line'
    )
    
    show_on_dashboard = fields.Boolean(
        string='Show on Dashboard',
        default=True
    )
    
    # Frequency
    measurement_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string='Measurement Frequency',
        default='monthly'
    )
    
    last_measurement_date = fields.Datetime(
        string='Last Measurement',
        readonly=True
    )
    
    next_measurement_date = fields.Datetime(
        string='Next Measurement',
        compute='_compute_next_measurement',
        store=True
    )
    
    # Owner
    owner_id = fields.Many2one(
        comodel_name='res.users',
        string='Owner',
        tracking=True
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # ==========================================
    # Constraints
    # ==========================================
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code, company_id)', 'KPI code must be unique per company.'),
    ]
    
    # ==========================================
    # Computed Methods
    # ==========================================
    
    @api.depends('current_value', 'target_value', 'warning_threshold', 'critical_threshold')
    def _compute_status(self):
        for record in self:
            if record.target_value == 0:
                record.status = 'on_track'
                continue
            
            percentage = (record.current_value / record.target_value) * 100
            
            if percentage >= 100:
                record.status = 'exceeded'
            elif percentage >= record.warning_threshold:
                record.status = 'on_track'
            elif percentage >= record.critical_threshold:
                record.status = 'warning'
            else:
                record.status = 'critical'
    
    @api.depends('current_value', 'target_value')
    def _compute_progress(self):
        for record in self:
            if record.target_value == 0:
                record.progress_percentage = 0
            else:
                record.progress_percentage = min(100, (record.current_value / record.target_value) * 100)
    
    @api.depends('current_value', 'previous_value')
    def _compute_trend(self):
        for record in self:
            if record.previous_value == 0:
                record.trend = 'stable'
            elif record.current_value > record.previous_value * 1.05:
                record.trend = 'up'
            elif record.current_value < record.previous_value * 0.95:
                record.trend = 'down'
            else:
                record.trend = 'stable'
    
    @api.depends('data_source_type', 'computation_formula', 'dataset_id')
    def _compute_current_value(self):
        for record in self:
            if record.data_source_type == 'computed' and record.computation_formula:
                try:
                    record.current_value = record._evaluate_formula()
                except Exception:
                    record.current_value = 0
            else:
                # Keep manual value or compute from dataset
                if record.data_source_type == 'dataset' and record.dataset_id:
                    record.current_value = record._compute_from_dataset()
    
    @api.depends('measurement_frequency', 'last_measurement_date')
    def _compute_next_measurement(self):
        from datetime import timedelta
        
        for record in self:
            if not record.last_measurement_date:
                record.next_measurement_date = fields.Datetime.now()
                continue
            
            last = record.last_measurement_date
            
            if record.measurement_frequency == 'daily':
                record.next_measurement_date = last + timedelta(days=1)
            elif record.measurement_frequency == 'weekly':
                record.next_measurement_date = last + timedelta(weeks=1)
            elif record.measurement_frequency == 'monthly':
                record.next_measurement_date = last + timedelta(days=30)
            elif record.measurement_frequency == 'quarterly':
                record.next_measurement_date = last + timedelta(days=90)
            else:
                record.next_measurement_date = last + timedelta(days=365)
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_update_value(self, new_value):
        """Update KPI value manually."""
        self.ensure_one()
        
        # Store previous value
        self.previous_value = self.current_value
        
        # Create history entry
        self.env['optimaai.kpi.history'].create({
            'kpi_id': self.id,
            'value': new_value,
            'previous_value': self.current_value,
            'measurement_date': fields.Datetime.now(),
            'measured_by': self.env.user.id,
        })
        
        # Update current value
        self.current_value = new_value
        self.last_measurement_date = fields.Datetime.now()
        
        # Check for alerts
        self._check_threshold_alerts()
        
        return True
    
    def _evaluate_formula(self):
        """Evaluate computation formula."""
        self.ensure_one()
        
        if not self.computation_formula:
            return 0
        
        # Create safe evaluation context
        context = {
            'dataset_count': self.env['optimaai.dataset'].search_count([]),
            'prediction_count': self.env['optimaai.prediction'].search_count([]),
            'insight_count': self.env['optimaai.insight'].search_count([]),
        }
        
        try:
            return eval(self.computation_formula, {"__builtins__": {}}, context)
        except Exception as e:
            _logger.error('Failed to evaluate KPI formula: %s', str(e))
            return 0
    
    def _compute_from_dataset(self):
        """Compute KPI from dataset."""
        self.ensure_one()
        
        if not self.dataset_id:
            return 0
        
        # Return row count as default metric
        return self.dataset_id.row_count
    
    def _check_threshold_alerts(self):
        """Check if thresholds are crossed and send alerts."""
        self.ensure_one()
        
        if self.status == 'critical':
            self._send_alert('critical')
        elif self.status == 'warning':
            self._send_alert('warning')
    
    def _send_alert(self, level):
        """Send threshold alert notification."""
        if self.owner_id:
            self.env['optimaai.notification.service'].send_notification(
                user_id=self.owner_id.id,
                title=_('KPI Alert: %s') % self.name,
                message=_('KPI "%s" has reached %s level. Current value: %.2f') % (
                    self.name, level, self.current_value
                ),
            )
    
    def get_dashboard_data(self):
        """Get KPI data for dashboard display."""
        self.ensure_one()
        
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'progress_percentage': self.progress_percentage,
            'status': self.status,
            'trend': self.trend,
            'unit': self.unit,
            'color': self.color,
            'icon': self.icon,
        }
    
    # ==========================================
    # Cron Jobs
    # ==========================================
    
    @api.model
    def _cron_update_computed_kpis(self):
        """Update all computed KPIs."""
        kpis = self.search([
            ('data_source_type', '=', 'computed'),
            ('active', '=', True),
        ])
        
        for kpi in kpis:
            try:
                kpi._compute_current_value()
            except Exception as e:
                _logger.error('Failed to update KPI %s: %s', kpi.name, str(e))


class KPIHistory(models.Model):
    """KPI measurement history."""
    
    _name = 'optimaai.kpi.history'
    _description = 'KPI History'
    _order = 'measurement_date desc'
    
    kpi_id = fields.Many2one(
        comodel_name='optimaai.kpi',
        string='KPI',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    value = fields.Float(
        string='Value',
        required=True
    )
    
    previous_value = fields.Float(
        string='Previous Value'
    )
    
    measurement_date = fields.Datetime(
        string='Measurement Date',
        required=True,
        default=fields.Datetime.now
    )
    
    measured_by = fields.Many2one(
        comodel_name='res.users',
        string='Measured By'
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    company_id = fields.Many2one(
        related='kpi_id.company_id',
        store=True,
        readonly=True
    )