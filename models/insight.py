# -*- coding: utf-8 -*-
"""
Insight Model
=============
AI-generated insights from predictions.
Equivalent to Next.js insights page.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Insight(models.Model):
    """AI-generated insight model."""
    
    _name = 'optimaai.insight'
    _description = 'Insight'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, priority desc'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Title',
        required=True,
        tracking=True
    )
    
    # Relations
    dataset_id = fields.Many2one(
        comodel_name='optimaai.dataset',
        string='Dataset',
        ondelete='restrict',
        tracking=True
    )
    prediction_id = fields.Many2one(
        comodel_name='optimaai.prediction',
        string='Prediction',
        ondelete='restrict',
        tracking=True
    )
    
    # Content
    insight_type = fields.Selection([
        ('anomaly', 'Anomaly Detected'),
        ('opportunity', 'Opportunity'),
        ('risk', 'Risk Factor'),
        ('recommendation', 'Recommendation'),
        ('pattern', 'Pattern Discovered'),
        ('trend', 'Trend Analysis'),
    ], string='Type',
        default='recommendation',
        required=True,
        index=True
    )
    
    summary = fields.Text(
        string='Summary',
        required=True
    )
    
    detailed_analysis = fields.Text(
        string='Detailed Analysis'
    )
    
    # Impact scoring
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Priority',
        default='medium',
        index=True
    )
    
    impact_score = fields.Integer(
        string='Impact Score',
        default=50,
        help='Impact score from 0-100'
    )
    
    confidence_level = fields.Integer(
        string='Confidence Level',
        default=50,
        help='Confidence level from 0-100'
    )
    
    # Actionable
    is_actionable = fields.Boolean(
        string='Actionable',
        default=False
    )
    
    action_suggestion = fields.Text(
        string='Suggested Action'
    )
    
    action_status = fields.Selection([
        ('pending', 'Pending Review'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ], string='Action Status',
        default='pending',
        tracking=True
    )
    
    action_notes = fields.Text(
        string='Action Notes'
    )
    
    action_assigned_to = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        tracking=True
    )
    
    resolved_date = fields.Datetime(
        string='Resolved Date',
        readonly=True
    )
    
    resolved_by = fields.Many2one(
        comodel_name='res.users',
        string='Resolved By',
        readonly=True
    )
    
    # Supporting data
    supporting_data = fields.Text(
        string='Supporting Data',
        widget='json'
    )
    
    chart_config = fields.Text(
        string='Chart Configuration',
        widget='json'
    )
    
    # Metadata
    tags = fields.Char(
        string='Tags',
        help='Comma-separated tags'
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
    # Business Methods
    # ==========================================
    
    def action_acknowledge(self):
        """Acknowledge the insight."""
        self.ensure_one()
        self.action_status = 'acknowledged'
        return True
    
    def action_start(self):
        """Mark as in progress."""
        self.ensure_one()
        self.action_status = 'in_progress'
        return True
    
    def action_resolve(self):
        """Resolve the insight."""
        self.ensure_one()
        self.action_status = 'resolved'
        self.resolved_date = fields.Datetime.now()
        self.resolved_by = self.env.user
        return True
    
    def action_dismiss(self):
        """Dismiss the insight."""
        self.ensure_one()
        self.action_status = 'dismissed'
        return True
    
    def action_assign(self, user_id=None):
        """Assign to a user."""
        self.ensure_one()
        if user_id:
            self.action_assigned_to = user_id
        return True
    
    def action_create_kpi(self):
        """Create a KPI from this insight."""
        self.ensure_one()
        kpi = self.env['optimaai.kpi'].create({
            'name': self.name,
            'description': self.summary,
            'category': 'operational',
            'target_value': 100,
            'insight_id': self.id,
            'company_id': self.company_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('KPI'),
            'res_model': 'optimaai.kpi',
            'res_id': kpi.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ==========================================
    # Compute Methods
    # ==========================================
    
    @api.depends('impact_score', 'confidence_level')
    def _compute_priority_auto(self):
        """Auto-compute priority based on scores."""
        for record in self:
            if record.impact_score >= 80:
                record.priority = 'critical'
            elif record.impact_score >= 60:
                record.priority = 'high'
            elif record.impact_score >= 40:
                record.priority = 'medium'
            else:
                record.priority = 'low'
    
    # ==========================================
    # Dashboard Methods
    # ==========================================
    
    @api.model
    def get_dashboard_stats(self):
        """Get statistics for dashboard."""
        domain = [('company_id', '=', self.env.company.id)]
        
        return {
            'total': self.search_count(domain),
            'critical': self.search_count(domain + [('priority', '=', 'critical')]),
            'high': self.search_count(domain + [('priority', '=', 'high')]),
            'actionable': self.search_count(domain + [('is_actionable', '=', True)]),
            'pending': self.search_count(domain + [('action_status', '=', 'pending')]),
            'resolved': self.search_count(domain + [('action_status', '=', 'resolved')]),
        }