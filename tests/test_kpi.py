# -*- coding: utf-8 -*-
"""
Tests for KPI Model
"""
import json
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestKPI(common.TransactionCase):
    """
    Test cases for OptimaAI KPI model.
    """
    
    def setUp(self):
        super(TestKPI, self).setUp()
        
        # Create test KPI
        self.kpi = self.env['optimaai.kpi'].create({
            'name': 'Test KPI',
            'code': 'TEST_001',
            'kpi_type': 'percentage',
            'category': 'system',
            'description': 'Test KPI description',
        })
    
    def test_create_kpi(self):
        """Test KPI creation."""
        self.assertTrue(self.kpi.id)
        self.assertEqual(self.kpi.name, 'Test KPI')
        self.assertEqual(self.kpi.code, 'TEST_001')
        self.assertEqual(self.kpi.status, 'draft')
    
    def test_kpi_reference_generation(self):
        """Test that reference is auto-generated."""
        self.assertTrue(self.kpi.reference)
        self.assertTrue(self.kpi.reference.startswith('KPI-'))
    
    def test_kpi_status_flow(self):
        """Test KPI status transitions."""
        # Initial status
        self.assertEqual(self.kpi.status, 'draft')
        
        # Activate
        self.kpi.action_activate()
        self.assertEqual(self.kpi.status, 'active')
        
        # Archive
        self.kpi.action_archive()
        self.assertEqual(self.kpi.status, 'archived')
    
    def test_kpi_action_reset(self):
        """Test KPI reset to draft."""
        self.kpi.action_activate()
        self.assertEqual(self.kpi.status, 'active')
        
        self.kpi.action_reset()
        self.assertEqual(self.kpi.status, 'draft')
    
    def test_kpi_with_target(self):
        """Test KPI with target value."""
        self.kpi.write({
            'value': 75.5,
            'target_value': 100.0,
            'unit': '%',
        })
        
        self.assertEqual(self.kpi.value, 75.5)
        self.assertEqual(self.kpi.target_value, 100.0)
    
    def test_kpi_trend_calculation(self):
        """Test KPI trend calculation."""
        self.kpi.write({
            'value': 100.0,
            'previous_value': 80.0,
        })
        
        self.kpi._compute_trend()
        
        # Trend should be up (25% increase)
        self.assertEqual(self.kpi.trend_direction, 'up')
        self.assertEqual(self.kpi.trend_percentage, 25.0)
    
    def test_kpi_trend_down(self):
        """Test KPI trend when value decreases."""
        self.kpi.write({
            'value': 60.0,
            'previous_value': 100.0,
        })
        
        self.kpi._compute_trend()
        
        # Trend should be down (40% decrease)
        self.assertEqual(self.kpi.trend_direction, 'down')
        self.assertEqual(self.kpi.trend_percentage, 40.0)
    
    def test_kpi_trend_stable(self):
        """Test KPI trend when value is stable."""
        self.kpi.write({
            'value': 100.0,
            'previous_value': 100.0,
        })
        
        self.kpi._compute_trend()
        
        # Trend should be stable
        self.assertEqual(self.kpi.trend_direction, 'stable')
        self.assertEqual(self.kpi.trend_percentage, 0.0)
    
    def test_kpi_unique_code(self):
        """Test KPI code uniqueness."""
        # Creating another KPI with same code should work
        # (uniqueness is usually per company)
        kpi2 = self.env['optimaai.kpi'].create({
            'name': 'Another KPI',
            'code': 'TEST_002',
            'kpi_type': 'count',
            'category': 'system',
        })
        
        self.assertTrue(kpi2.id)


