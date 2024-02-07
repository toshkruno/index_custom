
from odoo import models, fields, api

class PaymentOrder(models.Model):
    _inherit='account.payment.order'


    def generated2uploaded(self):
        res = super(PaymentOrder, self).generated2uploaded()
        self.ensure_one()
        template_id=self.env.ref('account_payment_order.email_template_payment_order').id
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
            ctx = {
                'default_model': 'account.payment.order',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'proforma': self.env.context.get('proforma', False),
                'force_email': True,
                'model_description': self.with_context(lang=lang).name,
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }
        return res