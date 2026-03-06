# -*- coding: utf-8 -*-
"""
Dataset Column Model
====================
Stores column metadata for datasets.
"""
from odoo import models, fields, api


class DatasetColumn(models.Model):
    """Column metadata for datasets."""
    
    _name = 'optimaai.dataset.column'
    _description = 'Dataset Column'
    _order = 'dataset_id, sequence, name'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Column Name',
        required=True
    )
    
    dataset_id = fields.Many2one(
        comodel_name='optimaai.dataset',
        string='Dataset',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Column type from pandas dtype
    column_type = fields.Char(
        string='Data Type',
        readonly=True
    )
    
    # Statistics
    null_count = fields.Integer(
        string='Null Count',
        readonly=True,
        default=0
    )
    
    unique_count = fields.Integer(
        string='Unique Values',
        readonly=True,
        default=0
    )
    
    # Computed fields
    null_percentage = fields.Float(
        string='Null Percentage',
        compute='_compute_null_percentage',
        store=True
    )
    
    is_numeric = fields.Boolean(
        string='Is Numeric',
        compute='_compute_is_numeric',
        store=True
    )
    
    # User-defined metadata
    description = fields.Text(
        string='Description'
    )
    
    is_target = fields.Boolean(
        string='Is Target Column',
        default=False,
        help='Mark as target variable for predictions'
    )
    
    is_feature = fields.Boolean(
        string='Is Feature',
        default=True,
        help='Include in prediction features'
    )
    
    # ==========================================
    # Computed Methods
    # ==========================================
    
    @api.depends('null_count', 'dataset_id.row_count')
    def _compute_null_percentage(self):
        for record in self:
            if record.dataset_id.row_count > 0:
                record.null_percentage = (record.null_count / record.dataset_id.row_count) * 100
            else:
                record.null_percentage = 0.0
    
    @api.depends('column_type')
    def _compute_is_numeric(self):
        numeric_types = ['int', 'float', 'int64', 'float64', 'int32', 'float32', 'number']
        for record in self:
            record.is_numeric = any(t in str(record.column_type).lower() for t in numeric_types)
    
    # ==========================================
    # Constraints
    # ==========================================
    
    _sql_constraints = [
        ('name_dataset_unique', 'UNIQUE(name, dataset_id)', 'Column name must be unique within a dataset.'),
    ]