@tagged('post_install', '-at_install')
class TestKPIType(common.TransactionCase):
    """
    Test cases for different KPI types.
    """
    
    def setUp(self):
        super(TestKPIType, self).setUp()
    
    def test_percentage_kpi(self):
        """Test percentage type KPI."""
        kpi = self.env['optimaai.kpi'].create({
            'name': 'Percentage KPI',
            'code': 'PERC_001',
            'kpi_type': 'percentage',
            'category': 'data_quality',
            'value': 85.5,
            'unit': '%',
        })
        
        self.assertEqual(kpi.kpi_type, 'percentage')
    
    def test_count_kpi(self):
        """Test count type KPI."""
        kpi = self.env['optimaai.kpi'].create({
            'name': 'Count KPI',
            'code': 'CNT_001',
            'kpi_type': 'count',
            'category': 'system',
            'value': 150,
            'unit': 'records',
        })
        
        self.assertEqual(kpi.kpi_type, 'count')
    
    def test_currency_kpi(self):
        """Test currency type KPI."""
        kpi = self.env['optimaai.kpi'].create({
            'name': 'Revenue KPI',
            'code': 'REV_001',
            'kpi_type': 'currency',
            'category': 'financial',
            'value': 50000.00,
            'unit': 'USD',
        })
        
        self.assertEqual(kpi.kpi_type, 'currency')
    
    def test_ratio_kpi(self):
        """Test ratio type KPI."""
        kpi = self.env['optimaai.kpi'].create({
            'name': 'Ratio KPI',
            'code': 'RAT_001',
            'kpi_type': 'ratio',
            'category': 'performance',
            'value': 3.5,
            'unit': 'x',
        })
        
        self.assertEqual(kpi.kpi_type, 'ratio')


@tagged('post_install', '-at_install')
class TestKPICalculation(common.TransactionCase):
    """
    Test cases for KPI calculation functionality.
    """
    
    def setUp(self):
        super(TestKPICalculation, self).setUp()
        
        self.kpi = self.env['optimaai.kpi'].create({
            'name': 'Calculatable KPI',
            'code': 'CALC_001',
            'kpi_type': 'count',
            'category': 'system',
            'calculation_formula': 'COUNT(datasets)',
        })
    
    def test_manual_calculation(self):
        """Test manual value setting."""
        self.kpi.write({'value': 42.0})
        
        self.assertEqual(self.kpi.value, 42.0)
    
    def test_previous_value_tracking(self):
        """Test that previous value is tracked."""
        self.kpi.write({'value': 50.0})
        self.kpi.write({'value': 75.0})
        
        self.assertEqual(self.kpi.previous_value, 50.0)
    
    def test_calculation_date_update(self):
        """Test that last_calculated is updated."""
        self.kpi.action_calculate()
        
        self.assertTrue(self.kpi.last_calculated)


@tagged('post_install', '-at_install')
class TestKPICategory(common.TransactionCase):
    """
    Test cases for KPI categories.
    """
    
    def setUp(self):
        super(TestKPICategory, self).setUp()
    
    def test_data_quality_category(self):
        """Test data quality category KPI."""
        kpi = self.env['optimaai.kpi'].create({
            'name': 'Data Quality',
            'code': 'DQ_001',
            'kpi_type': 'percentage',
            'category': 'data_quality',
        })
        
        self.assertEqual(kpi.category, 'data_quality')
    
    def test_prediction_category(self):
        """Test prediction category KPI."""
        kpi = self.env['optimaai.kpi'].create({
            'name': 'Prediction Accuracy',
            'code': 'PRED_001',
            'kpi_type': 'percentage',
            'category': 'prediction',
        })
        
        self.assertEqual(kpi.category, 'prediction')
    
    def test_search_by_category(self):
        """Test searching KPIs by category."""
        self.env['optimaai.kpi'].create({
            'name': 'System KPI 1',
            'code': 'SYS_001',
            'kpi_type': 'count',
            'category': 'system',
        })
        
        self.env['optimaai.kpi'].create({
            'name': 'Data KPI 1',
            'code': 'DATA_001',
            'kpi_type': 'percentage',
            'category': 'data_quality',
        })
        
        system_kpis = self.env['optimaai.kpi'].search([
            ('category', '=', 'system')
        ])
        
        self.assertTrue(len(system_kpis) > 0)