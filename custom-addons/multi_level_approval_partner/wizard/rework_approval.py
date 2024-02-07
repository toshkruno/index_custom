# -*- coding: utf-8 -*-
from odoo import models


class ReworkApproval(models.TransientModel):
    _inherit = 'rework.approval'

    def action_rework(self):
        res = super(ReworkApproval, self).action_rework()
        if self.origin_ref._name == 'res.partner':
            self.origin_ref.write({'approval_state': 'Draft'})
        return res
