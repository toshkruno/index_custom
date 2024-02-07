# -*- coding: utf-8 -*-

import itertools
from odoo import models, fields, api
import logging
from datetime import timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'


	is_quotation = fields.Boolean("Is Quotation", default=False)


	@api.onchange('is_quotation')
	def check_template_source(self):
		for rec in self:
			if rec.requisition_id and rec.is_quotation:
				purchase_orders = self.env['purchase.order'].search([
					('requisition_id', '=', rec.requisition_id.id)
				])
				for order in purchase_orders:
					if order.is_quotation:
						raise ValidationError(f"Purchase order {order.name} is already a quotation for purchase agreement {rec.requisition_id.name}")