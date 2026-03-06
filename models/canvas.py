# -*- coding: utf-8 -*-
"""
Canvas Model
============
Visual canvas for building AI workflows.
Equivalent to Next.js canvas page.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Canvas(models.Model):
    """Visual canvas for workflow building."""
    
    _name = 'optimaai.canvas'
    _description = 'Canvas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    # Canvas configuration
    canvas_type = fields.Selection([
        ('prediction', 'Prediction Workflow'),
        ('analysis', 'Data Analysis'),
        ('integration', 'Integration Flow'),
        ('custom', 'Custom Canvas'),
    ], string='Type',
        default='custom',
        required=True,
        tracking=True
    )
    
    # Layout
    zoom_level = fields.Float(
        string='Zoom Level',
        default=1.0
    )
    
    pan_offset_x = fields.Float(
        string='Pan Offset X',
        default=0
    )
    
    pan_offset_y = fields.Float(
        string='Pan Offset Y',
        default=0
    )
    
    grid_enabled = fields.Boolean(
        string='Show Grid',
        default=True
    )
    
    snap_to_grid = fields.Boolean(
        string='Snap to Grid',
        default=True
    )
    
    # Relationships
    block_ids = fields.One2many(
        comodel_name='optimaai.canvas.block',
        inverse_name='canvas_id',
        string='Blocks'
    )
    
    connection_ids = fields.One2many(
        comodel_name='optimaai.canvas.connection',
        inverse_name='canvas_id',
        string='Connections'
    )
    
    # Execution
    status = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ], string='Status',
        default='draft',
        tracking=True
    )
    
    last_run_date = fields.Datetime(
        string='Last Run',
        readonly=True
    )
    
    last_run_duration = fields.Integer(
        string='Last Run Duration (ms)',
        readonly=True
    )
    
    # Ownership
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    created_by = fields.Many2one(
        comodel_name='res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_run(self):
        """Execute the canvas workflow."""
        self.ensure_one()
        
        if self.status == 'running':
            raise UserError(_('Canvas is already running.'))
        
        self.status = 'running'
        
        # Execute async
        self.with_delay()._execute_canvas()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Canvas Execution'),
                'message': _('Canvas workflow started.'),
                'type': 'info',
            }
        }
    
    def _execute_canvas(self):
        """Execute the canvas workflow blocks."""
        import time
        start_time = time.time()
        
        try:
            # Get blocks in execution order (topological sort)
            ordered_blocks = self._get_execution_order()
            
            # Execute each block
            context = {}
            for block in ordered_blocks:
                block.execute(context)
            
            self.status = 'completed'
            self.last_run_date = fields.Datetime.now()
            self.last_run_duration = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            self.status = 'error'
            _logger.error('Canvas execution failed: %s', str(e))
    
    def _get_execution_order(self):
        """Get blocks in execution order using topological sort."""
        blocks = self.block_ids
        connections = self.connection_ids
        
        # Build dependency graph
        dependencies = {block.id: set() for block in blocks}
        for conn in connections:
            if conn.target_block_id.id in dependencies:
                dependencies[conn.target_block_id.id].add(conn.source_block_id.id)
        
        # Topological sort
        ordered = []
        visited = set()
        
        def visit(block_id):
            if block_id in visited:
                return
            visited.add(block_id)
            for dep_id in dependencies[block_id]:
                visit(dep_id)
            ordered.append(block_id)
        
        for block_id in dependencies:
            visit(block_id)
        
        return blocks.filtered(lambda b: b.id in ordered)
    
    def action_save_layout(self, layout_data):
        """Save canvas layout."""
        self.ensure_one()
        
        # Update zoom and pan
        if 'zoom' in layout_data:
            self.zoom_level = layout_data['zoom']
        if 'pan' in layout_data:
            self.pan_offset_x = layout_data['pan'].get('x', 0)
            self.pan_offset_y = layout_data['pan'].get('y', 0)
        
        return True
    
    def action_clear(self):
        """Clear all blocks from canvas."""
        self.ensure_one()
        self.block_ids.unlink()
        self.connection_ids.unlink()
        return True
    
    def action_duplicate(self):
        """Duplicate the canvas."""
        self.ensure_one()
        
        new_canvas = self.copy({
            'name': _('%s (Copy)') % self.name,
            'status': 'draft',
            'last_run_date': False,
            'last_run_duration': 0,
        })
        
        # Copy blocks
        block_mapping = {}
        for block in self.block_ids:
            new_block = block.copy({
                'canvas_id': new_canvas.id,
            })
            block_mapping[block.id] = new_block.id
        
        # Copy connections
        for conn in self.connection_ids:
            conn.copy({
                'canvas_id': new_canvas.id,
                'source_block_id': block_mapping.get(conn.source_block_id.id),
                'target_block_id': block_mapping.get(conn.target_block_id.id),
            })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': new_canvas.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CanvasConnection(models.Model):
    """Connection between canvas blocks."""
    
    _name = 'optimaai.canvas.connection'
    _description = 'Canvas Connection'
    
    canvas_id = fields.Many2one(
        comodel_name='optimaai.canvas',
        string='Canvas',
        required=True,
        ondelete='cascade'
    )
    
    source_block_id = fields.Many2one(
        comodel_name='optimaai.canvas.block',
        string='Source Block',
        required=True,
        ondelete='cascade'
    )
    
    source_port = fields.Char(
        string='Source Port',
        default='output'
    )
    
    target_block_id = fields.Many2one(
        comodel_name='optimaai.canvas.block',
        string='Target Block',
        required=True,
        ondelete='cascade'
    )
    
    target_port = fields.Char(
        string='Target Port',
        default='input'
    )
    
    # Visual properties
    color = fields.Char(
        string='Color',
        default='#666666'
    )