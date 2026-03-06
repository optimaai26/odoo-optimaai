# -*- coding: utf-8 -*-
"""
Canvas Connection Model
=======================
Connections between blocks in the visual canvas.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CanvasConnection(models.Model):
    """Connection between canvas blocks."""
    
    _name = 'optimaai.canvas.connection'
    _description = 'Canvas Connection'
    _order = 'canvas_id, sequence'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True
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
    
    # Source block
    source_block_id = fields.Many2one(
        comodel_name='optimaai.canvas.block',
        string='Source Block',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    source_port = fields.Char(
        string='Source Port',
        default='output',
        help='Output port name on source block'
    )
    
    # Target block
    target_block_id = fields.Many2one(
        comodel_name='optimaai.canvas.block',
        string='Target Block',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    target_port = fields.Char(
        string='Target Port',
        default='input',
        help='Input port name on target block'
    )
    
    # Connection properties
    connection_type = fields.Selection([
        ('data', 'Data Flow'),
        ('trigger', 'Trigger'),
        ('condition', 'Conditional'),
        ('error', 'Error Handler'),
    ], string='Connection Type',
        default='data'
    )
    
    # Condition for conditional connections
    condition = fields.Text(
        string='Condition',
        widget='json'
    )
    
    # Label shown on connection line
    label = fields.Char(
        string='Label'
    )
    
    # Visual style
    color = fields.Char(
        string='Color',
        default='#666666'
    )
    
    line_style = fields.Selection([
        ('solid', 'Solid'),
        ('dashed', 'Dashed'),
        ('dotted', 'Dotted'),
    ], string='Line Style',
        default='solid'
    )
    
    animated = fields.Boolean(
        string='Animated',
        default=False,
        help='Show animation for data flow'
    )
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ], string='Status',
        default='active'
    )
    
    last_data_transfer = fields.Datetime(
        string='Last Data Transfer',
        readonly=True
    )
    
    transfer_count = fields.Integer(
        string='Transfer Count',
        default=0,
        readonly=True
    )
    
    # Company
    company_id = fields.Many2one(
        related='canvas_id.company_id',
        store=True,
        readonly=True
    )
    
    # ==========================================
    # Constraints
    # ==========================================
    
    _sql_constraints = [
        ('connection_unique', 
         'UNIQUE(source_block_id, source_port, target_block_id, target_port)',
         'Connection must be unique.'),
    ]
    
    # ==========================================
    # Computed Methods
    # ==========================================
    
    @api.depends('source_block_id.name', 'target_block_id.name')
    def _compute_name(self):
        for record in self:
            source = record.source_block_id.name or 'Unknown'
            target = record.target_block_id.name or 'Unknown'
            record.name = f"{source} → {target}"
    
    # ==========================================
    # Constraints
    # ==========================================
    
    @api.constrains('source_block_id', 'target_block_id')
    def _check_blocks(self):
        for record in self:
            # Blocks must be in same canvas
            if record.source_block_id.canvas_id != record.canvas_id:
                raise UserError(_('Source block must be in the same canvas.'))
            if record.target_block_id.canvas_id != record.canvas_id:
                raise UserError(_('Target block must be in the same canvas.'))
            
            # Cannot connect to itself
            if record.source_block_id == record.target_block_id:
                raise UserError(_('Cannot connect a block to itself.'))
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def transfer_data(self, data):
        """
        Transfer data through this connection.
        
        Args:
            data: Data to transfer
        
        Returns:
            Transformed data after applying any mappings
        """
        self.ensure_one()
        
        # Apply any data transformation
        transformed_data = self._transform_data(data)
        
        # Update statistics
        self.write({
            'last_data_transfer': fields.Datetime.now(),
            'transfer_count': self.transfer_count + 1,
        })
        
        return transformed_data
    
    def _transform_data(self, data):
        """Transform data based on connection configuration."""
        # For conditional connections, evaluate condition
        if self.connection_type == 'condition' and self.condition:
            if not self._evaluate_condition(data):
                return None
        
        return data
    
    def _evaluate_condition(self, data):
        """Evaluate condition for conditional connection."""
        # Simplified condition evaluation
        # Would be extended with proper expression evaluation
        return True
    
    def get_connection_info(self):
        """Get connection information for frontend."""
        self.ensure_one()
        
        return {
            'id': self.id,
            'name': self.name,
            'source': {
                'block_id': self.source_block_id.id,
                'port': self.source_port,
            },
            'target': {
                'block_id': self.target_block_id.id,
                'port': self.target_port,
            },
            'type': self.connection_type,
            'label': self.label,
            'color': self.color,
            'line_style': self.line_style,
            'animated': self.animated,
        }
    
    @api.model
    def create_connection(self, canvas_id, source_block_id, target_block_id, 
                          source_port='output', target_port='input', **kwargs):
        """
        Create a new connection.
        
        Args:
            canvas_id: Canvas ID
            source_block_id: Source block ID
            target_block_id: Target block ID
            source_port: Source port name
            target_port: Target port name
            **kwargs: Additional connection properties
        
        Returns:
            Created connection record
        """
        return self.create({
            'canvas_id': canvas_id,
            'source_block_id': source_block_id,
            'target_block_id': target_block_id,
            'source_port': source_port,
            'target_port': target_port,
            **kwargs
        })
    
    def action_activate(self):
        """Activate the connection."""
        self.status = 'active'
        return True
    
    def action_deactivate(self):
        """Deactivate the connection."""
        self.status = 'inactive'
        return True