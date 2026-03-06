# -*- coding: utf-8 -*-
"""
Dataset Model
=============
Manages uploaded datasets for analysis.
Equivalent to Next.js Dataset type and datasets page.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import json
import logging

_logger = logging.getLogger(__name__)


class Dataset(models.Model):
    """Dataset model for data management."""
    
    _name = 'optimaai.dataset'
    _description = 'Dataset'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'optimaai.security.mixin']
    _order = 'create_date desc'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    # File storage
    file_name = fields.Char(
        string='Filename',
        readonly=True
    )
    file_data = fields.Binary(
        string='File Data',
        attachment=True
    )
    file_size = fields.Integer(
        string='File Size (bytes)',
        readonly=True
    )
    
    # Statistics
    row_count = fields.Integer(
        string='Row Count',
        readonly=True,
        default=0
    )
    column_count = fields.Integer(
        string='Column Count',
        readonly=True,
        default=0
    )
    
    # Status
    status = fields.Selection([
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ], string='Status',
        default='uploading',
        tracking=True,
        index=True
    )
    
    # Quality metrics
    quality_score = fields.Integer(
        string='Quality Score',
        readonly=True,
        default=0,
        help='Data quality score from 0-100'
    )
    null_percentage = fields.Float(
        string='Null Percentage',
        readonly=True,
        default=0.0,
        help='Percentage of null values in the dataset'
    )
    duplicate_count = fields.Integer(
        string='Duplicate Rows',
        readonly=True,
        default=0
    )
    
    # Relationships
    column_ids = fields.One2many(
        comodel_name='optimaai.dataset.column',
        inverse_name='dataset_id',
        string='Columns'
    )
    prediction_ids = fields.One2many(
        comodel_name='optimaai.prediction',
        inverse_name='dataset_id',
        string='Predictions'
    )
    insight_ids = fields.One2many(
        comodel_name='optimaai.insight',
        inverse_name='dataset_id',
        string='Insights'
    )
    
    # Metadata
    description = fields.Text(
        string='Description'
    )
    tags = fields.Char(
        string='Tags',
        help='Comma-separated tags'
    )
    
    # Ownership
    uploaded_by = fields.Many2one(
        comodel_name='res.users',
        string='Uploaded By',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    # Processing
    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )
    processed_date = fields.Datetime(
        string='Processed Date',
        readonly=True
    )
    
    # Preview data (first N rows)
    preview_data = fields.Text(
        string='Preview Data',
        readonly=True,
        widget='json'
    )
    
    # Active for archiving
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # ==========================================
    # Constraints
    # ==========================================
    
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name, company_id)', 'Dataset name must be unique per company.'),
    ]
    
    # ==========================================
    # CRUD Methods
    # ==========================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Create datasets and trigger processing."""
        datasets = super().create(vals_list)
        
        for dataset in datasets:
            if dataset.file_data:
                dataset.with_delay()._process_file()
        
        return datasets
    
    def unlink(self):
        """Prevent deletion if predictions exist."""
        for dataset in self:
            if dataset.prediction_ids:
                raise UserError(_(
                    'Cannot delete dataset "%s" because it has associated predictions. '
                    'Archive it instead or delete predictions first.'
                ) % dataset.name)
        return super().unlink()
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_process(self):
        """Manually trigger dataset processing."""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_('No file data to process.'))
        
        self.status = 'processing'
        self._process_file()
    
    def _process_file(self):
        """
        Process the uploaded file.
        Analyzes structure, calculates statistics.
        """
        self.ensure_one()
        
        try:
            import pandas as pd
            import io
            
            # Decode file
            content = base64.b64decode(self.file_data)
            
            # Parse based on file type
            if self.file_name and self.file_name.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content))
            elif self.file_name and self.file_name.endswith('.json'):
                df = pd.read_json(io.BytesIO(content))
            elif self.file_name and self.file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise UserError(_('Unsupported file format: %s') % self.file_name)
            
            # Update statistics
            self.row_count = len(df)
            self.column_count = len(df.columns)
            
            # Calculate quality metrics
            null_count = df.isnull().sum().sum()
            total_cells = self.row_count * self.column_count
            self.null_percentage = (null_count / total_cells * 100) if total_cells > 0 else 0
            
            self.duplicate_count = int(df.duplicated().sum())
            
            # Quality score calculation
            self.quality_score = max(0, 100 - int(self.null_percentage) - int(self.duplicate_count / max(1, self.row_count) * 100))
            
            # Create column records
            self.column_ids.unlink()  # Remove existing columns
            for col_name in df.columns:
                self.env['optimaai.dataset.column'].create({
                    'dataset_id': self.id,
                    'name': str(col_name),
                    'column_type': str(df[col_name].dtype),
                    'null_count': int(df[col_name].isnull().sum()),
                    'unique_count': int(df[col_name].nunique()),
                })
            
            # Store preview data (first 10 rows)
            self.preview_data = df.head(10).to_json(orient='records')
            
            # Update status
            self.status = 'ready'
            self.processed_date = fields.Datetime.now()
            
            _logger.info('Dataset %s processed successfully: %d rows, %d columns', 
                        self.name, self.row_count, self.column_count)
            
        except Exception as e:
            self.status = 'error'
            self.error_message = str(e)
            _logger.error('Failed to process dataset %s: %s', self.name, str(e))
    
    def action_archive(self):
        """Archive the dataset."""
        self.ensure_one()
        return self.write({'active': False})
    
    def action_download(self):
        """Download the dataset file."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/optimaai/dataset/{self.id}/download',
            'target': 'self',
        }
    
    # ==========================================
    # Dashboard Methods
    # ==========================================
    
    @api.model
    def get_dashboard_stats(self):
        """Get statistics for dashboard display."""
        domain = [('company_id', '=', self.env.company.id)]
        
        return {
            'total': self.search_count(domain),
            'ready': self.search_count(domain + [('status', '=', 'ready')]),
            'processing': self.search_count(domain + [('status', '=', 'processing')]),
            'error': self.search_count(domain + [('status', '=', 'error')]),
            'total_rows': sum(self.search(domain).mapped('row_count')),
            'total_columns': sum(self.search(domain).mapped('column_count')),
        }