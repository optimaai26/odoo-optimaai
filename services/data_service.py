# -*- coding: utf-8 -*-
"""
Data Service
============
Centralized data management service.
Handles data import, export, validation, and transformation.

TODO: This service is not yet integrated with any model or controller.
      It contains useful import/export/transform logic for CSV, JSON, Excel.
      Wire it into dataset.py or a controller endpoint when ready.
"""
from odoo import models, api, _, fields
from odoo.exceptions import UserError, ValidationError
import json
import base64
import csv
import io
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class DataService(models.AbstractModel):
    """Data service for dataset operations."""
    
    _name = 'optimaai.data.service'
    _description = 'Data Service'
    
    # ==========================================
    # Import Methods
    # ==========================================
    
    @api.model
    def import_csv(self, dataset_id, file_data, file_name=None):
        """
        Import CSV data into a dataset.
        
        Args:
            dataset_id: Dataset record ID
            file_data: Base64 encoded CSV file
            file_name: Original file name
        
        Returns:
            Dictionary with import results
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        try:
            # Decode file data
            data = base64.b64decode(file_data)
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(data.decode('utf-8')))
            
            columns = csv_reader.fieldnames or []
            rows = list(csv_reader)
            
            # Update dataset
            dataset.write({
                'data_raw': json.dumps(rows[:1000]),  # Store first 1000 rows
                'data_summary': json.dumps({
                    'columns': columns,
                    'row_count': len(rows),
                    'preview_rows': rows[:5],
                }),
                'row_count': len(rows),
                'file_size': len(data),
                'import_date': fields.Datetime.now(),
            })
            
            # Create column records
            self._create_column_records(dataset, columns, rows)
            
            return {
                'success': True,
                'row_count': len(rows),
                'columns': columns,
            }
            
        except Exception as e:
            _logger.error('Failed to import CSV: %s', str(e))
            raise UserError(_('Failed to import CSV: %s') % str(e))
    
    @api.model
    def import_json(self, dataset_id, file_data, file_name=None):
        """
        Import JSON data into a dataset.
        
        Args:
            dataset_id: Dataset record ID
            file_data: Base64 encoded JSON file
            file_name: Original file name
        
        Returns:
            Dictionary with import results
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        try:
            # Decode and parse JSON
            data = base64.b64decode(file_data)
            json_data = json.loads(data.decode('utf-8'))
            
            # Normalize to list of records
            if isinstance(json_data, dict):
                if 'data' in json_data:
                    json_data = json_data['data']
                else:
                    json_data = [json_data]
            
            if not isinstance(json_data, list):
                raise UserError(_('Invalid JSON format. Expected array of objects.'))
            
            # Extract columns from first record
            columns = list(json_data[0].keys()) if json_data else []
            
            # Update dataset
            dataset.write({
                'data_raw': json.dumps(json_data[:1000]),
                'data_summary': json.dumps({
                    'columns': columns,
                    'row_count': len(json_data),
                    'preview_rows': json_data[:5],
                }),
                'row_count': len(json_data),
                'file_size': len(data),
                'import_date': fields.Datetime.now(),
            })
            
            # Create column records
            self._create_column_records(dataset, columns, json_data)
            
            return {
                'success': True,
                'row_count': len(json_data),
                'columns': columns,
            }
            
        except json.JSONDecodeError as e:
            raise UserError(_('Invalid JSON format: %s') % str(e))
        except Exception as e:
            _logger.error('Failed to import JSON: %s', str(e))
            raise UserError(_('Failed to import JSON: %s') % str(e))
    
    @api.model
    def import_excel(self, dataset_id, file_data, file_name=None, sheet_name=None):
        """
        Import Excel data into a dataset.
        
        Args:
            dataset_id: Dataset record ID
            file_data: Base64 encoded Excel file
            file_name: Original file name
            sheet_name: Sheet name to import
        
        Returns:
            Dictionary with import results
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        try:
            import openpyxl
            
            # Decode and load workbook
            data = base64.b64decode(file_data)
            workbook = openpyxl.load_workbook(io.BytesIO(data))
            
            # Select sheet
            if sheet_name:
                sheet = workbook[sheet_name]
            else:
                sheet = workbook.active
            
            # Read data
            rows = list(sheet.values)
            
            if not rows:
                raise UserError(_('Excel file is empty.'))
            
            # First row is header
            columns = [str(c) if c else f'column_{i}' for i, c in enumerate(rows[0])]
            
            # Convert to list of dicts
            records = []
            for row in rows[1:]:
                record = {}
                for i, value in enumerate(row):
                    record[columns[i]] = value
                records.append(record)
            
            # Update dataset
            dataset.write({
                'data_raw': json.dumps(records[:1000], default=str),
                'data_summary': json.dumps({
                    'columns': columns,
                    'row_count': len(records),
                    'preview_rows': records[:5],
                }),
                'row_count': len(records),
                'file_size': len(data),
                'import_date': fields.Datetime.now(),
            })
            
            # Create column records
            self._create_column_records(dataset, columns, records)
            
            return {
                'success': True,
                'row_count': len(records),
                'columns': columns,
            }
            
        except ImportError:
            raise UserError(_('openpyxl library not installed. Please install it to import Excel files.'))
        except Exception as e:
            _logger.error('Failed to import Excel: %s', str(e))
            raise UserError(_('Failed to import Excel: %s') % str(e))
    
    @api.model
    def _create_column_records(self, dataset, columns, sample_data):
        """Create column records for dataset."""
        column_model = self.env['optimaai.dataset.column']
        
        # Remove existing columns
        column_model.search([('dataset_id', '=', dataset.id)]).unlink()
        
        # Analyze and create new columns
        for col_name in columns:
            col_type = self._infer_column_type(col_name, sample_data)
            col_values = self._analyze_column_values(col_name, sample_data)
            
            column_model.create({
                'dataset_id': dataset.id,
                'name': col_name,
                'column_type': col_type,
                'missing_count': col_values.get('missing_count', 0),
                'unique_count': col_values.get('unique_count', 0),
                'statistics': json.dumps(col_values),
            })
    
    @api.model
    def _infer_column_type(self, column_name, sample_data):
        """Infer the data type of a column."""
        if not sample_data:
            return 'text'
        
        # Sample first 100 values
        values = [row.get(column_name) for row in sample_data[:100] if row.get(column_name) is not None]
        
        if not values:
            return 'text'
        
        # Check for numeric
        try:
            [float(v) for v in values]
            return 'numeric'
        except (ValueError, TypeError):
            pass
        
        # Check for boolean
        bool_values = {'true', 'false', 'yes', 'no', '1', '0'}
        if str(values[0]).lower() in bool_values:
            if all(str(v).lower() in bool_values for v in values):
                return 'boolean'
        
        # Check for date
        try:
            datetime.strptime(str(values[0]), '%Y-%m-%d')
            return 'date'
        except ValueError:
            pass
        
        # Check for datetime
        try:
            datetime.strptime(str(values[0]), '%Y-%m-%d %H:%M:%S')
            return 'datetime'
        except ValueError:
            pass
        
        return 'text'
    
    @api.model
    def _analyze_column_values(self, column_name, sample_data):
        """Analyze column values for statistics."""
        values = [row.get(column_name) for row in sample_data]
        
        non_null = [v for v in values if v is not None and v != '']
        unique_values = set(str(v) for v in non_null)
        
        stats = {
            'total_count': len(values),
            'missing_count': len(values) - len(non_null),
            'unique_count': len(unique_values),
        }
        
        return stats
    
    # ==========================================
    # Export Methods
    # ==========================================
    
    @api.model
    def export_csv(self, dataset_id, columns=None):
        """
        Export dataset to CSV.
        
        Args:
            dataset_id: Dataset record ID
            columns: List of columns to export (all if None)
        
        Returns:
            Base64 encoded CSV data
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        data = json.loads(dataset.data_raw) if dataset.data_raw else []
        
        if not data:
            raise UserError(_('Dataset is empty.'))
        
        # Determine columns
        if not columns:
            columns = list(data[0].keys()) if data else []
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
        
        csv_data = output.getvalue().encode('utf-8')
        
        return {
            'file_data': base64.b64encode(csv_data).decode('utf-8'),
            'file_name': f'{dataset.name}.csv',
            'mime_type': 'text/csv',
        }
    
    @api.model
    def export_json(self, dataset_id):
        """
        Export dataset to JSON.
        
        Args:
            dataset_id: Dataset record ID
        
        Returns:
            Base64 encoded JSON data
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        data = json.loads(dataset.data_raw) if dataset.data_raw else []
        
        json_data = json.dumps(data, indent=2, default=str).encode('utf-8')
        
        return {
            'file_data': base64.b64encode(json_data).decode('utf-8'),
            'file_name': f'{dataset.name}.json',
            'mime_type': 'application/json',
        }
    
    # ==========================================
    # Data Transformation Methods
    # ==========================================
    
    @api.model
    def validate_data(self, dataset_id):
        """
        Validate dataset data quality.
        
        Args:
            dataset_id: Dataset record ID
        
        Returns:
            Dictionary with validation results
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        data = json.loads(dataset.data_raw) if dataset.data_raw else []
        columns = dataset.column_ids
        
        issues = []
        stats = {
            'total_rows': len(data),
            'total_columns': len(columns),
            'complete_rows': 0,
            'missing_cells': 0,
        }
        
        # Check each row
        for i, row in enumerate(data):
            row_complete = True
            for col in columns:
                if col.required and not row.get(col.name):
                    issues.append({
                        'type': 'missing_required',
                        'row': i + 1,
                        'column': col.name,
                        'message': f"Missing required value in column '{col.name}'",
                    })
                    row_complete = False
                if not row.get(col.name):
                    stats['missing_cells'] += 1
            if row_complete:
                stats['complete_rows'] += 1
        
        # Calculate quality score
        total_cells = stats['total_rows'] * stats['total_columns'] if stats['total_rows'] > 0 else 0
        stats['quality_score'] = round((total_cells - stats['missing_cells']) / total_cells * 100, 2) if total_cells > 0 else 0
        stats['completeness_rate'] = round(stats['complete_rows'] / stats['total_rows'] * 100, 2) if stats['total_rows'] > 0 else 0
        
        return {
            'stats': stats,
            'issues': issues[:100],  # Limit to 100 issues
            'issue_count': len(issues),
        }
    
    @api.model
    def transform_data(self, dataset_id, transformations):
        """
        Apply transformations to dataset.
        
        Args:
            dataset_id: Dataset record ID
            transformations: List of transformation steps
        
        Returns:
            Dictionary with transformation results
        """
        dataset = self.env['optimaai.dataset'].browse(dataset_id)
        if not dataset.exists():
            raise UserError(_('Dataset not found.'))
        
        data = json.loads(dataset.data_raw) if dataset.data_raw else []
        
        for transform in transformations:
            transform_type = transform.get('type')
            
            if transform_type == 'rename_column':
                data = self._transform_rename_column(data, transform)
            elif transform_type == 'drop_column':
                data = self._transform_drop_column(data, transform)
            elif transform_type == 'fill_missing':
                data = self._transform_fill_missing(data, transform)
            elif transform_type == 'filter_rows':
                data = self._transform_filter_rows(data, transform)
            elif transform_type == 'sort':
                data = self._transform_sort(data, transform)
            elif transform_type == 'calculate':
                data = self._transform_calculate(data, transform)
        
        # Update dataset
        dataset.write({
            'data_raw': json.dumps(data[:1000]),
            'row_count': len(data),
        })
        
        return {
            'success': True,
            'row_count': len(data),
        }
    
    def _transform_rename_column(self, data, transform):
        """Rename a column."""
        old_name = transform.get('old_name')
        new_name = transform.get('new_name')
        
        for row in data:
            if old_name in row:
                row[new_name] = row.pop(old_name)
        
        return data
    
    def _transform_drop_column(self, data, transform):
        """Drop columns from dataset."""
        columns = transform.get('columns', [])
        
        for row in data:
            for col in columns:
                row.pop(col, None)
        
        return data
    
    def _transform_fill_missing(self, data, transform):
        """Fill missing values."""
        column = transform.get('column')
        value = transform.get('value')
        method = transform.get('method', 'value')
        
        if method == 'value':
            for row in data:
                if row.get(column) is None or row.get(column) == '':
                    row[column] = value
        elif method == 'mean':
            values = [float(row[column]) for row in data if row.get(column) is not None]
            mean_val = sum(values) / len(values) if values else 0
            for row in data:
                if row.get(column) is None or row.get(column) == '':
                    row[column] = mean_val
        
        return data
    
    def _transform_filter_rows(self, data, transform):
        """Filter rows based on condition."""
        column = transform.get('column')
        operator = transform.get('operator')
        value = transform.get('value')
        
        filtered_data = []
        for row in data:
            row_val = row.get(column)
            include = False
            
            if operator == 'eq':
                include = row_val == value
            elif operator == 'ne':
                include = row_val != value
            elif operator == 'gt':
                include = row_val > value
            elif operator == 'lt':
                include = row_val < value
            elif operator == 'contains':
                include = value in str(row_val) if row_val else False
            elif operator == 'is_null':
                include = row_val is None or row_val == ''
            elif operator == 'is_not_null':
                include = row_val is not None and row_val != ''
            
            if include:
                filtered_data.append(row)
        
        return filtered_data
    
    def _transform_sort(self, data, transform):
        """Sort data by column."""
        column = transform.get('column')
        reverse = transform.get('reverse', False)
        
        return sorted(data, key=lambda x: (x.get(column) is None, x.get(column)), reverse=reverse)
    
    def _transform_calculate(self, data, transform):
        """Calculate new column from existing columns."""
        new_column = transform.get('new_column')
        formula = transform.get('formula')
        columns = transform.get('columns', [])
        
        for row in data:
            if formula == 'sum':
                row[new_column] = sum(row.get(col, 0) or 0 for col in columns)
            elif formula == 'avg':
                values = [row.get(col) for col in columns if row.get(col) is not None]
                row[new_column] = sum(values) / len(values) if values else 0
            elif formula == 'multiply':
                result = 1
                for col in columns:
                    result *= row.get(col, 1) or 1
                row[new_column] = result
            elif formula == 'concat':
                row[new_column] = ''.join(str(row.get(col, '')) for col in columns)
        
        return data