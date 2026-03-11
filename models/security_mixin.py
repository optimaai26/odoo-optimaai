# -*- coding: utf-8 -*-
"""
Security Mixin Classes
======================
Provides permission check helpers similar to hasPermission() hook.
"""
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class OptimaaiSecurityMixin(models.AbstractModel):
    """Mixin providing security utility methods."""
    
    _name = 'optimaai.security.mixin'
    _description = 'Security Mixin'
    
    def check_permission(self, operation='read'):
        """
        Check if current user has permission for operation.
        Similar to hasPermission() hook in Next.js.
        
        Args:
            operation: 'read', 'write', 'create', 'unlink'
        
        Raises:
            AccessError if permission denied
        """
        self.ensure_one()
        
        # Admin always has access
        if self.env.user.has_group('optimaai.group_optimaai_admin'):
            return True
        
        # Manager has access to company records
        if self.env.user.has_group('optimaai.group_optimaai_manager'):
            if hasattr(self, 'company_id'):
                if self.company_id == self.env.company:
                    return True
        
        # Analyst has limited access
        if self.env.user.has_group('optimaai.group_optimaai_analyst'):
            if operation in ('read', 'write', 'create'):
                if hasattr(self, 'company_id'):
                    if self.company_id == self.env.company:
                        return True
        
        # User has read-only access to own records
        if self.env.user.has_group('optimaai.group_optimaai_user'):
            if operation == 'read':
                if hasattr(self, 'uploaded_by'):
                    if self.uploaded_by == self.env.user:
                        return True
                if hasattr(self, 'create_uid'):
                    if self.create_uid == self.env.user:
                        return True
        
        raise AccessError(_(
            'You do not have permission to %s this record.'
        ) % operation)
    
    def can_read(self):
        """Check read permission."""
        return self._check_permission_safe('read')
    
    def can_write(self):
        """Check write permission."""
        return self._check_permission_safe('write')
    
    def can_delete(self):
        """Check delete permission."""
        return self._check_permission_safe('unlink')
    
    def _check_permission_safe(self, operation):
        """Safe permission check (returns bool instead of raising)."""
        try:
            self.check_permission(operation)
            return True
        except AccessError:
            return False


class OwnRecordMixin(models.AbstractModel):
    """Mixin for models where users can only access their own records."""
    
    _name = 'optimaai.own.record.mixin'
    _description = 'Own Record Mixin'
    
    @api.model
    def create(self, vals):
        """Auto-assign owner on creation."""
        if 'uploaded_by' in self._fields and 'uploaded_by' not in vals:
            vals['uploaded_by'] = self.env.user.id
        return super().create(vals)
    
    def read(self, fields=None, load='_classic_read'):
        """Check ownership on read."""
        result = super().read(fields, load)
        for record in self:
            if not self._is_own_record(record):
                # Filter out records user doesn't own
                if record.id in [r['id'] for r in result]:
                    result = [r for r in result if r['id'] != record.id]
        return result
    
    def _is_own_record(self, record):
        """Check if record belongs to current user."""
        if self.env.user.has_group('optimaai.group_optimaai_manager'):
            return True
        if hasattr(record, 'uploaded_by'):
            return record.uploaded_by == self.env.user
        if hasattr(record, 'create_uid'):
            return record.create_uid == self.env.user
        return False


class CompanyRecordMixin(models.AbstractModel):
    """Mixin for multi-company record isolation."""
    
    _name = 'optimaai.company.record.mixin'
    _description = 'Company Record Mixin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    @api.model
    def create(self, vals):
        """Auto-assign company on creation."""
        if 'company_id' not in vals:
            vals['company_id'] = self.env.company.id
        return super().create(vals)
    
    def _check_company_access(self):
        """Verify user has access to record's company."""
        self.ensure_one()
        if self.company_id not in self.env.user.company_ids:
            raise AccessError(_(
                'You do not have access to records from company %s.'
            ) % self.company_id.name)