# -*- coding: utf-8 -*-
"""
Prediction Model
================
AI-powered predictions using datasets.
Equivalent to Next.js predictions page.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class Prediction(models.Model):
    """Prediction model for AI predictions."""
    
    _name = 'optimaai.prediction'
    _description = 'Prediction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    # Dataset relation
    dataset_id = fields.Many2one(
        comodel_name='optimaai.dataset',
        string='Dataset',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    # Prediction configuration
    prediction_type = fields.Selection([
        ('churn', 'Churn Prediction'),
        ('revenue_forecast', 'Revenue Forecast'),
        ('growth_scoring', 'Growth Scoring'),
        ('clv', 'Customer Lifetime Value'),
        ('custom', 'Custom Prediction'),
    ], string='Prediction Type',
        required=True,
        default='churn',
        tracking=True
    )
    
    prediction_options = fields.Text(
        string='Options',
        widget='json',
        default='{}'
    )
    
    # Status
    status = fields.Selection([
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status',
        default='queued',
        tracking=True,
        index=True
    )
    
    progress = fields.Integer(
        string='Progress',
        default=0,
        help='Progress percentage (0-100)'
    )
    
    # Results
    result_summary = fields.Text(
        string='Result Summary',
        readonly=True
    )
    result_confidence = fields.Integer(
        string='Confidence Score',
        readonly=True,
        default=0,
        help='Confidence percentage (0-100)'
    )
    result_data = fields.Text(
        string='Result Data',
        readonly=True,
        widget='json'
    )
    chart_config = fields.Text(
        string='Chart Configuration',
        readonly=True,
        widget='json'
    )
    
    # Error handling
    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )
    
    # Timing
    started_date = fields.Datetime(
        string='Started Date',
        readonly=True
    )
    completed_date = fields.Datetime(
        string='Completed Date',
        readonly=True
    )
    duration_seconds = fields.Integer(
        string='Duration (seconds)',
        readonly=True
    )
    
    # Ownership
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    # Insights generated from this prediction
    insight_ids = fields.One2many(
        comodel_name='optimaai.insight',
        inverse_name='prediction_id',
        string='Insights'
    )
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_run(self):
        """Start the prediction process."""
        self.ensure_one()
        
        if self.status not in ('queued', 'failed'):
            raise UserError(_('Prediction must be queued or failed to run.'))
        
        # Update status
        self.status = 'running'
        self.started_date = fields.Datetime.now()
        
        # Call AI service
        self.with_delay(priority=5)._run_prediction()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prediction Started'),
                'message': _('Prediction is now running. You will be notified when it completes.'),
                'type': 'info',
                'sticky': False,
            }
        }
    
    def _run_prediction(self):
        """
        Execute the prediction using AI service.
        This is an async method called via queue.
        """
        self.ensure_one()
        
        try:
            # Get AI service
            ai_service = self.env['optimaai.ai.service']
            
            # Update progress
            self.progress = 10
            
            # Call external AI API
            result = ai_service.call_prediction_api(self)
            
            self.progress = 80
            
            # Process results
            ai_service.process_prediction_result(self, result)
            
            # Update status
            self.status = 'completed'
            self.progress = 100
            self.completed_date = fields.Datetime.now()
            if self.started_date:
                self.duration_seconds = (self.completed_date - self.started_date).total_seconds()
            
            # Send notification
            self.env['optimaai.notification.service'].notify_prediction_complete(self)
            
            _logger.info('Prediction %s completed with confidence %d%%', 
                        self.name, self.result_confidence)
            
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
            self.progress = 0
            _logger.error('Prediction %s failed: %s', self.name, str(e))
    
    def action_cancel(self):
        """Cancel a running prediction."""
        self.ensure_one()
        
        if self.status != 'running':
            raise UserError(_('Only running predictions can be cancelled.'))
        
        self.status = 'failed'
        self.error_message = 'Cancelled by user'
        
        return True
    
    def action_rerun(self):
        """Re-run a completed/failed prediction."""
        self.ensure_one()
        
        # Reset state
        self.status = 'queued'
        self.progress = 0
        self.error_message = False
        self.result_summary = False
        self.result_confidence = 0
        self.result_data = False
        self.chart_config = False
        
        return self.action_run()
    
    def action_view_insights(self):
        """View insights generated from this prediction."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insights'),
            'res_model': 'optimaai.insight',
            'view_mode': 'tree,form',
            'domain': [('prediction_id', '=', self.id)],
            'context': {'default_prediction_id': self.id},
        }
    
    # ==========================================
    # Dashboard Methods
    # ==========================================
    
    @api.model
    def get_dashboard_stats(self):
        """Get statistics for dashboard."""
        domain = [('company_id', '=', self.env.company.id)]
        
        completed_domain = domain + [('status', '=', 'completed')]
        completed_records = self.search(completed_domain)
        avg_confidence = 0
        if completed_records:
            confidences = completed_records.mapped('result_confidence')
            avg_confidence = sum(confidences) / len(confidences)
        
        return {
            'total': self.search_count(domain),
            'completed': self.search_count(domain + [('status', '=', 'completed')]),
            'running': self.search_count(domain + [('status', '=', 'running')]),
            'queued': self.search_count(domain + [('status', '=', 'queued')]),
            'failed': self.search_count(domain + [('status', '=', 'failed')]),
            'avg_confidence': avg_confidence,
        }
    
    @api.model
    def _cron_process_queued(self):
        """Process all queued predictions."""
        queued = self.search([
            ('status', '=', 'queued'),
        ], limit=10)
        
        for prediction in queued:
            try:
                prediction.action_run()
            except Exception as e:
                _logger.error('Failed to start prediction %s: %s', prediction.name, str(e))