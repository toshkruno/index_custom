# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import json
import werkzeug.utils

class CustomerStatementPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerStatementPortal,
                       self)._prepare_portal_layout_values()
        values.update({
            'page_name': 'sh_customer_statement_portal',
            'default_url': '/my/customer_statements',
        })
        return values

    @http.route(['/my/customer_statements', '/my/customer_statements/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_customer_statements(self, **kw):
        values = self._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        customer_statement_ids = partner_id.sh_customer_statement_ids
        overdue_statement_ids = partner_id.sh_customer_due_statement_ids
        values.update({
            'customer_statement_ids': customer_statement_ids,
            'overdue_statement_ids': overdue_statement_ids,
            'page_name': 'sh_customer_statement_portal',
            'default_url': '/my/customer_statements',
        })
        return request.render("sh_customer_statement.sh_customer_statement_portal", values)

    @http.route(['/my/customer_statements/send'], type='http', auth="user", website=False,csrf=False)
    def customer_statement_send(self, **post):
        dic = {}
        if post.get('customer_send_statement') == 'true':
            request.env.user.partner_id.action_send_customer_statement()
            dic.update({
                'msg':'Statement Sent Successfully.....'
                })
        if post.get('customer_send_overdue_statement') == 'true':
            request.env.user.partner_id.action_send_customer_due_statement()
            dic.update({
                'msg':'Statement Sent Successfully.....'
                })
        return json.dumps(dic)
    
    @http.route(['/my/customer_statements/xls'], type='http', auth="user", website=False,csrf=False)
    def customer_statement_xls(self, **post):
        res =  request.env.user.partner_id.action_print_customer_statement_xls()
        return werkzeug.utils.redirect(res.get('url'))
    
    @http.route(['/my/customer_statements_due/xls'], type='http', auth="user", website=False,csrf=False)
    def customer_statement_xls_due(self, **post):
        res =  request.env.user.partner_id.action_print_customer_due_statement_xls()
        return werkzeug.utils.redirect(res.get('url'))
