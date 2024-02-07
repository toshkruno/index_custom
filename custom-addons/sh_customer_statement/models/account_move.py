# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    sh_paid_amount = fields.Monetary('Paid Amount', compute='_compute_paid_amount')
    sh_balance = fields.Monetary('Balance Amount', compute='_compute_sh_balance')
    sh_today = fields.Date('Today')

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        res.update({
            'sh_today':fields.Date.today()
            })
        return res

    
    def _compute_paid_amount(self):
        if self:
            for rec in self:
                rec.sh_paid_amount = rec.amount_total_signed - rec.amount_residual_signed
    
    
    def _compute_sh_balance(self):
        if self:
            for rec in self:
                rec.sh_balance = rec.amount_total_signed - rec.sh_paid_amount