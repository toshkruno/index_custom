# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow over credit?')
    credit_approval_status = fields.Selection([
        ('not_approved', 'Not Approved'),
        ('approved', 'Approved')], string="Approval status")

    def write(self, vals):
        if vals.get('over_credit'):
            credit_approval_recs = self.env['multi.approval'].search([('credit_partner', '=', self.id),
                                                                      ('state', 'in', ['Draft', 'Submitted'])
                                                                      ])
            if not credit_approval_recs:
                vals['credit_approval_status'] = 'not_approved'
                name = 'Allow over credit Approval for ' + self.name
                approval_vals = {
                    'credit_partner': self.id,
                    'name': name,
                    'type_id': self.env.ref('partner_credit_limit.allow_credit_approval_type').id,
                    'user_id': self.env.user.id
                }
                approval_rec = self.env['multi.approval'].sudo().create(approval_vals)
                approval_rec.action_submit()
        res = super(ResPartner, self).write(vals)
        if not self.over_credit and self.credit_approval_status == 'approved':
            self.credit_approval_status = 'not_approved'
        return res
