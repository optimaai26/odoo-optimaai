# -*- coding: utf-8 -*-
"""
Tests for Notification Model
"""
import json
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestNotification(common.TransactionCase):
    """
    Test cases for OptimaAI Notification model.
    """
    
    def setUp(self):
        super(TestNotification, self).setUp()
        
        # Create test user
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_notification_user',
            'email': 'test@example.com',
        })
        
        # Create test notification
        self.notification = self.env['optimaai.notification'].create({
            'name': 'Test Notification',
            'notification_type': 'info',
            'message': 'This is a test notification',
            'user_id': self.test_user.id,
        })
    
    def test_create_notification(self):
        """Test notification creation."""
        self.assertTrue(self.notification.id)
        self.assertEqual(self.notification.name, 'Test Notification')
        self.assertEqual(self.notification.notification_type, 'info')
        self.assertFalse(self.notification.is_read)
    
    def test_notification_reference_generation(self):
        """Test that reference is auto-generated."""
        self.assertTrue(self.notification.reference)
        self.assertTrue(self.notification.reference.startswith('NOT-'))
    
    def test_notification_mark_read(self):
        """Test marking notification as read."""
        self.notification.action_mark_read()
        
        self.assertTrue(self.notification.is_read)
        self.assertTrue(self.notification.read_date)
    
    def test_notification_mark_unread(self):
        """Test marking notification as unread."""
        self.notification.action_mark_read()
        self.assertTrue(self.notification.is_read)
        
        self.notification.action_mark_unread()
        self.assertFalse(self.notification.is_read)
        self.assertFalse(self.notification.read_date)
    
    def test_notification_dismiss(self):
        """Test dismissing notification."""
        self.notification.action_dismiss()
        
        self.assertTrue(self.notification.is_dismissed)
    
    def test_notification_priority_default(self):
        """Test default priority."""
        self.assertEqual(self.notification.priority, 'medium')
    
    def test_notification_with_data(self):
        """Test notification with additional data."""
        data = {'key': 'value', 'number': 42}
        
        notification = self.env['optimaai.notification'].create({
            'name': 'Data Notification',
            'notification_type': 'info',
            'message': 'Notification with data',
            'data': json.dumps(data),
        })
        
        self.assertEqual(notification.data, json.dumps(data))
    
    def test_notification_with_related_record(self):
        """Test notification linked to a record."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'Related Dataset',
            'data_source': 'manual',
        })
        
        notification = self.env['optimaai.notification'].create({
            'name': 'Dataset Notification',
            'notification_type': 'success',
            'message': 'Dataset processing completed',
            'res_model': 'optimaai.dataset',
            'res_id': dataset.id,
        })
        
        self.assertEqual(notification.res_model, 'optimaai.dataset')
        self.assertEqual(notification.res_id, dataset.id)


@tagged('post_install', '-at_install')
class TestNotificationType(common.TransactionCase):
    """
    Test cases for different notification types.
    """
    
    def setUp(self):
        super(TestNotificationType, self).setUp()
    
    def test_info_notification(self):
        """Test info type notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'Info',
            'notification_type': 'info',
            'message': 'Information message',
        })
        
        self.assertEqual(notification.notification_type, 'info')
    
    def test_success_notification(self):
        """Test success type notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'Success',
            'notification_type': 'success',
            'message': 'Operation successful',
        })
        
        self.assertEqual(notification.notification_type, 'success')
    
    def test_warning_notification(self):
        """Test warning type notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'Warning',
            'notification_type': 'warning',
            'message': 'Warning message',
            'priority': 'high',
        })
        
        self.assertEqual(notification.notification_type, 'warning')
        self.assertEqual(notification.priority, 'high')
    
    def test_error_notification(self):
        """Test error type notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'Error',
            'notification_type': 'error',
            'message': 'Error occurred',
            'priority': 'critical',
        })
        
        self.assertEqual(notification.notification_type, 'error')
        self.assertEqual(notification.priority, 'critical')


@tagged('post_install', '-at_install')
class TestNotificationPriority(common.TransactionCase):
    """
    Test cases for notification priority.
    """
    
    def setUp(self):
        super(TestNotificationPriority, self).setUp()
    
    def test_low_priority(self):
        """Test low priority notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'Low Priority',
            'notification_type': 'info',
            'message': 'Low priority message',
            'priority': 'low',
        })
        
        self.assertEqual(notification.priority, 'low')
    
    def test_high_priority(self):
        """Test high priority notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'High Priority',
            'notification_type': 'warning',
            'message': 'High priority message',
            'priority': 'high',
        })
        
        self.assertEqual(notification.priority, 'high')
    
    def test_critical_priority(self):
        """Test critical priority notification."""
        notification = self.env['optimaai.notification'].create({
            'name': 'Critical',
            'notification_type': 'error',
            'message': 'Critical issue',
            'priority': 'critical',
        })
        
        self.assertEqual(notification.priority, 'critical')
    
    def test_search_by_priority(self):
        """Test searching by priority."""
        self.env['optimaai.notification'].create({
            'name': 'High',
            'notification_type': 'warning',
            'message': 'High',
            'priority': 'high',
        })
        
        self.env['optimaai.notification'].create({
            'name': 'Low',
            'notification_type': 'info',
            'message': 'Low',
            'priority': 'low',
        })
        
        high_priority = self.env['optimaai.notification'].search([
            ('priority', 'in', ['high', 'critical'])
        ])
        
        self.assertTrue(len(high_priority) > 0)


@tagged('post_install', '-at_install')
class TestNotificationService(common.TransactionCase):
    """
    Test cases for Notification Service.
    """
    
    def setUp(self):
        super(TestNotificationService, self).setUp()
        
        self.notification_service = self.env['notification.service']
        self.test_user = self.env['res.users'].create({
            'name': 'Service Test User',
            'login': 'service_test_user',
            'email': 'service@example.com',
        })
    
    def test_send_basic_notification(self):
        """Test sending basic notification."""
        notification = self.notification_service.send_notification(
            user_id=self.test_user.id,
            name='Service Notification',
            message='Test from service',
            notification_type='info',
        )
        
        self.assertTrue(notification.id)
        self.assertEqual(notification.user_id.id, self.test_user.id)
    
    def test_send_notification_with_data(self):
        """Test sending notification with data."""
        data = {'action': 'view_dataset', 'dataset_id': 42}
        
        notification = self.notification_service.send_notification(
            user_id=self.test_user.id,
            name='Data Notification',
            message='Check dataset',
            notification_type='info',
            data=data,
        )
        
        self.assertTrue(notification.id)
    
    def test_broadcast_notification(self):
        """Test broadcasting notification to multiple users."""
        users = self.env['res.users'].search([('active', '=', True)], limit=5)
        
        notifications = self.notification_service.broadcast(
            name='Broadcast',
            message='Broadcast message',
            notification_type='info',
            user_ids=users.ids,
        )
        
        self.assertEqual(len(notifications), len(users))
    
    def test_create_for_record(self):
        """Test creating notification for a record."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'Record Dataset',
            'data_source': 'manual',
        })
        
        notification = self.notification_service.create_for_record(
            record=dataset,
            name='Record Notification',
            message='Dataset notification',
            notification_type='success',
            user_id=self.test_user.id,
        )
        
        self.assertEqual(notification.res_model, 'optimaai.dataset')
        self.assertEqual(notification.res_id, dataset.id)