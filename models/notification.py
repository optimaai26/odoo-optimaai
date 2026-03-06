# -*- coding: utf-8 -*-
"""
Notification Model
==================
In-app notifications for users.
"""
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Notification(models.Model):
    """In-app notification."""
    
    _name = 'optimaai.notification'
    _description = 'Notification'
    _order = 'create_date desc'
    
    # ==========================================
    # Fields
    # ==========================================
    
    title = fields.Char(
        string='Title',
        required=True
    )
    
    message = fields.Text(
        string='Message',
        required=True
    )
    
    notification_type = fields.Selection([
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='Type',
        default='info'
    )
    
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    is_read = fields.Boolean(
        string='Read',
        default=False,
        index=True
    )
    
    read_date = fields.Datetime(
        string='Read Date',
        readonly=True
    )
    
    # Related record
    related_model = fields.Char(
        string='Related Model'
    )
    
    related_id = fields.Integer(
        string='Related ID'
    )
    
    action = fields.Char(
        string='Action',
        help='Action to perform when notification is clicked'
    )
    
    # Company
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='user_id.company_id',
        store=True,
        readonly=True
    )
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_mark_read(self):
        """Mark notification as read."""
        self.write({
            'is_read': True,
            'read_date': fields.Datetime.now(),
        })
        return True
    
    def action_mark_unread(self):
        """Mark notification as unread."""
        self.write({
            'is_read': False,
            'read_date': False,
        })
        return True
    
    def get_related_record(self):
        """Get the related record if exists."""
        self.ensure_one()
        
        if not self.related_model or not self.related_id:
            return False
        
        try:
            return self.env[self.related_model].browse(self.related_id).exists()
        except Exception:
            return False
    
    def open_related(self):
        """Open the related record."""
        self.ensure_one()
        
        if not self.related_model or not self.related_id:
            return {'type': 'ir.actions.act_window_close'}
        
        record = self.get_related_record()
        if not record:
            return {'type': 'ir.actions.act_window_close'}
        
        # Mark as read
        self.action_mark_read()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.related_model,
            'res_id': self.related_id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ==========================================
    # Cron Jobs
    # ==========================================
    
    @api.model
    def _cron_cleanup_old_notifications(self):
        """Clean up old read notifications (older than 90 days)."""
        from datetime import datetime, timedelta
        
        cleanup_date = datetime.now() - timedelta(days=90)
        
        old_notifications = self.search([
            ('is_read', '=', True),
            ('read_date', '<', cleanup_date),
        ])
        
        count = len(old_notifications)
        old_notifications.unlink()
        
        _logger.info('Cleaned up %d old notifications', count)
        return count