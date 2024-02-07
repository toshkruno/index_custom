# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    approval_state = fields.Selection(
        [('Draft', 'Draft'),
         ('Submitted', 'Submitted'),
         ('Approved', 'Approved'),
         ('Refused', 'Refused'),
         ('Cancel', 'Cancel')], default='Draft', tracking=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids = self._name_search(name, args, operator, limit=limit)
        return self.search([('id', 'in', ids), ('approval_state', '=', 'Approved')]).sudo().name_get()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids = self._name_search(name, args, operator, limit=limit)
        return self.search([('id', 'in', ids), ('approval_state', '=', 'Approved')]).sudo().name_get()
