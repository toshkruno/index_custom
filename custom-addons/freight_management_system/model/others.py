from odoo import fields, models

TRANSPORT_MODES = [('land', 'Land'), ('air', 'Air'), ('sea', 'Sea'), ('rail', 'Rail')]


class AccountMove(models.Model):
    _inherit = 'account.move'

    custom_entry = fields.Char(string='Custom Entry')
    awb_number = fields.Char(string='AWB Number')
    bl_number = fields.Char(string='BL Number')
    consignee_id = fields.Many2one(comodel_name='res.partner', string='Shipper Name')
    ship_to_id = fields.Many2one(comodel_name='res.partner', string='Ship To', domain=[('type', '=', 'delivery')])
    transport_type = fields.Selection(string='Cargo', selection=TRANSPORT_MODES)
    ship_date = fields.Date(string='Shipping Date')


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res.update({
            'custom_entry': move.custom_entry,
            'awb_number': move.awb_number,
            'ship_date': move.ship_date,
            'transport_type': move.transport_type,
            'consignee_id': move.consignee_id.id,
            'ship_to_id': move.ship_to_id.id,
        })
        return res