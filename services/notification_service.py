# -*- coding: utf-8 -*-
"""
Notification Service
====================
Centralized notification service.
Handles in-app notifications, emails, and webhooks.
"""
from odoo import models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class NotificationService(models.AbstractModel):
    """Notification service for sending notifications."""
    
    _name = 'optimaai.notification.service'
    _description = 'Notification Service'
    
    @api.model
    def send_notification(self, user_id, title, message, notification_type='info', 
                          related_model=None, related_id=None, action=None):
        """
        Send notification to a user.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type (info, success, warning, error)
            related_model: Related model name
            related_id: Related record ID
            action: Action to perform on click
        
        Returns:
            Created notification record
        """
        # Create in-app notification
        notification = self.env['optimaai.notification'].create({
            'user_id': user_id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'related_model': related_model,
            'related_id': related_id,
            'action': action,
        })
        
        # Also send via Odoo's built-in mail system for email
        try:
            self._send_email_notification(user_id, title, message)
        except Exception as e:
            _logger.warning('Failed to send email notification: %s', str(e))
        
        return notification
    
    @api.model
    def send_bulk_notification(self, user_ids, title, message, **kwargs):
        """
        Send notification to multiple users.
        
        Args:
            user_ids: List of user IDs
            title: Notification title
            message: Notification message
            **kwargs: Additional arguments
        
        Returns:
            List of created notification records
        """
        notifications = []
        for user_id in user_ids:
            notification = self.send_notification(user_id, title, message, **kwargs)
            notifications.append(notification)
        return notifications
    
    @api.model
    def send_company_notification(self, title, message, company_id=None, **kwargs):
        """
        Send notification to all users in company.
        
        Args:
            title: Notification title
            message: Notification message
            company_id: Company ID (current if not specified)
            **kwargs: Additional arguments
        
        Returns:
            List of created notification records
        """
        if company_id is None:
            company_id = self.env.company.id
        
        users = self.env['res.users'].search([
            ('company_id', '=', company_id),
            ('active', '=', True),
        ])
        
        return self.send_bulk_notification(users.ids, title, message, **kwargs)
    
    @api.model
    def _send_email_notification(self, user_id, title, message):
        """Send email notification to user."""
        user = self.env['res.users'].browse(user_id)
        
        if not user.email:
            return False
        
        # Use Odoo's mail system
        mail_values = {
            'subject': title,
            'body_html': f'''
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #4A90D9;">{title}</h2>
                    <p>{message}</p>
                    <hr/>
                    <p style="color: #666; font-size: 12px;">
                        Sent from OptimaAI
                    </p>
                </div>
            ''',
            'email_to': user.email,
            'email_from': self.env.company.email,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        return True
    
    @api.model
    def mark_as_read(self, notification_id):
        """Mark notification as read."""
        notification = self.env['optimaai.notification'].browse(notification_id)
        if notification.exists():
            notification.is_read = True
        return True
    
    @api.model
    def mark_all_as_read(self, user_id=None):
        """Mark all notifications as read for a user."""
        if user_id is None:
            user_id = self.env.user.id
        
        notifications = self.env['optimaai.notification'].search([
            ('user_id', '=', user_id),
            ('is_read', '=', False),
        ])
        
        notifications.write({'is_read': True})
        return len(notifications)
    
    @api.model
    def get_unread_count(self, user_id=None):
        """Get unread notification count for a user."""
        if user_id is None:
            user_id = self.env.user.id
        
        return self.env['optimaai.notification'].search_count([
            ('user_id', '=', user_id),
            ('is_read', '=', False),
        ])
    
    @api.model
    def get_notifications(self, user_id=None, limit=20, offset=0):
        """Get notifications for a user."""
        if user_id is None:
            user_id = self.env.user.id
        
        return self.env['optimaai.notification'].search_read(
            [('user_id', '=', user_id)],
            ['title', 'message', 'notification_type', 'is_read', 'create_date', 
             'related_model', 'related_id', 'action'],
            limit=limit,
            offset=offset,
            order='create_date desc'
        )