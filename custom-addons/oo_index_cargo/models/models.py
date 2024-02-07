# -*- coding: utf-8 -*-

import uuid

from odoo import api, models, fields
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.model
    def create(self, vals):
        if not self.env.user.has_group('oo_index_cargo.oo_contact_creation'):
            raise UserError("You're not allowed to create contacts.")
        return super().create(vals)

    def write(self, vals):
        if not self.env.user.has_group('oo_index_cargo.oo_contact_creation'):
            raise UserError("You're not allowed to update contacts.")
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('oo_index_cargo.oo_contact_creation'):
            raise UserError("You're not allowed to delete contacts.")
        return super().unlink()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('oo_index_cargo.oo_product_creation'):
            raise UserError("You're not allowed to create products.")
        return super().create(vals)

    def write(self, vals):
        if not self.env.user.has_group('oo_index_cargo.oo_product_creation'):
            raise UserError("You're not allowed to update products.")
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('oo_index_cargo.oo_product_creation'):
            raise UserError("You're not allowed to delete products.")
        return super().unlink()
    

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('oo_index_cargo.oo_product_creation'):
            raise UserError("You're not allowed to create products.")
        return super().create(vals)

    def write(self, vals):
        if not self.env.user.has_group('oo_index_cargo.oo_product_creation'):
            raise UserError("You're not allowed to update products.")
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('oo_index_cargo.oo_product_creation'):
            raise UserError("You're not allowed to delete products.")
        return super().unlink()
    
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_note = fields.Text(string='Order Note', help="Extra order details")


class AccountMove(models.Model):
    _inherit = 'account.move'

    po_number = fields.Char(string='PO Number')
    reference_number = fields.Char(string='Reference Number')

    @api.model
    def create(self, vals):
        if not vals.get('access_token'):
            vals['access_token'] = uuid.uuid4().hex
        return super().create(vals)


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res.update({
            'po_number': move.po_number,
            'reference_number': move.reference_number,
        })
        return res
