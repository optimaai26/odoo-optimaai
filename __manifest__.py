# -*- coding: utf-8 -*-
{
    'name': 'OptimaAI - Business Intelligence Platform',
    'version': '19.0.1.0.0',
    'summary': 'AI-powered business intelligence and predictive analytics',
    'description': """
        OptimaAI Module
        ===============
        
        A comprehensive business intelligence platform that provides:
        - Dataset management and analysis
        - AI-powered predictions
        - Automated insights generation
        - Report generation
        - Visual canvas for data workflows
        - KPI tracking and monitoring
        - Notification system
        - Public-facing website dashboard
        
        Migrated from Next.js application with full feature parity.
    """,
    'category': 'Tools',
    'author': 'OptimaAI Team',
    'website': 'https://optimaai.example.com',
    'license': 'LGPL-3',
    
    # Dependencies
    'depends': [
        'base',
        'mail',
        'web',
        'board',
        'bus',
        'website',  # For public-facing website pages
    ],
    
    # Data files (load order matters)
    'data': [
        # Security first
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Sequences
        'data/sequence_data.xml',
        
        # Default data
        'data/default_kpi_data.xml',
        
        # Website pages
        'data/pages/dashboard.xml',
        
        # Views (menu_views.xml MUST be last — it references actions from the other files)
        'views/dataset_views.xml',
        'views/prediction_views.xml',
        'views/insight_views.xml',
        'views/report_views.xml',
        'views/canvas_views.xml',
        'views/kpi_views.xml',
        'views/notification_views.xml',
        'views/menu_views.xml',
    ],
    
    # Demo data (only loaded in demo mode)
    'demo': [
        'demo/demo_data.xml',
    ],
    
    # Assets
    'assets': {
        # Backend assets (Odoo backend / web client)
        'web.assets_backend': [
            'optimaai/static/src/scss/optimaai.scss',
            'optimaai/static/src/js/optimaai.js',
            'optimaai/static/src/xml/optimaai_templates.xml',
        ],
        # Website theme: Primary variables (loaded BEFORE Bootstrap)
        'web._assets_primary_variables': [
            'optimaai/static/src/scss/primary_variables.scss',
        ],
        # Website theme: Bootstrap overrides (loaded AFTER primary vars, BEFORE Bootstrap)
        'web._assets_frontend_helpers': [
            'optimaai/static/src/scss/bootstrap_overridden.scss',
        ],
        # Website frontend assets (public-facing pages)
        'web.assets_frontend': [
            'optimaai/static/src/scss/font.scss',
            'optimaai/static/src/scss/theme.scss',
        ],
    },
    
    # External dependencies
    'external_dependencies': {
        'python': [
            'requests',
            'pandas',
            'openpyxl',
        ],
    },
    
    # Auto-install (set to False for manual installation)
    'auto_install': False,
    
    # Application flag (shows in Apps list)
    'application': True,
    
    # Installable
    'installable': True,
    
    # Maintainer
    'maintainer': 'OptimaAI Team',
    
    # Support
    'support': 'support@optimaai.example.com',
}