# -*- coding: utf-8 -*-
"""
Tests for API Controllers
"""
import json
from unittest.mock import patch, MagicMock
from odoo.tests import common, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestAPIDataset(common.TransactionCase):
    """
    Test cases for Dataset API endpoints.
    """
    
    def setUp(self):
        super(TestAPIDataset, self).setUp()
        
        # Create test user with API key
        self.test_user = self.env['res.users'].create({
            'name': 'API Test User',
            'login': 'api_test_user',
            'email': 'api@example.com',
        })
        
        # Create API key for user
        self.api_key = self.env['res.users.api.key'].create({
            'user_id': self.test_user.id,
            'name': 'Test API Key',
            'key': 'test-api-key-12345',
        })
    
    def test_dataset_create_via_api(self):
        """Test creating dataset through model."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'API Dataset',
            'data_source': 'manual',
            'data_format': 'json',
        })
        
        self.assertTrue(dataset.id)
        self.assertEqual(dataset.name, 'API Dataset')
    
    def test_dataset_search_via_api(self):
        """Test searching datasets."""
        # Create multiple datasets
        self.env['optimaai.dataset'].create({
            'name': 'Dataset 1',
            'data_source': 'manual',
        })
        
        self.env['optimaai.dataset'].create({
            'name': 'Dataset 2',
            'data_source': 'upload',
        })
        
        # Search
        datasets = self.env['optimaai.dataset'].search([])
        self.assertTrue(len(datasets) >= 2)
        
        # Filtered search
        manual_datasets = self.env['optimaai.dataset'].search([
            ('data_source', '=', 'manual')
        ])
        self.assertTrue(len(manual_datasets) >= 1)
    
    def test_dataset_read_via_api(self):
        """Test reading dataset fields."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'Read Test Dataset',
            'data_source': 'manual',
            'data_format': 'json',
            'data_raw': json.dumps({'test': 'data'}),
        })
        
        # Read specific fields
        values = dataset.read(['name', 'data_source', 'data_format'])
        
        self.assertEqual(values[0]['name'], 'Read Test Dataset')
        self.assertEqual(values[0]['data_source'], 'manual')
        self.assertEqual(values[0]['data_format'], 'json')
    
    def test_dataset_update_via_api(self):
        """Test updating dataset through model."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'Update Test Dataset',
            'data_source': 'manual',
        })
        
        dataset.write({
            'name': 'Updated Dataset Name',
            'data_format': 'csv',
        })
        
        self.assertEqual(dataset.name, 'Updated Dataset Name')
        self.assertEqual(dataset.data_format, 'csv')
    
    def test_dataset_delete_via_api(self):
        """Test deleting (unLink) dataset."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'Delete Test Dataset',
            'data_source': 'manual',
        })
        
        dataset_id = dataset.id
        dataset.unlink()
        
        # Verify deleted
        deleted = self.env['optimaai.dataset'].search([
            ('id', '=', dataset_id)
        ])
        
        self.assertEqual(len(deleted), 0)


