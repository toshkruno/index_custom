# See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Credit Limit',
    'version': '14.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'Tiny, Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Set credit limit warning',
    'depends': [
        'sale_management', 'multi_level_approval_configuration'
    ],
    'data': [
        'data/approval_data.xml',
        'views/partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
