# -*- coding: utf-8 -*-
"""
OptimaAI Main Controllers
"""
import json
import logging
from datetime import datetime
from functools import wraps

from odoo import http, _, fields
from odoo.http import request, Response
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


def api_key_required(func):
    """
    Decorator to require valid API key for API endpoints.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.httprequest.headers.get('X-API-Key')
        if not api_key:
            return request.make_response(
                json.dumps({'error': 'API key required'}),
                headers={'Content-Type': 'application/json'},
                status=401
            )
        
        # Find valid API key
        key_record = request.env['res.users.api.key'].sudo().search([
            ('key', '=', api_key),
            ('active', '=', True),
        ], limit=1)
        
        if not key_record:
            return request.make_response(
                json.dumps({'error': 'Invalid API key'}),
                headers={'Content-Type': 'application/json'},
                status=401
            )
        
        if key_record.is_expired:
            return request.make_response(
                json.dumps({'error': 'API key expired'}),
                headers={'Content-Type': 'application/json'},
                status=401
            )
        
        # Update last used
        key_record.sudo().write({'last_used': fields.Datetime.now()})
        
        # Set user context
        request.update_env(user=key_record.user_id.id)
        
        return func(*args, **kwargs)
    return wrapper


def json_response(data, status=200):
    """
    Helper to create JSON response.
    """
    return request.make_response(
        json.dumps(data, default=str),
        headers={'Content-Type': 'application/json'},
        status=status
    )


class OptimaAIAPIController(http.Controller):
    """
    REST API Controller for OptimaAI
    """
    
    # ==========================================
    # Dataset API Endpoints
    # ==========================================
    
    @http.route('/api/v1/datasets', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def list_datasets(self, **kwargs):
        """
        List all datasets accessible to the user.
        """
        try:
            datasets = request.env['optimaai.dataset'].search([])
            result = [{
                'id': d.id,
                'name': d.name,
                'data_source': d.data_source,
                'status': d.status,
                'row_count': d.row_count,
                'create_date': d.create_date.isoformat() if d.create_date else None,
            } for d in datasets]
            return json_response({'datasets': result})
        except Exception as e:
            _logger.exception("Error listing datasets")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/datasets/<int:dataset_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def get_dataset(self, dataset_id, **kwargs):
        """
        Get a specific dataset by ID.
        """
        try:
            dataset = request.env['optimaai.dataset'].browse(dataset_id)
            if not dataset.exists():
                return json_response({'error': 'Dataset not found'}, status=404)
            
            result = {
                'id': dataset.id,
                'name': dataset.name,
                'data_source': dataset.data_source,
                'data_format': dataset.data_format,
                'status': dataset.status,
                'row_count': dataset.row_count,
                'file_size': dataset.file_size,
                'columns': [{
                    'name': c.name,
                    'type': c.column_type,
                    'required': c.required,
                    'unique_count': c.unique_count,
                    'missing_count': c.missing_count,
                } for c in dataset.column_ids],
                'data_raw': dataset.data_raw,
                'create_date': dataset.create_date.isoformat() if dataset.create_date else None,
            }
            return json_response({'dataset': result})
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error getting dataset")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/datasets', type='http', auth='public', methods=['POST'], csrf=False)
    @api_key_required
    def create_dataset(self, **kwargs):
        """
        Create a new dataset.
        """
        try:
            data = json.loads(request.httprequest.data)
            
            # Validate required fields
            if 'name' not in data:
                return json_response({'error': 'name is required'}, status=400)
            
            # Create dataset
            vals = {
                'name': data.get('name'),
                'data_source': data.get('data_source', 'api'),
                'data_format': data.get('data_format', 'json'),
                'data_raw': data.get('data_raw'),
            }
            
            dataset = request.env['optimaai.dataset'].create(vals)
            
            return json_response({
                'id': dataset.id,
                'name': dataset.name,
                'message': 'Dataset created successfully'
            }, status=201)
        except ValidationError as e:
            return json_response({'error': str(e)}, status=400)
        except Exception as e:
            _logger.exception("Error creating dataset")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/datasets/<int:dataset_id>', type='http', auth='public', methods=['PUT'], csrf=False)
    @api_key_required
    def update_dataset(self, dataset_id, **kwargs):
        """
        Update an existing dataset.
        """
        try:
            dataset = request.env['optimaai.dataset'].browse(dataset_id)
            if not dataset.exists():
                return json_response({'error': 'Dataset not found'}, status=404)
            
            data = json.loads(request.httprequest.data)
            
            vals = {}
            if 'name' in data:
                vals['name'] = data['name']
            if 'data_raw' in data:
                vals['data_raw'] = data['data_raw']
            if 'status' in data:
                vals['status'] = data['status']
            
            if vals:
                dataset.write(vals)
            
            return json_response({
                'id': dataset.id,
                'message': 'Dataset updated successfully'
            })
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error updating dataset")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/datasets/<int:dataset_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    @api_key_required
    def delete_dataset(self, dataset_id, **kwargs):
        """
        Delete a dataset.
        """
        try:
            dataset = request.env['optimaai.dataset'].browse(dataset_id)
            if not dataset.exists():
                return json_response({'error': 'Dataset not found'}, status=404)
            
            dataset.unlink()
            
            return json_response({'message': 'Dataset deleted successfully'})
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error deleting dataset")
            return json_response({'error': str(e)}, status=500)
    
    # ==========================================
    # Prediction API Endpoints
    # ==========================================
    
    @http.route('/api/v1/predictions', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def list_predictions(self, **kwargs):
        """
        List all predictions.
        """
        try:
            domain = []
            if 'status' in kwargs:
                domain.append(('status', '=', kwargs['status']))
            if 'dataset_id' in kwargs:
                domain.append(('dataset_id', '=', int(kwargs['dataset_id'])))
            
            predictions = request.env['optimaai.prediction'].search(domain)
            result = [{
                'id': p.id,
                'name': p.name,
                'prediction_type': p.prediction_type,
                'status': p.status,
                'dataset_id': p.dataset_id.id if p.dataset_id else None,
                'result_confidence': p.result_confidence,
            } for p in predictions]
            return json_response({'predictions': result})
        except Exception as e:
            _logger.exception("Error listing predictions")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/predictions/<int:prediction_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def get_prediction(self, prediction_id, **kwargs):
        """
        Get a specific prediction by ID.
        """
        try:
            prediction = request.env['optimaai.prediction'].browse(prediction_id)
            if not prediction.exists():
                return json_response({'error': 'Prediction not found'}, status=404)
            
            result = {
                'id': prediction.id,
                'name': prediction.name,
                'prediction_type': prediction.prediction_type,
                'status': prediction.status,
                'dataset_id': prediction.dataset_id.id if prediction.dataset_id else None,
                'result_confidence': prediction.result_confidence,
                'result_data': prediction.result_data,
                'error_message': prediction.error_message,
                'create_date': prediction.create_date.isoformat() if prediction.create_date else None,
                'completed_date': prediction.completed_date.isoformat() if prediction.completed_date else None,
            }
            return json_response({'prediction': result})
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error getting prediction")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/predictions', type='http', auth='public', methods=['POST'], csrf=False)
    @api_key_required
    def create_prediction(self, **kwargs):
        """
        Create and optionally run a prediction.
        """
        try:
            data = json.loads(request.httprequest.data)
            
            if 'dataset_id' not in data:
                return json_response({'error': 'dataset_id is required'}, status=400)
            
            dataset = request.env['optimaai.dataset'].browse(int(data['dataset_id']))
            if not dataset.exists():
                return json_response({'error': 'Dataset not found'}, status=404)
            
            vals = {
                'name': data.get('name', f'Prediction for {dataset.name}'),
                'dataset_id': dataset.id,
                'prediction_type': data.get('prediction_type', 'classification'),
                'target_column': data.get('target_column'),
                'model_config': json.dumps(data.get('model_config', {})),
            }
            
            prediction = request.env['optimaai.prediction'].create(vals)
            
            # Auto-run if requested
            if data.get('auto_run', False):
                prediction.action_run_prediction()
            
            return json_response({
                'id': prediction.id,
                'name': prediction.name,
                'status': prediction.status,
                'message': 'Prediction created successfully'
            }, status=201)
        except ValidationError as e:
            return json_response({'error': str(e)}, status=400)
        except Exception as e:
            _logger.exception("Error creating prediction")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/predictions/<int:prediction_id>/run', type='http', auth='public', methods=['POST'], csrf=False)
    @api_key_required
    def run_prediction(self, prediction_id, **kwargs):
        """
        Run a prediction.
        """
        try:
            prediction = request.env['optimaai.prediction'].browse(prediction_id)
            if not prediction.exists():
                return json_response({'error': 'Prediction not found'}, status=404)
            
            if prediction.status not in ['pending', 'failed']:
                return json_response({
                    'error': f'Cannot run prediction in {prediction.status} status'
                }, status=400)
            
            prediction.action_run_prediction()
            
            return json_response({
                'id': prediction.id,
                'status': prediction.status,
                'message': 'Prediction started'
            })
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error running prediction")
            return json_response({'error': str(e)}, status=500)
    
    # ==========================================
    # Insight API Endpoints
    # ==========================================
    
    @http.route('/api/v1/insights', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def list_insights(self, **kwargs):
        """
        List all insights.
        """
        try:
            domain = []
            if 'status' in kwargs:
                domain.append(('status', '=', kwargs['status']))
            if 'priority' in kwargs:
                domain.append(('priority', '=', kwargs['priority']))
            if 'dataset_id' in kwargs:
                domain.append(('dataset_id', '=', int(kwargs['dataset_id'])))
            
            insights = request.env['optimaai.insight'].search(domain)
            result = [{
                'id': i.id,
                'name': i.name,
                'insight_type': i.insight_type,
                'priority': i.priority,
                'status': i.status,
                'dataset_id': i.dataset_id.id if i.dataset_id else None,
                'create_date': i.create_date.isoformat() if i.create_date else None,
            } for i in insights]
            return json_response({'insights': result})
        except Exception as e:
            _logger.exception("Error listing insights")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/insights/<int:insight_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def get_insight(self, insight_id, **kwargs):
        """
        Get a specific insight by ID.
        """
        try:
            insight = request.env['optimaai.insight'].browse(insight_id)
            if not insight.exists():
                return json_response({'error': 'Insight not found'}, status=404)
            
            result = {
                'id': insight.id,
                'name': insight.name,
                'insight_type': insight.insight_type,
                'priority': insight.priority,
                'status': insight.status,
                'description': insight.description,
                'recommendations': insight.recommendations,
                'dataset_id': insight.dataset_id.id if insight.dataset_id else None,
                'prediction_id': insight.prediction_id.id if insight.prediction_id else None,
            }
            return json_response({'insight': result})
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error getting insight")
            return json_response({'error': str(e)}, status=500)
    
    # ==========================================
    # KPI API Endpoints
    # ==========================================
    
    @http.route('/api/v1/kpis', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def list_kpis(self, **kwargs):
        """
        List all KPIs.
        """
        try:
            domain = []
            if 'status' in kwargs:
                domain.append(('status', '=', kwargs['status']))
            if 'category' in kwargs:
                domain.append(('category', '=', kwargs['category']))
            
            kpis = request.env['optimaai.kpi'].search(domain)
            result = [{
                'id': k.id,
                'name': k.name,
                'code': k.code,
                'kpi_type': k.kpi_type,
                'category': k.category,
                'value': k.current_value,
                'target_value': k.target_value,
                'unit': k.unit,
                'status': k.status,
                'trend_direction': k.trend_direction,
                'trend_percentage': k.trend_percentage,
            } for k in kpis]
            return json_response({'kpis': result})
        except Exception as e:
            _logger.exception("Error listing KPIs")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/kpis/<int:kpi_id>', type='http', auth='public', methods=['GET'], csrf=False)
    @api_key_required
    def get_kpi(self, kpi_id, **kwargs):
        """
        Get a specific KPI by ID.
        """
        try:
            kpi = request.env['optimaai.kpi'].browse(kpi_id)
            if not kpi.exists():
                return json_response({'error': 'KPI not found'}, status=404)
            
            result = {
                'id': kpi.id,
                'name': kpi.name,
                'code': kpi.code,
                'kpi_type': kpi.kpi_type,
                'category': kpi.category,
                'value': kpi.current_value,
                'previous_value': kpi.previous_value,
                'target_value': kpi.target_value,
                'unit': kpi.unit,
                'status': kpi.status,
                'trend_direction': kpi.trend_direction,
                'trend_percentage': kpi.trend_percentage,
                'last_calculated': kpi.last_calculated.isoformat() if kpi.last_calculated else None,
            }
            return json_response({'kpi': result})
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error getting KPI")
            return json_response({'error': str(e)}, status=500)
    
    @http.route('/api/v1/kpis/<int:kpi_id>/calculate', type='http', auth='public', methods=['POST'], csrf=False)
    @api_key_required
    def calculate_kpi(self, kpi_id, **kwargs):
        """
        Calculate KPI value.
        """
        try:
            kpi = request.env['optimaai.kpi'].browse(kpi_id)
            if not kpi.exists():
                return json_response({'error': 'KPI not found'}, status=404)
            
            kpi.action_calculate()
            
            return json_response({
                'id': kpi.id,
                'value': kpi.current_value,
                'status': kpi.status,
                'message': 'KPI calculated successfully'
            })
        except AccessError:
            return json_response({'error': 'Access denied'}, status=403)
        except Exception as e:
            _logger.exception("Error calculating KPI")
            return json_response({'error': str(e)}, status=500)


class OptimaAIDashboardController(http.Controller):
    """
    Controller for Dashboard web interface.
    """
    
    @http.route('/optimaai/dashboard', type='http', auth='user', website=True)
    def dashboard(self, **kwargs):
        """
        Render the main dashboard.
        """
        # Get summary data
        dataset_count = request.env['optimaai.dataset'].search_count([])
        prediction_count = request.env['optimaai.prediction'].search_count([('status', '=', 'completed')])
        insight_count = request.env['optimaai.insight'].search_count([('action_status', 'not in', ['dismissed', 'resolved'])])
        kpi_count = request.env['optimaai.kpi'].search_count([])
        
        # Get recent items
        recent_datasets = request.env['optimaai.dataset'].search([], limit=5, order='create_date desc')
        recent_predictions = request.env['optimaai.prediction'].search([], limit=5, order='create_date desc')
        active_insights = request.env['optimaai.insight'].search([('action_status', 'not in', ['dismissed', 'resolved'])], limit=5, order='create_date desc')
        
        values = {
            'dataset_count': dataset_count,
            'prediction_count': prediction_count,
            'insight_count': insight_count,
            'kpi_count': kpi_count,
            'recent_datasets': recent_datasets,
            'recent_predictions': recent_predictions,
            'active_insights': active_insights,
        }
        
        return request.render('optimaai.dashboard_template', values)
    
    @http.route('/optimaai/dashboard/data', type='json', auth='user')
    def dashboard_data(self, **kwargs):
        """
        Get dashboard data for AJAX updates.
        Returns summary counts plus recent KPIs and active insights.
        """
        # Fetch recent KPIs
        recent_kpis = request.env['optimaai.kpi'].search([], limit=12, order='write_date desc')
        kpi_list = [{
            'id': k.id,
            'name': k.name,
            'value': k.current_value,
            'target_value': k.target_value,
            'unit': k.unit,
            'status': k.status,
            'trend': k.trend,
            'progress_percentage': k.progress_percentage,
            'category': k.category or 'operational',
            'icon': k.icon or 'fa-tachometer',
        } for k in recent_kpis]

        # Fetch active insights
        active_insights = request.env['optimaai.insight'].search(
            [('action_status', 'not in', ['dismissed', 'resolved'])], limit=5, order='create_date desc'
        )
        insight_list = [{
            'id': i.id,
            'name': i.name,
            'description': i.summary or '',
            'insight_type': i.insight_type,
            'priority': i.priority,
            'action_status': i.action_status,
        } for i in active_insights]

        return {
            'datasets': {
                'total': request.env['optimaai.dataset'].search_count([]),
                'by_status': self._get_count_by_field('optimaai.dataset', 'status'),
            },
            'predictions': {
                'total': request.env['optimaai.prediction'].search_count([]),
                'by_status': self._get_count_by_field('optimaai.prediction', 'status'),
                'by_type': self._get_count_by_field('optimaai.prediction', 'prediction_type'),
            },
            'insights': {
                'total': request.env['optimaai.insight'].search_count([('action_status', 'not in', ['dismissed', 'resolved'])]),
                'by_priority': self._get_count_by_field('optimaai.insight', 'priority', [('action_status', 'not in', ['dismissed', 'resolved'])]),
            },
            'kpis': {
                'total': request.env['optimaai.kpi'].search_count([]),
                'by_status': self._get_count_by_field('optimaai.kpi', 'status'),
            },
            'recentKpis': kpi_list,
            'activeInsights': insight_list,
        }
    
    def _get_count_by_field(self, model, field, domain=None):
        """
        Get count of records grouped by field.
        Compatible with Odoo 19's read_group format.
        """
        if domain is None:
            domain = []
        
        groups = request.env[model].read_group(domain, [], [field])
        result = {}
        for group in groups:
            key = group[field]
            # Odoo 19 uses '<field>_count' instead of '__count'
            count = group.get('__count', group.get(f'{field}_count', 0))
            result[key] = count
        return result


class OptimaAIRPCController(http.Controller):
    """
    JSON-RPC endpoints consumed by the OWL frontend components.
    All routes use type='json' and auth='user'.
    """

    # ------------------------------------------
    # Notification endpoints
    # ------------------------------------------

    @http.route('/optimaai/notifications/count', type='json', auth='user')
    def notification_count(self, **kwargs):
        """Return unread notification count for the current user."""
        count = request.env['optimaai.notification'].search_count([
            ('user_id', '=', request.env.uid),
            ('is_read', '=', False),
        ])
        return {'count': count}

    @http.route('/optimaai/notifications/list', type='json', auth='user')
    def notification_list(self, limit=20, **kwargs):
        """Return recent notifications for the current user."""
        notifications = request.env['optimaai.notification'].search(
            [('user_id', '=', request.env.uid)],
            limit=int(limit),
            order='create_date desc',
        )
        return {
            'notifications': [{
                'id': n.id,
                'title': n.title,
                'message': n.message or '',
                'notification_type': n.notification_type,
                'is_read': n.is_read,
                'related_model': n.related_model or False,
                'related_id': n.related_id or False,
                'create_date': str(n.create_date) if n.create_date else '',
            } for n in notifications]
        }

    @http.route('/optimaai/notifications/mark_read', type='json', auth='user')
    def notification_mark_read(self, id=None, **kwargs):
        """Mark a single notification as read."""
        if id:
            notif = request.env['optimaai.notification'].browse(int(id))
            if notif.exists() and notif.user_id.id == request.env.uid:
                notif.write({'is_read': True})
        return {'success': True}

    @http.route('/optimaai/notifications/mark_all_read', type='json', auth='user')
    def notification_mark_all_read(self, **kwargs):
        """Mark all notifications as read for the current user."""
        notifications = request.env['optimaai.notification'].search([
            ('user_id', '=', request.env.uid),
            ('is_read', '=', False),
        ])
        notifications.write({'is_read': True})
        return {'success': True}

    # ------------------------------------------
    # Insight endpoints
    # ------------------------------------------

    @http.route('/optimaai/insight/dismiss', type='json', auth='user')
    def insight_dismiss(self, id=None, **kwargs):
        """Dismiss an insight by setting its status to dismissed."""
        if id:
            insight = request.env['optimaai.insight'].browse(int(id))
            if insight.exists():
                insight.write({'action_status': 'dismissed'})
        return {'success': True}

    # ------------------------------------------
    # Dataset preview endpoint
    # ------------------------------------------

    @http.route('/optimaai/dataset/preview', type='json', auth='user')
    def dataset_preview(self, dataset_id=None, limit=10, **kwargs):
        """Return a preview of the dataset rows and columns."""
        if not dataset_id:
            return {'data': [], 'columns': []}

        dataset = request.env['optimaai.dataset'].browse(int(dataset_id))
        if not dataset.exists():
            return {'data': [], 'columns': []}

        # Parse raw data
        data = []
        columns = []
        try:
            import json as _json
            raw = _json.loads(dataset.data_raw or '[]')
            if isinstance(raw, list) and raw:
                columns = list(raw[0].keys()) if isinstance(raw[0], dict) else []
                data = raw[:int(limit)]
        except Exception:
            pass

        # Also include column definitions if available
        if not columns and dataset.column_ids:
            columns = [c.name for c in dataset.column_ids]

        return {'data': data, 'columns': columns}

    # ------------------------------------------
    # Canvas endpoints
    # ------------------------------------------

    @http.route('/optimaai/canvas/load', type='json', auth='user')
    def canvas_load(self, canvas_id=None, **kwargs):
        """Load canvas blocks for a given canvas."""
        if not canvas_id:
            return {'blocks': []}

        canvas = request.env['optimaai.canvas'].browse(int(canvas_id))
        if not canvas.exists():
            return {'blocks': []}

        blocks = [{
            'id': b.id,
            'name': b.name,
            'block_type': b.block_type,
            'position_x': b.position_x,
            'position_y': b.position_y,
            'width': b.width if hasattr(b, 'width') else 1,
            'height': b.height if hasattr(b, 'height') else 1,
        } for b in canvas.block_ids]

        return {'blocks': blocks}

    @http.route('/optimaai/canvas/remove_block', type='json', auth='user')
    def canvas_remove_block(self, block_id=None, **kwargs):
        """Remove a canvas block by ID."""
        if block_id:
            block = request.env['optimaai.canvas.block'].browse(int(block_id))
            if block.exists():
                block.unlink()
        return {'success': True}


class OptimaAIWebhookController(http.Controller):
    """
    Controller for webhook endpoints.
    """
    
    @http.route('/webhook/optimaai/<string:webhook_type>', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_webhook(self, webhook_type, **kwargs):
        """
        Handle incoming webhooks.
        """
        try:
            data = json.loads(request.httprequest.data)
            
            # Get integration config for this webhook type
            integration = request.env['optimaai.integration.config'].sudo().search([
                ('provider', '=', webhook_type),
                ('active', '=', True),
            ], limit=1)
            
            if not integration:
                _logger.warning(f"No active integration found for webhook type: {webhook_type}")
                return json_response({'error': 'Integration not found'}, status=404)
            
            # Process webhook based on type
            if webhook_type == 'data_source':
                return self._process_data_source_webhook(integration, data)
            elif webhook_type == 'notification':
                return self._process_notification_webhook(integration, data)
            else:
                return json_response({'error': 'Unknown webhook type'}, status=400)
            
        except Exception as e:
            _logger.exception("Error processing webhook")
            return json_response({'error': str(e)}, status=500)
    
    def _process_data_source_webhook(self, integration, data):
        """
        Process data source webhook.
        """
        # Create or update dataset
        if 'dataset_name' in data and 'data' in data:
            dataset_vals = {
                'name': data['dataset_name'],
                'data_source': 'webhook',
                'data_raw': json.dumps(data['data']),
            }
            dataset = request.env['optimaai.dataset'].sudo().create(dataset_vals)
            
            return json_response({
                'message': 'Dataset created',
                'dataset_id': dataset.id
            }, status=201)
        
        return json_response({'message': 'Webhook received'})
    
    def _process_notification_webhook(self, integration, data):
        """
        Process notification webhook.
        """
        if 'message' in data:
            notification_vals = {
                'name': data.get('title', 'External Notification'),
                'notification_type': data.get('type', 'info'),
                'message': data['message'],
                'priority': data.get('priority', 'medium'),
            }
            
            if 'user_id' in data:
                notification_vals['user_id'] = int(data['user_id'])
            
            notification = request.env['optimaai.notification'].sudo().create(notification_vals)
            
            return json_response({
                'message': 'Notification created',
                'notification_id': notification.id
            }, status=201)
        
        return json_response({'message': 'Webhook received'})