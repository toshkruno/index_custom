# -*- coding: utf-8 -*-
{
    'name': "multi_level_approval_purchase",

    'summary': """
       Approval Configurations on Purchase orders""",

    'description': """
        Approval Configurations Made on Purchase Orders for Quotations
    """,

    'author': "Auraska Infotech Limited",
    'website': "http://www.auraska.ke",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase'],

    # always loaded
    'data': [
        'views/purchase_order.xml',

    ],
}
