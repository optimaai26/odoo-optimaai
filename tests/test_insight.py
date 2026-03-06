# -*- coding: utf-8 -*-
"""
Tests for Insight Model
"""
import json
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestInsight(common.TransactionCase):
    """
    Test cases for OptimaAI Insight model.
    """
    
    def setUp(self):
        super(TestInsight, self).setUp()
        
        # Create test dataset
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
        })
        
        # Create test insight
        self.insight = self.env['optimaai.insight'].create({
            'name': 'Test Insight',
            'insight_type': 'pattern',
            'description': 'Test insight description',
            'dataset_id': self.dataset.id,
        })
    
    def test_create_insight(self):
        """Test insight creation."""
        self.assertTrue(self.insight.id)
        self.assertEqual(self.insight.name, 'Test Insight')
        self.assertEqual(self.insight.insight_type, 'pattern')
        self.assertEqual(self.insight.status, 'draft')
    
    def test_insight_reference_generation(self):
        """Test that reference is auto-generated."""
        self.assertTrue(self.insight.reference)
        self.assertTrue(self.insight.reference.startswith('INS-'))
    
    def test_insight_status_flow(self):
        """Test insight status transitions."""
        # Initial status
        self.assertEqual(self.insight.status, 'draft')
        
        # Activate
        self.insight.action_activate()
        self.assertEqual(self.insight.status, 'active')
        
        # Archive
        self.insight.action_archive()
        self.assertEqual(self.insight.status, 'archived')
    
    def test_insight_action_dismiss(self):
        """Test insight dismissal."""
        self.insight.action_activate()
        self.insight.action_dismiss()
        self.assertEqual(self.insight.status, 'dismissed')
    
    def test_insight_priority_default(self):
        """Test default priority."""
        self.assertEqual(self.insight.priority, 'medium')
    
    def test_insight_with_recommendations(self):
        """Test insight with recommendations."""
        self.insight.write({
            'recommendations': '1. Action one\n2. Action two'
        })
        
        self.assertEqual(self.insight.recommendations, '1. Action one\n2. Action two')
    
    def test_insight_with_impact_data(self):
        """Test insight with impact data."""
        self.insight.write({
            'impact_score': 8.5,
            'impact_currency': 50000.0,
        })
        
        self.assertEqual(self.insight.impact_score, 8.5)
        self.assertEqual(self.insight.impact_currency, 50000.0)
    
    def test_insight_with_prediction(self):
        """Test insight linked to prediction."""
        prediction = self.env['optimaai.prediction'].create({
            'name': 'Test Prediction',
            'dataset_id': self.dataset.id,
            'prediction_type': 'classification',
        })
        
        insight = self.env['optimaai.insight'].create({
            'name': 'Prediction Insight',
            'insight_type': 'prediction',
            'description': 'Insight from prediction',
            'dataset_id': self.dataset.id,
            'prediction_id': prediction.id,
        })
        
        self.assertEqual(insight.prediction_id.id, prediction.id)
    
    def test_insight_copy(self):
        """Test insight duplication."""
        self.insight.action_activate()
        
        copy = self.insight.copy()
        self.assertNotEqual(copy.id, self.insight.id)
        self.assertEqual(copy.status, 'draft')  # Copy should be draft


@tagged('post_install', '-at_install')
class TestInsightPriority(common.TransactionCase):
    """
    Test cases for Insight priority handling.
    """
    
    def setUp(self):
        super(TestInsightPriority, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
        })
    
    def test_low_priority(self):
        """Test low priority insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Low Priority',
            'insight_type': 'info',
            'priority': 'low',
            'dataset_id': self.dataset.id,
        })
        
        self.assertEqual(insight.priority, 'low')
    
    def test_critical_priority(self):
        """Test critical priority insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Critical Issue',
            'insight_type': 'anomaly',
            'priority': 'critical',
            'description': 'Critical issue detected',
            'dataset_id': self.dataset.id,
        })
        
        self.assertEqual(insight.priority, 'critical')
    
    def test_search_by_priority(self):
        """Test searching insights by priority."""
        self.env['optimaai.insight'].create({
            'name': 'High Priority',
            'insight_type': 'pattern',
            'priority': 'high',
            'dataset_id': self.dataset.id,
        })
        
        self.env['optimaai.insight'].create({
            'name': 'Low Priority',
            'insight_type': 'pattern',
            'priority': 'low',
            'dataset_id': self.dataset.id,
        })
        
        high_priority = self.env['optimaai.insight'].search([
            ('priority', 'in', ['high', 'critical'])
        ])
        
        self.assertTrue(len(high_priority) > 0)


@tagged('post_install', '-at_install')
class TestInsightType(common.TransactionCase):
    """
    Test cases for different insight types.
    """
    
    def setUp(self):
        super(TestInsightType, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
        })
    
    def test_pattern_insight(self):
        """Test pattern type insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Pattern Detected',
            'insight_type': 'pattern',
            'description': 'Sales pattern detected',
            'dataset_id': self.dataset.id,
        })
        
        self.assertEqual(insight.insight_type, 'pattern')
    
    def test_anomaly_insight(self):
        """Test anomaly type insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Anomaly Detected',
            'insight_type': 'anomaly',
            'priority': 'high',
            'description': 'Unusual activity detected',
            'dataset_id': self.dataset.id,
        })
        
        self.assertEqual(insight.insight_type, 'anomaly')
    
    def test_trend_insight(self):
        """Test trend type insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Trend Analysis',
            'insight_type': 'trend',
            'description': 'Upward trend in sales',
            'dataset_id': self.dataset.id,
        })
        
        self.assertEqual(insight.insight_type, 'trend')
    
    def test_recommendation_insight(self):
        """Test recommendation type insight."""
        insight = self.env['optimaai.insight'].create({
            'name': 'Recommendation',
            'insight_type': 'recommendation',
            'description': 'Increase inventory for product X',
            'recommendations': 'Order 500 more units',
            'dataset_id': self.dataset.id,
        })
        
        self.assertEqual(insight.insight_type, 'recommendation')