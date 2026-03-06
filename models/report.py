# -*- coding: utf-8 -*-
"""
Report Model
============
Automated report generation and scheduling.
Equivalent to Next.js reports page.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import json
import logging

_logger = logging.getLogger(__name__)


class Report(models.Model):
    """Report model for automated reporting."""
    
    _name = 'optimaai.report'
    _description = 'Report'
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
    
    # Report type
    report_type = fields.Selection([
        ('executive', 'Executive Summary'),
        ('prediction', 'Prediction Report'),
        ('insight', 'Insight Summary'),
        ('kpi', 'KPI Dashboard'),
        ('custom', 'Custom Report'),
    ], string='Report Type',
        default='executive',
        required=True,
        tracking=True
    )
    
    # Configuration
    format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ], string='Format',
        default='pdf',
        required=True
    )
    
    # Content sources
    dataset_ids = fields.Many2many(
        comodel_name='optimaai.dataset',
        relation='optimaai_report_dataset_rel',
        column1='report_id',
        column2='dataset_id',
        string='Datasets'
    )
    
    prediction_ids = fields.Many2many(
        comodel_name='optimaai.prediction',
        relation='optimaai_report_prediction_rel',
        column1='report_id',
        column2='prediction_id',
        string='Predictions'
    )
    
    insight_ids = fields.Many2many(
        comodel_name='optimaai.insight',
        relation='optimaai_report_insight_rel',
        column1='report_id',
        column2='insight_id',
        string='Insights'
    )
    
    kpi_ids = fields.Many2many(
        comodel_name='optimaai.kpi',
        relation='optimaai_report_kpi_rel',
        column1='report_id',
        column2='kpi_id',
        string='KPIs'
    )
    
    # Scheduling
    schedule_type = fields.Selection([
        ('manual', 'Manual Only'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ], string='Schedule',
        default='manual',
        tracking=True
    )
    
    schedule_time = fields.Float(
        string='Schedule Time',
        default=8.0,
        help='Time of day to generate (24h format)'
    )
    
    schedule_day = fields.Integer(
        string='Schedule Day',
        default=1,
        help='Day of week (1-7) or month (1-31)'
    )
    
    next_run_date = fields.Datetime(
        string='Next Run Date',
        compute='_compute_next_run_date',
        store=True
    )
    
    last_run_date = fields.Datetime(
        string='Last Run Date',
        readonly=True
    )
    
    # Recipients
    recipient_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='optimaai_report_recipient_rel',
        column1='report_id',
        column2='user_id',
        string='Recipients'
    )
    
    recipient_emails = fields.Text(
        string='Additional Emails',
        help='Comma-separated email addresses'
    )
    
    # Generated content
    file_name = fields.Char(
        string='Filename',
        readonly=True
    )
    
    file_data = fields.Binary(
        string='File Data',
        attachment=True,
        readonly=True
    )
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status',
        default='draft',
        tracking=True,
        index=True
    )
    
    error_message = fields.Text(
        string='Error Message',
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
    
    created_by = fields.Many2one(
        comodel_name='res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # ==========================================
    # Computed Methods
    # ==========================================
    
    @api.depends('schedule_type', 'schedule_time', 'schedule_day')
    def _compute_next_run_date(self):
        """Calculate next run date based on schedule."""
        from datetime import datetime, timedelta
        
        for record in self:
            if record.schedule_type == 'manual':
                record.next_run_date = False
                continue
            
            now = fields.Datetime.now()
            base_time = now.replace(
                hour=int(record.schedule_time),
                minute=int((record.schedule_time % 1) * 60),
                second=0,
                microsecond=0
            )
            
            if record.schedule_type == 'daily':
                if base_time > now:
                    record.next_run_date = base_time
                else:
                    record.next_run_date = base_time + timedelta(days=1)
            
            elif record.schedule_type == 'weekly':
                days_ahead = record.schedule_day - now.isoweekday()
                if days_ahead < 0 or (days_ahead == 0 and base_time <= now):
                    days_ahead += 7
                record.next_run_date = base_time + timedelta(days=days_ahead)
            
            elif record.schedule_type == 'monthly':
                target_day = min(record.schedule_day, 28)
                target_date = now.replace(day=target_day)
                if target_date < now or (target_date == now and base_time <= now):
                    if now.month == 12:
                        target_date = target_date.replace(year=now.year + 1, month=1)
                    else:
                        target_date = target_date.replace(month=now.month + 1)
                record.next_run_date = target_date.replace(
                    hour=int(record.schedule_time),
                    minute=int((record.schedule_time % 1) * 60)
                )
            
            else:
                record.next_run_date = base_time + timedelta(days=90)  # Quarterly
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_generate(self):
        """Generate the report."""
        self.ensure_one()
        
        if self.status == 'generating':
            raise UserError(_('Report is already being generated.'))
        
        self.status = 'generating'
        
        # Run async
        self.with_delay(priority=10)._generate_report()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Report Generation'),
                'message': _('Report generation started. You will be notified when complete.'),
                'type': 'info',
            }
        }
    
    def _generate_report(self):
        """
        Generate the report file.
        Called async via queue.
        """
        self.ensure_one()
        
        try:
            report_service = self.env['optimaai.report.service']
            
            # Generate based on type
            if self.format == 'pdf':
                file_data, file_name = report_service.generate_pdf(self)
            elif self.format == 'xlsx':
                file_data, file_name = report_service.generate_excel(self)
            elif self.format == 'csv':
                file_data, file_name = report_service.generate_csv(self)
            else:
                file_data, file_name = report_service.generate_json(self)
            
            # Store result
            self.write({
                'file_data': base64.b64encode(file_data),
                'file_name': file_name,
                'status': 'completed',
                'last_run_date': fields.Datetime.now(),
            })
            
            # Send notifications
            if self.recipient_user_ids or self.recipient_emails:
                self._send_report_email()
            
            _logger.info('Report %s generated successfully', self.name)
            
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
            _logger.error('Failed to generate report %s: %s', self.name, str(e))
    
    def _send_report_email(self):
        """Send generated report to recipients."""
        self.ensure_one()
        
        if not self.file_data:
            return
        
        recipients = list(self.recipient_user_ids.mapped('email'))
        if self.recipient_emails:
            recipients.extend([e.strip() for e in self.recipient_emails.split(',')])
        
        recipients = list(set(filter(None, recipients)))
        
        if not recipients:
            return
        
        mail_values = {
            'subject': _('OptimaAI Report: %s') % self.name,
            'body_html': self._get_report_email_body(),
            'email_to': ','.join(recipients),
            'auto_delete': False,
        }
        
        # Add attachment
        attachment = self.env['ir.attachment'].create({
            'name': self.file_name,
            'datas': self.file_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/octet-stream',
        })
        
        mail_values['attachment_ids'] = [(6, 0, [attachment.id])]
        
        self.env['mail.mail'].create(mail_values).send()
    
    def _get_report_email_body(self):
        """Get email body for report."""
        return f"""
        <p>Hello,</p>
        <p>Please find attached the report: <strong>{self.name}</strong></p>
        <p>Report Type: {dict(self._fields['report_type'].get_description(self.env)['selection']).get(self.report_type)}</p>
        <p>Generated: {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Best regards,<br>OptimaAI System</p>
        """
    
    def action_download(self):
        """Download the report file."""
        self.ensure_one()
        
        if not self.file_data:
            raise UserError(_('No file available for download.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/optimaai/report/{self.id}/download',
            'target': 'self',
        }
    
    def action_preview(self):
        """Preview the report."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/optimaai/report/{self.id}/preview',
            'target': 'new',
        }
    
    # ==========================================
    # Cron Jobs
    # ==========================================
    
    @api.model
    def _cron_process_scheduled(self):
        """Process all scheduled reports that are due."""
        now = fields.Datetime.now()
        
        reports = self.search([
            ('active', '=', True),
            ('schedule_type', '!=', 'manual'),
            ('next_run_date', '<=', now),
            ('status', '!=', 'generating'),
        ])
        
        for report in reports:
            try:
                report.action_generate()
            except Exception as e:
                _logger.error('Failed to generate scheduled report %s: %s', report.name, str(e))