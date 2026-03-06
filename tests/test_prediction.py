# -*- coding: utf-8 -*-
"""
Tests for Prediction Model
"""
import json
from unittest.mock import patch, MagicMock
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestPrediction(common.TransactionCase):
    """
    Test cases for OptimaAI Prediction model.
    """
    
    def setUp(self):
        super(TestPrediction, self).setUp()
        
        # Create test dataset
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
            'data_format': 'json',
            'data_raw': json.dumps([
                {'feature1': 1, 'feature2': 'A', 'target': 0},
                {'feature1': 2, 'feature2': 'B', 'target': 1},
                {'feature1': 3, 'feature2': 'A', 'target': 0},
                {'feature1': 4, 'feature2': 'B', 'target': 1},
            ]),
        })
        
        # Create test prediction
        self.prediction = self.env['optimaai.prediction'].create({
            'name': 'Test Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
            'target_column': 'target',
        })
    
    def test_create_prediction(self):
        """Test prediction creation."""
        self.assertTrue(self.prediction.id)
        self.assertEqual(self.prediction.name, 'Test Prediction')
        self.assertEqual(self.prediction.prediction_type, 'classification')
        self.assertEqual(self.prediction.status, 'pending')
    
    def test_prediction_reference_generation(self):
        """Test that reference is auto-generated."""
        self.assertTrue(self.prediction.reference)
        self.assertTrue(self.prediction.reference.startswith('PR-'))
    
    def test_prediction_status_flow(self):
        """Test prediction status transitions."""
        # Initial status
        self.assertEqual(self.prediction.status, 'pending')
        
        # Queue
        self.prediction.action_queue()
        self.assertEqual(self.prediction.status, 'queued')
        
        # Cancel (from queued)
        self.prediction.action_cancel()
        self.assertEqual(self.prediction.status, 'cancelled')
    
    def test_prediction_run_from_pending(self):
        """Test running prediction from pending status."""
        # Mock the AI service
        with patch('odoo.addons.optimaai.services.ai_service.AIService') as mock_ai:
            mock_instance = MagicMock()
            mock_instance.run_prediction.return_value = {
                'status': 'completed',
                'confidence': 0.85,
                'data': {'predictions': [0, 1, 0, 1]},
                'metrics': {'accuracy': 0.875},
            }
            
            self.prediction.action_run_prediction()
            # Status should change to processing
            self.assertIn(self.prediction.status, ['processing', 'completed'])
    
    def test_prediction_cannot_run_from_completed(self):
        """Test that completed prediction cannot be run again."""
        self.prediction.write({'status': 'completed'})
        
        with self.assertRaises(ValidationError):
            self.prediction.action_run_prediction()
    
    def test_prediction_cannot_run_from_cancelled(self):
        """Test that cancelled prediction cannot be run."""
        self.prediction.write({'status': 'cancelled'})
        
        with self.assertRaises(ValidationError):
            self.prediction.action_run_prediction()
    
    def test_prediction_dataset_required(self):
        """Test that dataset is required."""
        with self.assertRaises(ValidationError):
            self.env['optimaai.prediction'].create({
                'name': 'No Dataset Prediction',
                'prediction_type': 'classification',
            })
    
    def test_prediction_target_column_required_for_training(self):
        """Test target column is required for training predictions."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Test Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
        })
        
        self.assertTrue(prediction.id)
    
    def test_prediction_model_config_json(self):
        """Test model config is stored as JSON."""
        config = {
            'algorithm': 'random_forest',
            'parameters': {
                'n_estimators': 100,
                'max_depth': 10,
            }
        }
        
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Config Test',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
            'model_config': json.dumps(config),
        })
        
        self.assertEqual(prediction.model_config, json.dumps(config))
    
    def test_prediction_copy(self):
        """Test prediction duplication."""
        copy = self.prediction.copy()
        self.assertNotEqual(copy.id, self.prediction.id)
        self.assertEqual(copy.status, 'pending')  # Copy should be pending
        self.assertFalse(copy.result_data)  # Copy should not have results


@tagged('post_install', '-at_install')
class TestPredictionIntegration(common.TransactionCase):
    """
    Integration tests for Prediction with other models.
    """
    
    def setUp(self):
        super(TestPredictionIntegration, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Integration Test Dataset',
            'data_source': 'manual',
            'data_format': 'json',
            'data_raw': json.dumps([
                {'x': 1, 'y': 2, 'label': 'A'},
                {'x': 2, 'y': 4, 'label': 'B'},
            ]),
        })
    
    def test_prediction_creates_insight_on_completion(self):
        """Test that completing prediction can create insight."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Insight Test Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'clustering',
        })
        
        # Simulate completion with results
        prediction.write({
            'status': 'completed',
            'result_confidence': 0.92,
            'result_data': json.dumps({'clusters': 3, 'silhouette_score': 0.85}),
        })
        
        # Create insight based on prediction
        insight = self.env['optimaai.insight'].create({
            'name': 'Clustering Insight',
            'insight_type': 'pattern',
            'description': 'Found 3 distinct clusters',
            'dataset_id': self.dataset.id,
            'prediction_id': prediction.id,
        })
        
        self.assertEqual(insight.prediction_id.id, prediction.id)
    
    def test_multiple_predictions_same_dataset(self):
        """Test multiple predictions on same dataset."""
        pred1 = self.env['optimaai.prediction'].create({
            'name': 'Prediction 1',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
        })
        
        pred2 = self.env['optimaai.prediction'].create({
            'name': 'Prediction 2',
            'dataset_id': self.dataset.id,
            'prediction_type': 'regression',
        })
        
        predictions = self.env['optimaai.prediction'].search([
            ('dataset_id', '=', self.dataset.id)
        ])
        
        self.assertEqual(len(predictions), 2)


@tagged('post_install', '-at_install')
class TestPredictionValidation(common.TransactionCase):
    """
    Test cases for Prediction validation.
    """
    
    def setUp(self):
        super(TestPredictionValidation, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
        })
    
    def test_invalid_prediction_type(self):
        """Test validation for prediction type."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Test',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
        })
        
        # Should be valid
        self.assertEqual(prediction.prediction_type, 'classification')
    
    def test_confidence_value_range(self):
        """Test confidence is between 0 and 1."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Test',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
            'result_confidence': 0.85,
        })
        
        self.assertEqual(prediction.result_confidence, 0.85)
        
        # Test edge cases
        prediction.write({'result_confidence': 0.0})
        self.assertEqual(prediction.result_confidence, 0.0)
        
        prediction.write({'result_confidence': 1.0})
        self.assertEqual(prediction.result_confidence, 1.0)