# -*- coding: utf-8 -*-
"""
Integration Configuration Model
================================
External API integrations configuration.
Equivalent to Next.js integrations page.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class IntegrationConfig(models.Model):
    """Integration configuration model."""
    
    _name = 'optimaai.integration.config'
    _description = 'Integration Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    
    # ==========================================
    # Fields
    # ==========================================
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Code',
        help='Unique identifier for the integration'
    )
    
    # Integration type
    integration_type = fields.Selection([
        ('rest_api', 'REST API'),
        ('graphql', 'GraphQL'),
        ('webhook', 'Webhook'),
        ('database', 'Database'),
        ('file_storage', 'File Storage'),
        ('messaging', 'Messaging'),
        ('ai_service', 'AI Service'),
        ('custom', 'Custom'),
    ], string='Type',
        default='rest_api',
        required=True,
        tracking=True
    )
    
    # Provider presets
    provider = fields.Selection([
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google_ai', 'Google AI'),
        ('azure', 'Azure'),
        ('aws', 'AWS'),
        ('salesforce', 'Salesforce'),
        ('hubspot', 'HubSpot'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('custom', 'Custom'),
    ], string='Provider',
        default='custom',
        tracking=True
    )
    
    # Connection settings
    base_url = fields.Char(
        string='Base URL'
    )
    
    api_version = fields.Char(
        string='API Version'
    )
    
    # Authentication
    auth_type = fields.Selection([
        ('none', 'No Authentication'),
        ('api_key', 'API Key'),
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Auth'),
        ('oauth2', 'OAuth 2.0'),
        ('custom', 'Custom Headers'),
    ], string='Authentication Type',
        default='api_key'
    )
    
    # API Key authentication
    api_key_header = fields.Char(
        string='API Key Header Name',
        default='X-API-Key'
    )
    
    api_key_id = fields.Many2one(
        comodel_name='res.users.api.key',
        string='API Key'
    )
    
    # Bearer token
    bearer_token = fields.Text(
        string='Bearer Token'
    )
    
    # Basic auth
    username = fields.Char(
        string='Username'
    )
    
    password = fields.Char(
        string='Password'
    )
    
    # OAuth2
    oauth_client_id = fields.Char(
        string='Client ID'
    )
    
    oauth_client_secret = fields.Char(
        string='Client Secret'
    )
    
    oauth_token_url = fields.Char(
        string='Token URL'
    )
    
    oauth_scope = fields.Char(
        string='Scope'
    )
    
    oauth_access_token = fields.Text(
        string='Access Token',
        readonly=True
    )
    
    oauth_refresh_token = fields.Text(
        string='Refresh Token',
        readonly=True
    )
    
    oauth_token_expiry = fields.Datetime(
        string='Token Expiry',
        readonly=True
    )
    
    # Custom headers
    custom_headers = fields.Text(
        string='Custom Headers',
        widget='json',
        default='{}'
    )
    
    # Request settings
    timeout = fields.Integer(
        string='Timeout (seconds)',
        default=30
    )
    
    retry_count = fields.Integer(
        string='Retry Count',
        default=3
    )
    
    retry_delay = fields.Integer(
        string='Retry Delay (ms)',
        default=1000
    )
    
    # Rate limiting
    rate_limit_enabled = fields.Boolean(
        string='Rate Limiting Enabled',
        default=False
    )
    
    rate_limit_requests = fields.Integer(
        string='Requests per Period',
        default=100
    )
    
    rate_limit_period = fields.Integer(
        string='Period (seconds)',
        default=60
    )
    
    # Endpoints
    endpoint_ids = fields.One2many(
        comodel_name='optimaai.integration.endpoint',
        inverse_name='integration_id',
        string='Endpoints'
    )
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ], string='Status',
        default='draft',
        tracking=True,
        index=True
    )
    
    last_connection_test = fields.Datetime(
        string='Last Connection Test',
        readonly=True
    )
    
    connection_status = fields.Selection([
        ('unknown', 'Unknown'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Connection Status',
        default='unknown',
        readonly=True
    )
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )
    
    # Statistics
    total_requests = fields.Integer(
        string='Total Requests',
        default=0,
        readonly=True
    )
    
    successful_requests = fields.Integer(
        string='Successful Requests',
        default=0,
        readonly=True
    )
    
    failed_requests = fields.Integer(
        string='Failed Requests',
        default=0,
        readonly=True
    )
    
    last_request_date = fields.Datetime(
        string='Last Request',
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
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # ==========================================
    # Constraints
    # ==========================================
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code, company_id)', 'Integration code must be unique per company.'),
    ]
    
    # ==========================================
    # Business Methods
    # ==========================================
    
    def action_test_connection(self):
        """Test the connection."""
        self.ensure_one()
        
        try:
            result = self._test_connection()
            
            self.write({
                'last_connection_test': fields.Datetime.now(),
                'connection_status': 'success',
                'status': 'active',
                'error_message': False,
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Connection successful!'),
                    'type': 'success',
                }
            }
            
        except Exception as e:
            self.write({
                'last_connection_test': fields.Datetime.now(),
                'connection_status': 'failed',
                'error_message': str(e),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': str(e),
                    'type': 'danger',
                }
            }
    
    def _test_connection(self):
        """Internal connection test."""
        if self.base_url:
            response = self._make_request('GET', self.base_url)
            return response
        return {'status': 'success'}
    
    def call_api(self, endpoint=None, method='GET', data=None, params=None):
        """
        Make an API call.
        
        Args:
            endpoint: Endpoint path or endpoint record
            method: HTTP method
            data: Request body data
            params: Query parameters
        
        Returns:
            Response data
        """
        self.ensure_one()
        
        # Build URL
        if isinstance(endpoint, models.BaseModel):
            url = endpoint.full_url
        elif endpoint:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        else:
            url = self.base_url
        
        return self._make_request(method, url, data=data, params=params)
    
    def _make_request(self, method, url, data=None, params=None, headers=None):
        """
        Make HTTP request with authentication.
        
        Args:
            method: HTTP method
            url: Full URL
            data: Request body
            params: Query parameters
            headers: Additional headers
        
        Returns:
            Response data
        """
        self.ensure_one()
        
        # Build headers
        request_headers = self._build_headers()
        if headers:
            request_headers.update(headers)
        
        # Make request with retry
        last_error = None
        for attempt in range(self.retry_count):
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    json=data if data else None,
                    params=params,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                
                # Update stats
                self._update_stats(response.ok)
                
                if response.ok:
                    try:
                        return response.json()
                    except ValueError:
                        return {'status': 'success', 'text': response.text}
                else:
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.retry_count - 1:
                    import time
                    time.sleep(self.retry_delay / 1000)
        
        # All retries failed
        self._update_stats(False)
        raise Exception(f"Request failed after {self.retry_count} attempts: {last_error}")
    
    def _build_headers(self):
        """Build request headers with authentication."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.auth_type == 'api_key' and self.api_key_id:
            headers[self.api_key_header] = self.api_key_id.key
        
        elif self.auth_type == 'bearer' and self.bearer_token:
            headers['Authorization'] = f"Bearer {self.bearer_token}"
        
        elif self.auth_type == 'basic' and self.username and self.password:
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"
        
        elif self.auth_type == 'oauth2' and self.oauth_access_token:
            # Check token expiry
            if self.oauth_token_expiry and self.oauth_token_expiry < datetime.now():
                self._refresh_oauth_token()
            headers['Authorization'] = f"Bearer {self.oauth_access_token}"
        
        elif self.auth_type == 'custom' and self.custom_headers:
            custom = json.loads(self.custom_headers)
            headers.update(custom)
        
        return headers
    
    def _refresh_oauth_token(self):
        """Refresh OAuth2 token."""
        if not self.oauth_refresh_token or not self.oauth_token_url:
            return
        
        try:
            response = requests.post(
                self.oauth_token_url,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.oauth_refresh_token,
                    'client_id': self.oauth_client_id,
                    'client_secret': self.oauth_client_secret,
                }
            )
            
            if response.ok:
                data = response.json()
                self.write({
                    'oauth_access_token': data.get('access_token'),
                    'oauth_refresh_token': data.get('refresh_token', self.oauth_refresh_token),
                    'oauth_token_expiry': datetime.now() + datetime.timedelta(seconds=data.get('expires_in', 3600)),
                })
        except Exception as e:
            _logger.error('Failed to refresh OAuth token: %s', str(e))
    
    def _update_stats(self, success):
        """Update request statistics."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.last_request_date = fields.Datetime.now()
    
    def action_activate(self):
        """Activate the integration."""
        self.ensure_one()
        self.status = 'active'
        return True
    
    def action_deactivate(self):
        """Deactivate the integration."""
        self.ensure_one()
        self.status = 'inactive'
        return True


class IntegrationEndpoint(models.Model):
    """Integration endpoint configuration."""
    
    _name = 'optimaai.integration.endpoint'
    _description = 'Integration Endpoint'
    _order = 'integration_id, sequence'
    
    name = fields.Char(
        string='Name',
        required=True
    )
    
    integration_id = fields.Many2one(
        comodel_name='optimaai.integration.config',
        string='Integration',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Endpoint configuration
    path = fields.Char(
        string='Path',
        required=True,
        help='Endpoint path relative to base URL'
    )
    
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ], string='Method',
        default='GET',
        required=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    # Request/Response
    request_template = fields.Text(
        string='Request Template',
        widget='json'
    )
    
    response_mapping = fields.Text(
        string='Response Mapping',
        widget='json'
    )
    
    # Cache
    cache_enabled = fields.Boolean(
        string='Enable Caching',
        default=False
    )
    
    cache_ttl = fields.Integer(
        string='Cache TTL (seconds)',
        default=300
    )
    
    # Computed
    full_url = fields.Char(
        string='Full URL',
        compute='_compute_full_url'
    )
    
    @api.depends('integration_id.base_url', 'path')
    def _compute_full_url(self):
        for record in self:
            if record.integration_id.base_url and record.path:
                base = record.integration_id.base_url.rstrip('/')
                path = record.path.lstrip('/')
                record.full_url = f"{base}/{path}"
            else:
                record.full_url = False
    
    def call(self, data=None, params=None):
        """Call this endpoint."""
        self.ensure_one()
        return self.integration_id._make_request(
            method=self.method,
            url=self.full_url,
            data=data,
            params=params
        )