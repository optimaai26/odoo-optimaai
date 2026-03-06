# -*- coding: utf-8 -*-
"""
User API Key Model
==================
API key management for users.
Equivalent to Next.js API key management.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import secrets
import hashlib
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ResUsersApiKey(models.Model):
    """API Key for users."""
    
    _name = 'res.users.api.key'
    _description = 'User API Key'
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
    
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True
    )
    
    # Key
    key = fields.Char(
        string='API Key',
        readonly=True,
        copy=False,
        index=True
    )
    
    key_prefix = fields.Char(
        string='Key Prefix',
        readonly=True,
        help='First 8 characters shown for identification'
    )
    
    # Type and Scope
    key_type = fields.Selection([
        ('public', 'Public Key'),
        ('secret', 'Secret Key'),
        ('restricted', 'Restricted Key'),
    ], string='Key Type',
        default='secret',
        required=True
    )
    
    scope = fields.Selection([
        ('full', 'Full Access'),
        ('read', 'Read Only'),
        ('write', 'Write Only'),
        ('custom', 'Custom'),
    ], string='Scope',
        default='full',
        required=True
    )
    
    # Permissions for custom scope
    allowed_models = fields.Text(
        string='Allowed Models',
        widget='json',
        default='[]'
    )
    
    allowed_operations = fields.Selection([
        ('read', 'Read'),
        ('write', 'Read/Write'),
        ('all', 'Full Access'),
    ], string='Allowed Operations',
        default='read'
    )
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ], string='Status',
        default='active',
        tracking=True,
        index=True
    )
    
    # Expiry
    expires = fields.Boolean(
        string='Has Expiry',
        default=False
    )
    
    expiry_date = fields.Datetime(
        string='Expiry Date',
        tracking=True
    )
    
    # Usage tracking
    last_used = fields.Datetime(
        string='Last Used',
        readonly=True
    )
    
    use_count = fields.Integer(
        string='Use Count',
        default=0,
        readonly=True
    )
    
    # Source restrictions
    ip_whitelist = fields.Text(
        string='IP Whitelist',
        widget='json',
        default='[]'
    )
    
    referrer_whitelist = fields.Text(
        string='Referrer Whitelist',
        widget='json',
        default='[]'
    )
    
    # Description
    description = fields.Text(
        string='Description'
    )
    
    # Company
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='user_id.company_id',
        store=True,
        readonly=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # ==========================================
    # Constraints
    # ==========================================
    
    _sql_constraints = [
        ('key_unique', 'UNIQUE(key)', 'API Key must be unique.'),
    ]
    
    # ==========================================
    # Computed Methods
    # ==========================================
    
    @api.depends('key')
    def _compute_key_prefix(self):
        for record in self:
            if record.key:
                record.key_prefix = record.key[:8] + '...'
            else:
                record.key_prefix = False
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    @api.model
    def create(self, vals):
        """Create API key with generated key value."""
        # Generate key if not provided
        if 'key' not in vals:
            vals['key'] = self._generate_key()
        
        # Set key prefix
        if vals.get('key'):
            vals['key_prefix'] = vals['key'][:8] + '...'
        
        return super().create(vals)
    
    def _generate_key(self):
        """Generate a secure API key."""
        # Generate a 32-byte random key
        key = secrets.token_urlsafe(32)
        return f"opt_{key}"
    
    def action_regenerate(self):
        """Regenerate the API key."""
        self.ensure_one()
        
        if self.status != 'active':
            raise UserError(_('Only active keys can be regenerated.'))
        
        # Store old key prefix for logging
        old_prefix = self.key_prefix
        
        # Generate new key
        new_key = self._generate_key()
        
        self.write({
            'key': new_key,
            'key_prefix': new_key[:8] + '...',
        })
        
        _logger.info('API key regenerated: %s -> %s', old_prefix, self.key_prefix)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Regenerated'),
                'message': _('New API key has been generated. Save the key now as it will not be shown again.'),
                'type': 'warning',
            }
        }
    
    def action_revoke(self):
        """Revoke the API key."""
        self.ensure_one()
        
        if self.status == 'revoked':
            raise UserError(_('Key is already revoked.'))
        
        self.status = 'revoked'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Revoked'),
                'message': _('API key has been revoked.'),
                'type': 'warning',
            }
        }
    
    def action_activate(self):
        """Activate a revoked key."""
        self.ensure_one()
        
        if self.status != 'revoked':
            raise UserError(_('Only revoked keys can be reactivated.'))
        
        self.status = 'active'
        return True
    
    def validate_key(self, key):
        """
        Validate an API key.
        
        Args:
            key: The API key to validate
        
        Returns:
            User record if valid, False otherwise
        """
        if not key:
            return False
        
        # Find the key
        api_key = self.search([
            ('key', '=', key),
            ('status', '=', 'active'),
        ], limit=1)
        
        if not api_key:
            return False
        
        # Check expiry
        if api_key.expires and api_key.expiry_date:
            if api_key.expiry_date < datetime.now():
                api_key.status = 'expired'
                return False
        
        # Update usage stats
        api_key.write({
            'last_used': fields.Datetime.now(),
            'use_count': api_key.use_count + 1,
        })
        
        return api_key.user_id
    
    def check_permissions(self, model_name, operation='read'):
        """
        Check if key has permission for operation on model.
        
        Args:
            model_name: Model name to check
            operation: Operation type (read, write, create, unlink)
        
        Returns:
            True if permitted, False otherwise
        """
        self.ensure_one()
        
        if self.status != 'active':
            return False
        
        # Full access scope
        if self.scope == 'full':
            return True
        
        # Read only scope
        if self.scope == 'read' and operation == 'read':
            return True
        
        # Write only scope
        if self.scope == 'write' and operation in ('write', 'create'):
            return True
        
        # Custom scope
        if self.scope == 'custom':
            allowed_models = []
            if self.allowed_models:
                try:
                    allowed_models = json.loads(self.allowed_models)
                except Exception:
                    pass
            
            if model_name not in allowed_models:
                return False
            
            if self.allowed_operations == 'read' and operation != 'read':
                return False
            
            return True
        
        return False
    
    def get_masked_key(self):
        """Get masked version of the key for display."""
        self.ensure_one()
        if not self.key:
            return ''
        return self.key[:8] + '*' * 24
    
    @api.model
    def create_key_for_user(self, user_id, name, scope='full', expiry_days=None):
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            name: Key name
            scope: Access scope
            expiry_days: Days until expiry (None = no expiry)
        
        Returns:
            Created key record
        """
        vals = {
            'name': name,
            'user_id': user_id,
            'scope': scope,
        }
        
        if expiry_days:
            vals['expires'] = True
            vals['expiry_date'] = datetime.now() + timedelta(days=expiry_days)
        
        return self.create(vals)
    
    @api.model
    def get_user_keys(self, user_id=None):
        """Get all API keys for a user."""
        if user_id is None:
            user_id = self.env.user.id
        
        return self.search_read([
            ('user_id', '=', user_id),
            ('active', '=', True),
        ], ['name', 'key_prefix', 'scope', 'status', 'last_used', 'expiry_date'])
    
    # ==========================================
    # Cron Jobs
    # ==========================================
    
    @api.model
    def _cron_expire_keys(self):
        """Expire keys past their expiry date."""
        expired = self.search([
            ('status', '=', 'active'),
            ('expires', '=', True),
            ('expiry_date', '<', datetime.now()),
        ])
        
        expired.write({'status': 'expired'})
        
        _logger.info('Expired %d API keys', len(expired))
    
    @api.model
    def _cron_cleanup_old_revoked(self):
        """Clean up old revoked keys."""
        cleanup_date = datetime.now() - timedelta(days=90)
        
        old_revoked = self.search([
            ('status', '=', 'revoked'),
            ('write_date', '<', cleanup_date),
        ])
        
        old_revoked.unlink()
        
        _logger.info('Cleaned up %d old revoked API keys', len(old_revoked))


import json  # Required at module level