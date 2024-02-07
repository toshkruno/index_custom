# -*- coding: utf-8 -*-
from odoo import models


class RequestApproval(models.TransientModel):
    _inherit = 'request.approval'

    def action_request(self):
        res = super(RequestApproval, self).action_request()
        if self.origin_ref._name in ['product.product', 'product.template']:
            self.origin_ref.write({'approval_state': 'Submitted'})
        return res
