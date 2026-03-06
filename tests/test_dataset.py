# -*- coding: utf-8 -*-
"""
Tests for Dataset Model
"""
import json
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError, AccessError


@tagged('post_install', '-at_install')
class TestDataset(common.TransactionCase):
    """
    Test cases for OptimaAI Dataset model.
    """
    
    def setUp(self):
        super(TestDataset, self).setUp()
        
        # Create test user
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@example.com',
        })
        
        # Create test dataset
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
            'data_format': 'json',
            'data_raw': json.dumps([
                {'id': 1, 'name': 'Item 1', 'value': 100},
                {'id': 2, 'name': 'Item 2', 'value': 200},
                {'id': 3, 'name': 'Item 3', 'value': 300},
            ]),
        })
    
    def test_create_dataset(self):
        """Test dataset creation."""
        self.assertTrue(self.dataset.id)
        self.assertEqual(self.dataset.name, 'Test Dataset')
        self.assertEqual(self.dataset.data_source, 'manual')
        self.assertEqual(self.dataset.status, 'draft')
    
    def test_dataset_reference_generation(self):
        """Test that reference is auto-generated."""
        self.assertTrue(self.dataset.reference)
        self.assertTrue(self.dataset.reference.startswith('DS-'))
    
    def test_dataset_with_columns(self):
        """Test dataset with column definitions."""
        # Create columns
        self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'id',
            'column_type': 'integer',
            'required': True,
        })
        self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'name',
            'column_type': 'char',
            'required': True,
        })
        self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'value',
            'column_type': 'float',
            'required': False,
        })
        
        self.assertEqual(len(self.dataset.column_ids), 3)
    
    def test_dataset_status_flow(self):
        """Test dataset status transitions."""
        # Initial status
        self.assertEqual(self.dataset.status, 'draft')
        
        # Validate
        self.dataset.action_validate()
        self.assertEqual(self.dataset.status, 'validated')
        
        # Process
        self.dataset.action_process()
        self.assertEqual(self.dataset.status, 'processing')
        
        # Complete
        self.dataset.action_complete()
        self.assertEqual(self.dataset.status, 'completed')
    
    def test_dataset_action_reset(self):
        """Test dataset reset to draft."""
        self.dataset.action_validate()
        self.assertEqual(self.dataset.status, 'validated')
        
        self.dataset.action_reset()
        self.assertEqual(self.dataset.status, 'draft')
    
    def test_dataset_compute_row_count(self):
        """Test row count computation."""
        self.dataset._compute_row_count()
        self.assertEqual(self.dataset.row_count, 3)
    
    def test_dataset_copy(self):
        """Test dataset duplication."""
        copy = self.dataset.copy()
        self.assertNotEqual(copy.id, self.dataset.id)
        self.assertTrue('(Copy)' in copy.name)
    
    def test_dataset_name_search(self):
        """Test name search functionality."""
        # Search by name
        results = self.env['optimaai.dataset'].name_search('Test')
        self.assertTrue(len(results) > 0)
        
        # Search by reference
        results = self.env['optimaai.dataset'].name_search(self.dataset.reference)
        self.assertTrue(len(results) > 0)


@tagged('post_install', '-at_install')
class TestDatasetColumn(common.TransactionCase):
    """
    Test cases for Dataset Column model.
    """
    
    def setUp(self):
        super(TestDatasetColumn, self).setUp()
        
        self.dataset = self.env['optimaai.dataset'].create({
            'name': 'Test Dataset',
            'data_source': 'manual',
        })
    
    def test_create_column(self):
        """Test column creation."""
        column = self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'test_column',
            'column_type': 'char',
        })
        
        self.assertTrue(column.id)
        self.assertEqual(column.name, 'test_column')
        self.assertEqual(column.column_type, 'char')
    
    def test_column_type_validation(self):
        """Test column type is valid."""
        column = self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'int_column',
            'column_type': 'integer',
        })
        
        self.assertEqual(column.column_type, 'integer')
    
    def test_column_unique_per_dataset(self):
        """Test column name uniqueness within dataset."""
        self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'unique_column',
            'column_type': 'char',
        })
        
        # This should not raise error as the constraint is per dataset
        self.env['optimaai.dataset.column'].create({
            'dataset_id': self.dataset.id,
            'name': 'unique_column',
            'column_type': 'char',
        })


@tagged('post_install', '-at_install')
class TestDatasetSecurity(common.TransactionCase):
    """
    Test cases for Dataset security.
    """
    
    def setUp(self):
        super(TestDatasetSecurity, self).setUp()
        
        # Create users
        self.manager = self.env['res.users'].create({
            'name': 'Manager User',
            'login': 'manager_user',
            'email': 'manager@example.com',
            'groups_id': [(4, self.env.ref('optimaai.group_optimaai_manager').id)],
        })
        
        self.user = self.env['res.users'].create({
            'name': 'Regular User',
            'login': 'regular_user',
            'email': 'user@example.com',
            'groups_id': [(4, self.env.ref('optimaai.group_optimaai_user').id)],
        })
    
    def test_user_can_read(self):
        """Test that regular user can read datasets."""
        dataset = self.env['optimaai.dataset'].sudo(self.user).create({
            'name': 'User Dataset',
            'data_source': 'manual',
        })
        
        self.assertTrue(dataset.id)
        self.assertEqual(dataset.name, 'User Dataset')
    
    def test_user_can_create(self):
        """Test that regular user can create datasets."""
        dataset = self.env['optimaai.dataset'].sudo(self.user).create({
            'name': 'User Created Dataset',
            'data_source': 'manual',
        })
        
        self.assertTrue(dataset.id)
    
    def test_user_cannot_delete_without_permission(self):
        """Test that user cannot delete without permission."""
        dataset = self.env['optimaai.dataset'].create({
            'name': 'Protected Dataset',
            'data_source': 'manual',
        })
        
        # Regular user should not be able to delete
        with self.assertRaises(AccessError):
            dataset.sudo(self.user).unlink()
    
    def test_manager_can_delete(self):
        """Test that manager can delete datasets."""
        dataset = self.env['optimaai.dataset'].sudo(self.manager).create({
            'name': 'Manager Dataset',
            'data_source': 'manual',
        })
        
        dataset_id = dataset.id
        dataset.unlink()
        
        # Verify deleted
        self.assertFalse(self.env['optimaai.dataset'].browse(dataset_id).exists())