    # -*- coding: utf-8 -*-
# Part of Appjetty. See LICENSE file for full copyright and licensing details.

{
    'name': 'Clever Multiple Invoice Template',
    'version': '15.0.1.0.0',
    'author': 'Appjetty',
    'license': 'OPL-1',
    'category': 'Accounting',
    'depends': ['account', 'sale_management', 'purchase'],
    'website': 'https://www.appjetty.com',
    'description': '''Professiona Templates ,  
    Professional Report Templates , Customizable Invoice Templates , 
    Multiple Professional Invoice Templates  , Customized Invoice''',
    'summary': 'Get Diverse Invoice Templates In One Go!',
    'data': [
        'security/ir.model.access.csv',
        'data/template_data.xml',
        'views/templates.xml',
        'views/template_report.xml',
        'views/creative_template.xml',
        'views/elegant_template.xml',
        'views/professional_template.xml',
        'views/exclusive_template.xml',
        'views/advanced_template.xml',
        'views/incredible_template.xml',
        'views/innovative_template.xml',
        'views/custom_template.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/invoice_view.xml',
        'views/report_extra_content_view.xml',
    ],
    'external_dependencies': {
        'python': ['img2pdf', 'fpdf', 'num2words']
    },
    'assets': {
        'web.assets_backend': [
            '/biztech_report_template/static/src/css/colpick.css',
            '/biztech_report_template/static/src/css/widget.css',
           '/biztech_report_template/static/lib/colpick/colpick.js',
           '/biztech_report_template/static/src/js/widget.js'
        ],
        'web.report_assets_common': [
            '/biztech_report_template/static/src/css/template.css',
        ],
        'web.assets_qweb': [
           '/biztech_report_template/static/src/xml/widget_color.xml',
        ],
    },
    'images': ['static/description/splash-screen.png'],
    'price': 39.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'web_preload': True,
}
