# -*- coding: utf-8 -*-
from odoo import models, api


class MultiApprovalType(models.Model):
    _inherit = 'multi.approval.type'

    @api.model
    def check_rule(self, records, vals):
        model_name = records._name
        if model_name in ('product.template', 'product.product'):
            approval_types = self._get_types(model_name)
            if not approval_types or len(approval_types) < 1:
                return True
            approval_type = approval_types[0]
            if approval_type.state_field == 'approval_state':
                return True
        return super(MultiApprovalType, self).check_rule(records, vals)
