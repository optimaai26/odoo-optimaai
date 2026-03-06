# -*- coding: utf-8 -*-
"""
Access Request Model
====================
Request access system for restricted resources.
Equivalent to Next.js RequestAccessModal component.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccessRequest(models.Model):
    """Access request model."""
    
    _name = 'optimaai.access.request'
    _description = 'Access Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )
    
    # Requester
    requester_id = fields.Many2one(
        comodel_name='res.users',
        string='Requester',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True
    )
    
    # Target resource
    resource_model = fields.Char(
        string='Resource Model',
        required=True
    )
    
    resource_id = fields.Integer(
        string='Resource ID',
        required=True
    )
    
    resource_ref = fields.Char(
        string='Resource Reference',
        compute='_compute_resource_ref'
    )
    
    # Request details
    access_type = fields.Selection([
        ('read', 'Read Access'),
        ('write', 'Write Access'),
        ('delete', 'Delete Access'),
        ('admin', 'Admin Access'),
    ], string='Access Type',
        default='read',
        required=True
    )
    
    reason = fields.Text(
        string='Reason',
        required=True
    )
    
    justification = fields.Text(
        string='Business Justification'
    )
    
    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status',
        default='pending',
        tracking=True,
        index=True
    )
    
    # Approval
    approver_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver',
        tracking=True
    )
    
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason'
    )
    
    # Expiry
    expiry_date = fields.Datetime(
        string='Expiry Date'
    )
    
    # Duration requested
    duration_days = fields.Integer(
        string='Duration (Days)',
        default=30
    )
    
    # Company
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    # ==========================================
    # Computed Methods
    # ==========================================
    
    @api.depends('resource_model', 'resource_id')
    def _compute_resource_ref(self):
        for record in self:
            if record.resource_model and record.resource_id:
                try:
                    model = self.env[record.resource_model]
                    if model._rec_name:
                        rec = model.browse(record.resource_id)
                        record.resource_ref = rec.display_name
                    else:
                        record.resource_ref = f"{record.resource_model}#{record.resource_id}"
                except Exception:
                    record.resource_ref = f"{record.resource_model}#{record.resource_id}"
            else:
                record.resource_ref = False
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_approve(self):
        """Approve the access request."""
        self.ensure_one()
        
        if self.status != 'pending':
            raise UserError(_('Only pending requests can be approved.'))
        
        # Update status
        self.write({
            'status': 'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'expiry_date': fields.Datetime.add(fields.Datetime.now(), days=self.duration_days),
        })
        
        # Grant access (add user to appropriate group)
        self._grant_access()
        
        # Notify requester
        self._notify_requester('approved')
        
        return True
    
    def action_reject(self, reason=None):
        """Reject the access request."""
        self.ensure_one()
        
        if self.status != 'pending':
            raise UserError(_('Only pending requests can be rejected.'))
        
        self.write({
            'status': 'rejected',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'rejection_reason': reason,
        })
        
        # Notify requester
        self._notify_requester('rejected')
        
        return True
    
    def action_cancel(self):
        """Cancel the access request."""
        self.ensure_one()
        
        if self.status not in ('pending', 'approved'):
            raise UserError(_('Only pending or approved requests can be cancelled.'))
        
        self.status = 'cancelled'
        
        return True
    
    def _grant_access(self):
        """Grant the requested access."""
        # This would integrate with Odoo's ACL system
        # For now, we add the user to appropriate groups
        
        if self.access_type == 'read':
            group = self.env.ref('optimaai.group_optimaai_user', raise_if_not_found=False)
        elif self.access_type == 'write':
            group = self.env.ref('optimaai.group_optimaai_analyst', raise_if_not_found=False)
        elif self.access_type == 'admin':
            group = self.env.ref('optimaai.group_optimaai_admin', raise_if_not_found=False)
        else:
            group = False
        
        if group and self.requester_id:
            self.requester_id.write({
                'groups_id': [(4, group.id)]
            })
    
    def _notify_requester(self, result):
        """Notify requester about the result."""
        self.ensure_one()
        
        subject = _('Access Request %s') % result.upper()
        message = _('Your access request for "%s" has been %s.') % (self.name, result)
        
        if result == 'approved':
            message += _(' Access expires on %s.') % self.expiry_date
        
        self.env['optimaai.notification.service'].send_notification(
            user_id=self.requester_id.id,
            title=subject,
            message=message,
        )
    
    @api.model
    def create_access_request(self, resource_model, resource_id, access_type='read', reason=''):
        """Create an access request."""
        return self.create({
            'name': _('Access Request: %s#%d') % (resource_model, resource_id),
            'resource_model': resource_model,
            'resource_id': resource_id,
            'access_type': access_type,
            'reason': reason,
        })
    
    @api.model
    def get_pending_requests(self, user_id=None):
        """Get pending requests for a user."""
        domain = [('status', '=', 'pending')]
        if user_id:
            domain.append(('requester_id', '=', user_id))
        
        return self.search_read(domain, ['name', 'resource_ref', 'access_type', 'create_date'])
    
    # ==========================================
    # Cron Jobs
    # ==========================================
    
    @api.model
    def _cron_expire_requests(self):
        """Expire requests past their expiry date."""
        expired = self.search([
            ('status', '=', 'approved'),
            ('expiry_date', '<', fields.Datetime.now()),
        ])
        
        expired.write({'status': 'expired'})
        
        _logger.info('Expired %d access requests', len(expired))