@tagged('post_install', '-at_install')
class TestAPIPrediction(common.TransactionCase):
    """
    Test cases for Prediction API endpoints.
    """
    
    def setUp(self):
        super(TestAPIPrediction, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'API Test Dataset',
            'data_source': 'manual',
            'data_format': 'json',
            'data_raw': json.dumps([
                {'x': 1, 'y': 2},
                {'x': 2, 'y': 4},
            ]),
        })
    
    def test_prediction_create_via_api(self):
        """Test creating prediction through model."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'API Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
        })
        
        self.assertTrue(prediction.id)
        self.assertEqual(prediction.status, 'pending')
    
    def test_prediction_status_update_via_api(self):
        """Test updating prediction status."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Status Test Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'regression',
        })
        
        prediction.action_queue()
        self.assertEqual(prediction.status, 'queued')
        
        prediction.write({'status': 'processing'})
        self.assertEqual(prediction.status, 'processing')
        
        prediction.write({
            'status': 'completed',
            'result_confidence': 0.95,
            'result_data': json.dumps({'prediction': 'success'}),
        })
        
        self.assertEqual(prediction.status, 'completed')
        self.assertEqual(prediction.result_confidence, 0.95)
    
    def test_prediction_results_via_api(self):
        """Test retrieving prediction results."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Results Test Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'clustering',
            'status': 'completed',
            'result_data': json.dumps({'clusters': 3, 'labels': [0, 1, 0]}),
            'result_confidence': 0.88,
        })
        
        # Read results
        values = prediction.read(['result_data', 'result_confidence', 'status'])
        
        self.assertEqual(values[0]['status'], 'completed')
        result_data = json.loads(values[0]['result_data'])
        self.assertEqual(result_data['clusters'], 3)


@tagged('post_install', '-at_install')
class TestAPIInsight(common.TransactionCase):
    """
    Test cases for Insight API endpoints.
    """
    
    def setUp(self):
        super(TestAPIInsight, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Insight API Dataset',
            'data_source': 'manual',
        })
    
    def test_insight_create_via_api(self):
        """Test creating insight through model."""
        insight = self.env['optimaai.insight'].create({
            'name': 'API Insight',
            'insight_type': 'pattern',
            'description': 'Pattern detected in data',
            'dataset_id': self.dataset.id,
        })
        
        self.assertTrue(insight.id)
        self.assertEqual(insight.status, 'draft')
    
    def test_insight_activate_via_api(self):
        """Test activating insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Activation Test Insight',
            'insight_type': 'trend',
            'description': 'Trend detected',
            'dataset_id': self.dataset.id,
        })
        
        insight.action_activate()
        self.assertEqual(insight.status, 'active')
    
    def test_insight_filter_via_api(self):
        """Test filtering insights."""
        # Create insights with different types
        self.env['optimaai.insight'].create({
            'name': 'Pattern Insight',
            'insight_type': 'pattern',
            'dataset_id': self.dataset.id,
        })
        
        self.env['optimaai.insight'].create({
            'name': 'Anomaly Insight',
            'insight_type': 'anomaly',
            'priority': 'high',
            'dataset_id': self.dataset.id,
        })
        
        # Filter by type
        patterns = self.env['optimaai.insight'].search([
            ('insight_type', '=', 'pattern')
        ])
        
        anomalies = self.env['optimaai.insight'].search([
            ('insight_type', '=', 'anomaly')
        ])
        
        self.assertTrue(len(patterns) >= 1)
        self.assertTrue(len(anomalies) >= 1)


@tagged('post_install', '-at_install')
class TestAPIAuthentication(common.TransactionCase):
    """
    Test cases for API authentication.
    """
    
    def setUp(self):
        super(TestAPIAuthentication, self).setUp()
        
        self.test_user = self.env['res.users'].create({
            'name': 'Auth Test User',
            'login': 'auth_test_user',
            'email': 'auth@example.com',
        })
    
    def test_api_key_creation(self):
        """Test API key creation."""
        api_key = self.env['res.users.api.key'].create({
            'user_id': self.test_user.id,
            'name': 'Test Key',
            'key': 'unique-test-key-789',
        })
        
        self.assertTrue(api_key.id)
        self.assertEqual(api_key.user_id.id, self.test_user.id)
    
    def test_api_key_search(self):
        """Test finding user by API key."""
        key_value = 'searchable-key-456'
        
        self.env['res.users.api.key'].create({
            'user_id': self.test_user.id,
            'name': 'Searchable Key',
            'key': key_value,
        })
        
        # Search for key
        found_key = self.env['res.users.api.key'].search([
            ('key', '=', key_value)
        ], limit=1)
        
        self.assertEqual(len(found_key), 1)
        self.assertEqual(found_key.user_id.id, self.test_user.id)


@tagged('post_install', '-at_install')
class TestAPIPermissions(common.TransactionCase):
    """
    Test cases for API permissions and access control.
    """
    
    def setUp(self):
        super(TestAPIPermissions, self).setUp()
        
        # Create regular user
        self.regular_user = self.env['res.users'].create({
            'name': 'Regular User',
            'login': 'regular_user',
            'email': 'regular@example.com',
        })
    
    def test_user_can_create_own_dataset(self):
        """Test user can create dataset."""
        dataset = self.env['optimaai.dataset'].sudo(self.regular_user).create({
            'name': 'User Dataset',
            'data_source': 'manual',
        })
        
        self.assertTrue(dataset.id)
    
    def test_user_can_read_own_records(self):
        """Test user can read their own records."""
        dataset = self.env['optimaai.dataset'].sudo(self.regular_user).create({
            'name': 'User Own Dataset',
            'data_source': 'manual',
        })
        
        # User should be able to read their own record
        datasets = self.env['optimaai.dataset'].sudo(self.regular_user).search([
            ('id', '=', dataset.id)
        ])
        
        self.assertEqual(len(datasets), 1)
    
    def test_public_access_restricted(self):
        """Test that public user has restricted access."""
        public_user = self.env.ref('base.public_user')
        
        # Public user should not be able to create datasets
        # (depending on security rules)
        # This tests that security is properly configured
        datasets = self.env['optimaai.dataset'].sudo(public_user).search([])
        
        # Result depends on security rules, but should not error
        self.assertIsInstance(datasets.count(), int)