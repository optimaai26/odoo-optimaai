# -*- coding: utf-8 -*-
"""
OptimaAI Website Controllers
=============================
Public-facing website pages connected to backend models.
"""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OptimaAIWebsiteController(http.Controller):
    """
    Controller for public-facing OptimaAI website pages.
    Uses website=True to get the website layout (header, footer, SEO).
    """

    @http.route('/optimaai/public-dashboard', type='http', auth='user', website=True)
    def public_dashboard(self, **kwargs):
        """
        Public-facing dashboard page.
        Shows KPIs, recent datasets, active insights from the backend models.
        """
        try:
            # Summary counts
            dataset_count = request.env['optimaai.dataset'].search_count([])
            prediction_count = request.env['optimaai.prediction'].search_count(
                [('status', '=', 'completed')]
            )
            insight_count = request.env['optimaai.insight'].search_count(
                [('status', '=', 'active')]
            )
            kpi_count = request.env['optimaai.kpi'].search_count([])

            # Recent items
            recent_datasets = request.env['optimaai.dataset'].search(
                [], limit=5, order='create_date desc'
            )
            active_insights = request.env['optimaai.insight'].search(
                [('status', '=', 'active')], limit=5, order='create_date desc'
            )
            top_kpis = request.env['optimaai.kpi'].search(
                [], limit=6, order='write_date desc'
            )

            values = {
                'dataset_count': dataset_count,
                'prediction_count': prediction_count,
                'insight_count': insight_count,
                'kpi_count': kpi_count,
                'recent_datasets': recent_datasets,
                'active_insights': active_insights,
                'top_kpis': top_kpis,
            }

            return request.render('optimaai.page_public_dashboard', values)

        except Exception as e:
            _logger.exception("Error rendering public dashboard")
            return request.render('http_routing.404')

    @http.route('/optimaai/public-dashboard/data', type='json', auth='user', website=True)
    def public_dashboard_data(self, **kwargs):
        """
        JSON endpoint for AJAX dashboard updates from the website frontend.
        """
        return {
            'datasets': {
                'total': request.env['optimaai.dataset'].search_count([]),
            },
            'predictions': {
                'total': request.env['optimaai.prediction'].search_count([]),
                'completed': request.env['optimaai.prediction'].search_count(
                    [('status', '=', 'completed')]
                ),
            },
            'insights': {
                'active': request.env['optimaai.insight'].search_count(
                    [('status', '=', 'active')]
                ),
            },
            'kpis': {
                'total': request.env['optimaai.kpi'].search_count([]),
            },
        }
