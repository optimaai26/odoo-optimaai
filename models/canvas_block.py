# -*- coding: utf-8 -*-
"""
Canvas Block Model
==================
Individual blocks in the visual canvas.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class CanvasBlock(models.Model):
    """Block in a canvas workflow."""
    
    _name = 'optimaai.canvas.block'
    _description = 'Canvas Block'
    _order = 'canvas_id, sequence'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        required=True
    )
    
    canvas_id = fields.Many2one(
        comodel_name='optimaai.canvas',
        string='Canvas',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Block type
    block_type = fields.Selection([
        # Data blocks
        ('data_source', 'Data Source'),
        ('data_filter', 'Data Filter'),
        ('data_transform', 'Data Transform'),
        ('data_merge', 'Data Merge'),
        ('data_export', 'Data Export'),
        
        # AI blocks
        ('ai_prediction', 'AI Prediction'),
        ('ai_insight', 'AI Insight'),
        ('ai_model', 'AI Model'),
        
        # Integration blocks
        ('integration_api', 'API Call'),
        ('integration_webhook', 'Webhook'),
        ('integration_database', 'Database'),
        
        # Logic blocks
        ('logic_condition', 'Condition'),
        ('logic_loop', 'Loop'),
        ('logic_delay', 'Delay'),
        
        # Output blocks
        ('output_display', 'Display'),
        ('output_report', 'Report'),
        ('output_notification', 'Notification'),
    ], string='Block Type',
        required=True,
        default='data_source'
    )
    
    # Position
    position_x = fields.Float(
        string='Position X',
        default=0
    )
    
    position_y = fields.Float(
        string='Position Y',
        default=0
    )
    
    # Size
    width = fields.Integer(
        string='Width',
        default=200
    )
    
    height = fields.Integer(
        string='Height',
        default=100
    )
    
    # Configuration
    config = fields.Text(
        string='Configuration',
        widget='json',
        default='{}'
    )
    
    # Source references
    dataset_id = fields.Many2one(
        comodel_name='optimaai.dataset',
        string='Dataset'
    )
    
    prediction_id = fields.Many2one(
        comodel_name='optimaai.prediction',
        string='Prediction'
    )
    
    integration_id = fields.Many2one(
        comodel_name='optimaai.integration.config',
        string='Integration'
    )
    
    # Status
    status = fields.Selection([
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Status',
        default='idle'
    )
    
    result_data = fields.Text(
        string='Result Data',
        readonly=True,
        widget='json'
    )
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )
    
    # Visual style
    color = fields.Char(
        string='Color',
        default='#4A90D9'
    )
    
    icon = fields.Char(
        string='Icon',
        default='fa-cube'
    )
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def execute(self, context):
        """
        Execute this block with given context.
        
        Args:
            context: Dictionary with data from previous blocks
        
        Returns:
            Updated context with this block's output
        """
        self.ensure_one()
        
        self.status = 'running'
        
        try:
            # Get handler for this block type
            handler = self._get_handler()
            
            # Execute handler
            result = handler(context)
            
            # Store result
            self.result_data = json.dumps(result, default=str)
            self.status = 'success'
            
            # Update context
            context[f'block_{self.id}'] = result
            
            return result
            
        except Exception as e:
            self.status = 'error'
            self.error_message = str(e)
            _logger.error('Block %s execution failed: %s', self.name, str(e))
            raise
    
    def _get_handler(self):
        """Get the execution handler for this block type."""
        handlers = {
            'data_source': self._handle_data_source,
            'data_filter': self._handle_data_filter,
            'data_transform': self._handle_data_transform,
            'ai_prediction': self._handle_ai_prediction,
            'ai_insight': self._handle_ai_insight,
            'integration_api': self._handle_integration_api,
            'logic_condition': self._handle_logic_condition,
            'output_display': self._handle_output_display,
            'output_notification': self._handle_output_notification,
        }
        
        handler = handlers.get(self.block_type)
        if not handler:
            handler = self._handle_default
        
        return handler
    
    def _handle_data_source(self, context):
        """Handle data source block."""
        if not self.dataset_id:
            raise UserError(_('No dataset configured for data source block.'))
        
        # Return dataset preview/summary
        return {
            'dataset_id': self.dataset_id.id,
            'dataset_name': self.dataset_id.name,
            'row_count': self.dataset_id.row_count,
            'column_count': self.dataset_id.column_count,
            'columns': [{'name': col.name, 'type': col.column_type} 
                       for col in self.dataset_id.column_ids],
        }
    
    def _handle_data_filter(self, context):
        """Handle data filter block."""
        config = json.loads(self.config or '{}')
        
        # Get input from previous block
        input_data = self._get_input_data(context)
        
        # Apply filters (simplified)
        filters = config.get('filters', [])
        
        return {
            'filtered': True,
            'filters_applied': len(filters),
            'input_records': input_data.get('row_count', 0),
        }
    
    def _handle_data_transform(self, context):
        """Handle data transform block."""
        config = json.loads(self.config or '{}')
        
        transforms = config.get('transforms', [])
        
        return {
            'transformed': True,
            'operations': transforms,
        }
    
    def _handle_ai_prediction(self, context):
        """Handle AI prediction block."""
        if not self.prediction_id:
            raise UserError(_('No prediction configured.'))
        
        return {
            'prediction_id': self.prediction_id.id,
            'prediction_name': self.prediction_id.name,
            'confidence': self.prediction_id.result_confidence,
            'status': self.prediction_id.status,
        }
    
    def _handle_ai_insight(self, context):
        """Handle AI insight block."""
        config = json.loads(self.config or '{}')
        
        # Get insights for dataset/prediction
        domain = [('company_id', '=', self.env.company.id)]
        
        if self.dataset_id:
            domain.append(('dataset_id', '=', self.dataset_id.id))
        if self.prediction_id:
            domain.append(('prediction_id', '=', self.prediction_id.id))
        
        insights = self.env['optimaai.insight'].search(domain, limit=10)
        
        return {
            'insight_count': len(insights),
            'insights': [{'title': i.name, 'type': i.insight_type, 'priority': i.priority}
                        for i in insights],
        }
    
    def _handle_integration_api(self, context):
        """Handle API integration block."""
        if not self.integration_id:
            raise UserError(_('No integration configured.'))
        
        # Call the integration
        result = self.integration_id.call_api()
        
        return {
            'integration_id': self.integration_id.id,
            'response_status': result.get('status', 'unknown'),
            'response_data': result.get('data', {}),
        }
    
    def _handle_logic_condition(self, context):
        """Handle conditional logic block."""
        config = json.loads(self.config or '{}')
        
        condition = config.get('condition', {})
        condition_type = condition.get('type', 'always')
        condition_value = condition.get('value')
        
        # Evaluate condition
        if condition_type == 'always':
            result = True
        elif condition_type == 'equals':
            result = self._evaluate_condition(context, condition)
        else:
            result = False
        
        return {
            'condition_met': result,
            'condition_type': condition_type,
        }
    
    def _evaluate_condition(self, context, condition):
        """Evaluate a condition against context."""
        # Simplified condition evaluation
        return True
    
    def _handle_output_display(self, context):
        """Handle display output block."""
        config = json.loads(self.config or '{}')
        
        display_type = config.get('display_type', 'table')
        
        return {
            'display_type': display_type,
            'data': self._get_input_data(context),
        }
    
    def _handle_output_notification(self, context):
        """Handle notification output block."""
        config = json.loads(self.config or '{}')
        
        # Send notification
        message = config.get('message', 'Canvas workflow completed')
        recipients = config.get('recipients', [])
        
        if recipients:
            for user_id in recipients:
                self.env['optimaai.notification.service'].send_notification(
                    user_id=user_id,
                    title=self.name,
                    message=message,
                )
        
        return {
            'notification_sent': True,
            'recipients_count': len(recipients),
        }
    
    def _handle_default(self, context):
        """Default handler for unknown block types."""
        return {
            'block_type': self.block_type,
            'executed': True,
        }
    
    def _get_input_data(self, context):
        """Get input data from connected blocks."""
        # Find connections to this block
        connections = self.env['optimaai.canvas.connection'].search([
            ('target_block_id', '=', self.id),
        ])
        
        if not connections:
            return {}
        
        # Get data from first connected block
        source_block = connections[0].source_block_id
        return context.get(f'block_{source_block.id}', {})
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def get_block_info(self):
        """Get block information for frontend."""
        self.ensure_one()
        
        return {
            'id': self.id,
            'name': self.name,
            'type': self.block_type,
            'position': {'x': self.position_x, 'y': self.position_y},
            'size': {'width': self.width, 'height': self.height},
            'config': json.loads(self.config or '{}'),
            'color': self.color,
            'icon': self.icon,
            'status': self.status,
        }
    
    def update_position(self, x, y):
        """Update block position."""
        self.position_x = x
        self.position_y = y
        return True
    
    def update_config(self, config):
        """Update block configuration."""
        self.config = json.dumps(config)
        return True