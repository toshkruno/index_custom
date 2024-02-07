# -*- coding: utf-8 -*-
from odoo import models


class MultiApproval(models.Model):
    _inherit = 'multi.approval'

    def set_approved(self):
        res = super(MultiApproval, self).set_approved()
        if self.origin_ref and self.origin_ref._name == 'res.partner':
            self.origin_ref.write({'approval_state': 'Approved'})
        return res

    def set_refused(self, reason=''):
        res = super(MultiApproval, self).set_refused(reason)
        if self.origin_ref and self.origin_ref._name == 'res.partner':
            self.origin_ref.write({'approval_state': 'Refused'})
        return res

