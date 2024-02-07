# -*- coding: utf-8 -*-
from odoo import models, fields


class MultiApproval(models.Model):
    _inherit = 'multi.approval'

    credit_partner = fields.Many2one('res.partner')

    def action_approve(self):
        res = super(MultiApproval, self).action_approve()
        if self.credit_partner:
            self.credit_partner.credit_approval_status = 'approved'
        return res

    def set_refused(self, reason=''):
        res = super(MultiApproval, self).set_refused(reason)
        if self.credit_partner:
            self.credit_partner.over_credit = False
        return res
