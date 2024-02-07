# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import timedelta
from datetime import datetime
import calendar
import io
import xlwt
import base64
import uuid


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_start_date(self):
        return datetime.now().date().replace(month=1, day=1)
    
    @api.model
    def default_end_date(self):
        return fields.Date.today()

    start_date = fields.Date('Start Date',default=default_start_date)
    end_date = fields.Date('End Date',default=default_end_date)
    sh_filter_customer_statement_ids = fields.One2many(
        'sh.res.partner.filter.statement',
        'partner_id',
        string='Customer Filtered Statements')
    sh_customer_statement_ids = fields.One2many(
        'account.move',
        string='Customer Statements',
        compute='_compute_customer_statements',
        search='_search_sh_customer_statement_ids')
    sh_customer_zero_to_thiry = fields.Float(
        '0-30', compute='_compute_customer_statements')
    sh_customer_thirty_to_sixty = fields.Float(
        '30-60', compute='_compute_customer_statements')
    sh_customer_sixty_to_ninety = fields.Float(
        '60-90', compute='_compute_customer_statements')
    sh_customer_ninety_plus = fields.Float(
        '90+', compute='_compute_customer_statements')
    sh_customer_total = fields.Float('Total',
                                     compute='_compute_customer_statements')
    sh_dont_send_customer_statement_auto = fields.Boolean(
        "Don't send statement auto ?")
    sh_dont_send_due_customer_statement_auto = fields.Boolean(
        "Don't send Overdue statement auto ?")
    sh_customer_due_statement_ids = fields.One2many(
        'account.move',
        string='Customer Overdue Statements',
        compute='_compute_customer_statements',
        search='_search_sh_customer_due_statement_ids')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.user.company_id)
    sh_cfs_statement_report_url = fields.Char(compute='_compute_cfs_report_url')
    sh_cust_statement_report_url = fields.Char(compute='_compute_cust_report_url')
    sh_cust_due_statement_report_url = fields.Char(compute='_compute_cust_due_report_url')
    report_token = fields.Char("Access Token")
    portal_statement_url_wp = fields.Char(compute='_compute_statement_portal_url_wp')

    def _compute_statement_portal_url_wp(self):
        for rec in self:
            rec.portal_statement_url_wp = False
            if rec.company_id.sh_statement_url_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                ticket_url = ''
                if rec.active:
                    ticket_url = base_url+'/my/customer_statements'
                rec.portal_statement_url_wp = ticket_url

    def _get_token(self):
        """ Get the current record access token """
        if self.report_token:
            return self.report_token
        else:
            report_token = str(uuid.uuid4())
            self.write({'report_token': report_token})
            return report_token

    def get_download_report_url(self):
        url = ''
        if self.id:
            self.ensure_one()
            url = '/download/cfs/' + '%s?access_token=%s' % (
                self.id,
                self._get_token()
            )
        return url
    
    def get_cust_statement_download_report_url(self):
        url = ''
        if self.id:
            self.ensure_one()
            url = '/download/cs/' + '%s?access_token=%s' % (
                self.id,
                self._get_token()
            )
        return url
    
    def get_cust_due_statement_download_report_url(self):
        url = ''
        if self.id:
            self.ensure_one()
            url = '/download/cds/' + '%s?access_token=%s' % (
                self.id,
                self._get_token()
            )
        return url
    
    def _compute_cfs_report_url(self):
        for rec in self:
            rec.sh_cfs_statement_report_url = False
            if rec.company_id.sh_statement_pdf_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                if rec.active:
                    rec.sh_cfs_statement_report_url = base_url+rec.get_download_report_url()
    
    def _compute_cust_report_url(self):
        for rec in self:
            rec.sh_cust_statement_report_url = False
            if rec.company_id.sh_statement_pdf_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                if rec.active:
                    rec.sh_cust_statement_report_url = base_url+rec.get_cust_statement_download_report_url()
    
    def _compute_cust_due_report_url(self):
        for rec in self:
            rec.sh_cust_due_statement_report_url = False
            if rec.company_id.sh_statement_pdf_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                if rec.active:
                    rec.sh_cust_due_statement_report_url = base_url+rec.get_cust_due_statement_download_report_url()
    
    def _get_cfs_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Customer Statement Filter By Date', self.name)
    
    def _get_cs_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Customer Statement', self.name)

    def _get_cds_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Customer Due/Overdue Statement', self.name)
    
    def action_send_filter_customer_whatsapp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        template = self.env.ref(
            'sh_customer_statement.sh_send_customer_filter_whatsapp_email_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_is_customer_statement': True,
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
    
    def action_send_customer_whatsapp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        template = self.env.ref(
            'sh_customer_statement.sh_send_customer_whatsapp_email_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_is_customer_statement': True,
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
    
    def action_send_due_customer_whatsapp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        template = self.env.ref(
            'sh_customer_statement.sh_send_customer_due_whatsapp_email_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_is_customer_statement': True,
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

    def _search_sh_customer_statement_ids(self, operator, value):
        customer_ids = []
        for rec in self.search([]):
            if rec.sh_customer_statement_ids:
                if rec.id not in customer_ids:
                    customer_ids.append(rec.id)
        if operator == '!=':
            return [('id', 'in', customer_ids)]
        else:
            return []

    def _search_sh_customer_due_statement_ids(self, operator, value):
        customer_ids = []
        for rec in self.search([]):
            if rec.sh_customer_due_statement_ids:
                if rec.id not in customer_ids:
                    customer_ids.append(rec.id)
        if operator == '!=':
            return [('id', 'in', customer_ids)]
        else:
            return []

    
    def _compute_customer_statements(self):
        for rec in self:
            if rec.active:
                invoices = self.env['account.move'].sudo().search([
                    ('partner_id', '=', rec.id),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', 'not in', ['draft', 'cancel'])
                ])
                rec.sh_customer_statement_ids = False
                if invoices:
                    rec.sh_customer_statement_ids = [
                        (4, invoice.id) for invoice in invoices
                    ]
                    
                today = fields.Date.today()
                date_before_30 = today - timedelta(days=30)
                date_before_60 = date_before_30 - timedelta(days=30)
                date_before_90 = date_before_60 - timedelta(days=30)
                moves_before_30_days = self.env['account.move'].sudo(
                ).search([('move_type', 'in', ['out_invoice', 'out_refund']),
                          ('partner_id', '=', rec.id),
                          ('invoice_date', '>=', date_before_30),
                          ('invoice_date', '<=', fields.Date.today()),
                          ('state', 'not in', ['draft', 'cancel'])])
                if moves_before_30_days:
                    total_balance = 0.0
                    for move_before_30 in moves_before_30_days:
                        total_balance += move_before_30.sh_balance
                    rec.sh_customer_zero_to_thiry = total_balance
                rec.sh_customer_zero_to_thiry = 0
                moves_before_60_days = self.env['account.move'].sudo(
                ).search([('move_type', 'in', ['out_invoice', 'out_refund']),
                          ('partner_id', '=', rec.id),
                          ('invoice_date', '>=', date_before_60),
                          ('invoice_date', '<=', date_before_30),
                          ('state', 'not in', ['draft', 'cancel'])])
                if moves_before_60_days:
                    total_balance = 0.0
                    for move_before_60 in moves_before_60_days:
                        total_balance += move_before_60.sh_balance
                    rec.sh_customer_thirty_to_sixty = total_balance
                rec.sh_customer_thirty_to_sixty = 0
                moves_before_90_days = self.env['account.move'].sudo(
                ).search([('move_type', 'in', ['out_invoice', 'out_refund']),
                          ('partner_id', '=', rec.id),
                          ('invoice_date', '>=', date_before_90),
                          ('invoice_date', '<=', date_before_60),
                          ('state', 'not in', ['draft', 'cancel'])])
                if moves_before_90_days:
                    total_balance = 0.0
                    for move_before_90 in moves_before_90_days:
                        total_balance += move_before_90.sh_balance
                    rec.sh_customer_sixty_to_ninety = total_balance
                rec.sh_customer_sixty_to_ninety = 0
                moves_90_plus = self.env['account.move'].sudo().search([
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('partner_id', '=', rec.id),
                    ('invoice_date', '<=', date_before_90),
                    ('state', 'not in', ['draft', 'cancel'])
                ])
                if moves_90_plus:
                    total_balance = 0.0
                    for move_before_90_plus in moves_90_plus:
                        total_balance += move_before_90_plus.sh_balance
                    rec.sh_customer_ninety_plus = total_balance
                rec.sh_customer_ninety_plus = 0
                rec.sh_customer_total = rec.sh_customer_zero_to_thiry + rec.sh_customer_thirty_to_sixty + rec.sh_customer_sixty_to_ninety + rec.sh_customer_ninety_plus
                overdue_invoices = False
                if self.env.user.company_id.sh_display_due_statement == 'due':
                    overdue_invoices = invoices.filtered(
                        lambda x: x.invoice_date_due and x.invoice_date_due >= fields.Date.
                        today() and x.amount_residual > 0.00)
                elif self.env.user.company_id.sh_display_due_statement == 'overdue':
                    overdue_invoices = invoices.filtered(
                        lambda x: x.invoice_date_due and x.invoice_date_due < fields.Date.
                        today() and x.amount_residual > 0.00)
                elif self.env.user.company_id.sh_display_due_statement == 'both':
                    overdue_invoices = invoices.filtered(
                        lambda x: x.amount_residual > 0.00)
                if overdue_invoices:
                    rec.sh_customer_due_statement_ids = [
                        (4, overdue_invoice.id)
                        for overdue_invoice in overdue_invoices
                    ]
                else:
                    rec.sh_customer_due_statement_ids = False
            else:
                rec.sh_customer_statement_ids = False
                rec.sh_customer_due_statement_ids = False
                rec.sh_customer_zero_to_thiry = False
                rec.sh_customer_thirty_to_sixty = False
                rec.sh_customer_sixty_to_ninety = False
                rec.sh_customer_total = False
                rec.sh_customer_ninety_plus = False
                
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        if self.filtered(lambda c: c.end_date and c.start_date > c.end_date):
            raise ValidationError(_('start date must be less than end date.'))

    def send_customer_statement(self):
        for rec in self:
            if rec.active and rec.sh_customer_statement_ids:
                template = self.env.ref(
                    'sh_customer_statement.sh_customer_statement_mail_template'
                )
                if template:
                    mail = template.sudo().send_mail(rec.id, force_send=True)
                    mail_id = self.env['mail.mail'].sudo().browse(mail)
                    if mail_id:
                        self.env['sh.customer.mail.history'].sudo().create({
                            'name':
                            'Customer Account Statement',
                            'sh_statement_type':
                            'customer_statement',
                            'sh_current_date':
                            fields.Datetime.now(),
                            'sh_partner_id':
                            rec.id,
                            'sh_mail_id':
                            mail_id.id,
                            'sh_mail_status':
                            mail_id.state,
                        })

    def send_customer_overdue_statement(self):
        for rec in self:
            if rec.active and rec.sh_customer_due_statement_ids:
                template = self.env.ref(
                    'sh_customer_statement.sh_customer_due_statement_mail_template'
                )
                if template:
                    mail = template.sudo().send_mail(rec.id, force_send=True)
                    mail_id = self.env['mail.mail'].sudo().browse(mail)
                    if mail_id:
                        self.env['sh.customer.mail.history'].sudo().create({
                            'name':
                            'Customer Account Overdue Statement',
                            'sh_statement_type':
                            'customer_overdue_statement',
                            'sh_current_date':
                            fields.Datetime.now(),
                            'sh_partner_id':
                            rec.id,
                            'sh_mail_id':
                            mail_id.id,
                            'sh_mail_status':
                            mail_id.state,
                        })

    def action_print_customer_statement(self):
        return self.env.ref(
            'sh_customer_statement.action_report_sh_customer_statement'
        ).report_action(self)

    def action_send_customer_statement(self):
        self.ensure_one()
        template = self.env.ref(
            'sh_customer_statement.sh_customer_statement_mail_template')
        if template:
            mail = template.sudo().send_mail(self.id, force_send=True)
            mail_id = self.env['mail.mail'].sudo().browse(mail)
            if mail_id:
                self.env['sh.customer.mail.history'].sudo().create({
                    'name':
                    'Customer Account Statement',
                    'sh_statement_type':
                    'customer_statement',
                    'sh_current_date':
                    fields.Datetime.now(),
                    'sh_partner_id':
                    self.id,
                    'sh_mail_id':
                    mail_id.id,
                    'sh_mail_status':
                    mail_id.state,
                })

    def action_print_customer_statement_xls(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        normal = xlwt.easyxf(
            'font:bold True;align: horiz center;align: vert center')
        cyan_text = xlwt.easyxf(
            'font:bold True,color aqua;align: horiz center;align: vert center')
        green_text = xlwt.easyxf(
            'font:bold True,color green;align: horiz center;align: vert center'
        )
        red_text = xlwt.easyxf(
            'font:bold True,color red;align: horiz center;align: vert center')
        bold_center = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        totals = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        worksheet = workbook.add_sheet(u'Customer Statement',
                                       cell_overwrite_ok=True)

        worksheet.row(5).height = 400
        worksheet.row(12).height = 400
        worksheet.row(13).height = 400
        worksheet.row(10).height = 350
        worksheet.row(11).height = 350
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        worksheet.col(6).width = 5500
        worksheet.col(0).width = 5500
        worksheet.col(1).width = 6000
        worksheet.write_merge(2, 3, 0, 6, self.name, heading_format)
        worksheet.write(5, 0, "Number", bold_center)
        worksheet.write(5, 1, "Account", bold_center)
        worksheet.write(5, 2, "Date", bold_center)
        worksheet.write(5, 3, "Due Date", bold_center)
        worksheet.write(5, 4, "Total Amount", bold_center)
        worksheet.write(5, 5, "Paid Amount", bold_center)
        worksheet.write(5, 6, "Balance", bold_center)

        total_amount = 0
        total_paid_amount = 0
        total_balance = 0
        k = 6

        if self.sh_customer_statement_ids:
            for i in self.sh_customer_statement_ids:
                for j in i:
                    worksheet.row(k).height = 350
                    if j.amount_total_signed == j.sh_balance:
                        worksheet.write(k, 0, j.name, cyan_text)
                        worksheet.write(
                            k, 1, self.property_account_receivable_id.name,
                            cyan_text)
                        worksheet.write(k, 2, str(j.invoice_date), cyan_text)
                        if j.invoice_date_due:
                            worksheet.write(k, 3, str(j.invoice_date_due), cyan_text)
                        else:
                            worksheet.write(k, 3, '', cyan_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.amount_total_signed)), cyan_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_paid_amount)), cyan_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_balance)), cyan_text)
                    elif j.sh_balance == 0:
                        worksheet.write(k, 0, j.name, green_text)
                        worksheet.write(
                            k, 1, self.property_account_receivable_id.name,
                            green_text)
                        worksheet.write(k, 2, str(j.invoice_date), green_text)
                        if j.invoice_date_due:
                            worksheet.write(k, 3, str(j.invoice_date_due), green_text)
                        else:
                            worksheet.write(k, 3, '', green_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.amount_total_signed)), green_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_paid_amount)), green_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_balance)), green_text)
                    else:
                        worksheet.write(k, 0, j.name, red_text)
                        worksheet.write(
                            k, 1, self.property_account_receivable_id.name,
                            red_text)
                        worksheet.write(k, 2, str(j.invoice_date), red_text)
                        if j.invoice_date_due:
                            worksheet.write(k, 3, str(j.invoice_date_due), red_text)
                        else:
                            worksheet.write(k, 3, '', red_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.amount_total_signed)), red_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_paid_amount)), red_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_balance)), red_text)
                    k = k + 1
                total_amount = total_amount + j.amount_total_signed
                total_paid_amount = total_paid_amount + j.sh_paid_amount
                total_balance = total_balance + j.sh_balance

        if self.sh_customer_statement_ids:
            worksheet.write(
                k, 4,
                str("{:.2f}".format(total_amount)),
                totals)
            worksheet.row(k).height = 350
            worksheet.write(
                k, 5,
                str("{:.2f}".format(total_paid_amount)), totals)
            worksheet.write(
                k, 6,
                str("{:.2f}".format(total_balance)), totals)
        worksheet.write(k + 3, 0, 'Gap Between Days', bold_center)
        worksheet.write(k + 3, 1, '0-30(Days)', bold_center)
        worksheet.write(k + 3, 2, '30-60(Days)', bold_center)
        worksheet.write(k + 3, 3, '60-90(Days)', bold_center)
        worksheet.write(k + 3, 4, '90+(Days)', bold_center)
        worksheet.write(k + 3, 5, 'Total', bold_center)
        worksheet.write(k + 4, 0, 'Balance Amount', bold_center)
        if self.sh_customer_statement_ids:
            worksheet.write(
                k + 4, 1,
                str("{:.2f}".format(self.sh_customer_zero_to_thiry)), normal)
            worksheet.write(
                k + 4, 2,
                str("{:.2f}".format(self.sh_customer_thirty_to_sixty)), normal)
            worksheet.write(
                k + 4, 3,
                str("{:.2f}".format(self.sh_customer_sixty_to_ninety)), normal)
            worksheet.write(
                k + 4, 4,
                str("{:.2f}".format(self.sh_customer_ninety_plus)), normal)
            worksheet.write(
                k + 4, 5,
                str("{:.2f}".format(self.sh_customer_total)), normal)

        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": "Customer Statement.xls",
            "res_model": "ir.ui.view",
            # 'datas_fname': 'Customer Statement.xls',
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search([('name', '=', 'Customer Statement'),
                                          ('type', '=', 'binary'),
                                          ('res_model', '=', 'ir.ui.view')],
                                         limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }

    def action_print_customer_due_statement(self):
        return self.env.ref(
            'sh_customer_statement.action_report_sh_customer_due_statement'
        ).report_action(self)

    def action_send_customer_due_statement(self):
        self.ensure_one()
        template = self.env.ref(
            'sh_customer_statement.sh_customer_due_statement_mail_template')
        if template:
            mail = template.sudo().send_mail(self.id, force_send=True)
            mail_id = self.env['mail.mail'].sudo().browse(mail)
            if mail_id:
                self.env['sh.customer.mail.history'].sudo().create({
                    'name':
                    'Customer Account Overdue Statement',
                    'sh_statement_type':
                    'customer_overdue_statement',
                    'sh_current_date':
                    fields.Datetime.now(),
                    'sh_partner_id':
                    self.id,
                    'sh_mail_id':
                    mail_id.id,
                    'sh_mail_status':
                    mail_id.state,
                })

    def action_print_customer_due_statement_xls(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        red_text = xlwt.easyxf(
            'font:bold True,color red;align: horiz center;align: vert center')
        center_text = xlwt.easyxf(
            'align: horiz center;align: vert center')
        bold_center = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        date = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin;align: vert center;align: horiz left'
        )
        worksheet = workbook.add_sheet(u'Customer Overdue Statement',
                                       cell_overwrite_ok=True)

        now = datetime.now()
        today_date = now.strftime("%d/%m/%Y %H:%M:%S")

        worksheet.write(1, 0, str(str("Date") + str(": ") + str(today_date)),
                        date)
        worksheet.row(1).height = 350
        worksheet.row(6).height = 350
        worksheet.col(0).width = 8000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        worksheet.col(6).width = 5500
        worksheet.row(11).height = 350

        worksheet.write_merge(3, 4, 0, 6, self.name, heading_format)
        worksheet.write(6, 0, "Number", bold_center)
        worksheet.write(6, 1, "Account", bold_center)
        worksheet.write(6, 2, "Date", bold_center)
        worksheet.write(6, 3, "Due Date", bold_center)
        worksheet.write(6, 4, "Total Amount", bold_center)
        worksheet.write(6, 5, "Paid Amount", bold_center)
        worksheet.write(6, 6, "Balance", bold_center)

        total_amount = 0
        total_paid_amount = 0
        total_balance = 0
        k = 7

        if self.sh_customer_due_statement_ids:
            for i in self.sh_customer_due_statement_ids:
                worksheet.row(k).height = 350
                for j in i:
                    if j.invoice_date_due and j.sh_today and j.invoice_date_due < j.sh_today:
                        worksheet.write(k, 0, j.name, red_text)
                        worksheet.write(k, 1,
                                        self.property_account_receivable_id.name,
                                        red_text)
                        worksheet.write(k, 2, str(j.invoice_date), red_text)
                        if j.invoice_date_due:
                            worksheet.write(k, 3, str(j.invoice_date_due), red_text)
                        else:
                            worksheet.write(k, 3, '', red_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.amount_total_signed)), red_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_paid_amount)), red_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_balance)), red_text)
                    else:
                        worksheet.write(k, 0, j.name, center_text)
                        worksheet.write(k, 1,
                                        self.property_account_receivable_id.name,
                                        center_text)
                        worksheet.write(k, 2, str(j.invoice_date), center_text)
                        if j.invoice_date_due:
                            worksheet.write(k, 3, str(j.invoice_date_due), center_text)
                        else:
                            worksheet.write(k, 3, '', center_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.amount_total_signed)), center_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_paid_amount)), center_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_balance)), center_text)
                    k = k + 1
                total_amount = total_amount + j.amount_total_signed
                total_paid_amount = total_paid_amount + j.sh_paid_amount
                total_balance = total_balance + j.sh_balance
        if self.sh_customer_due_statement_ids:
            worksheet.write(
                k, 4,
                str("{:.2f}".format(total_amount)),
                bold_center)
            worksheet.row(k).height = 350
            worksheet.write(
                k, 5,
                str("{:.2f}".format(total_paid_amount)), bold_center)
            worksheet.write(
                k, 6,
                str("{:.2f}".format(total_balance)), bold_center)

        fp = io.BytesIO()
        workbook.save(fp)

        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": "Customer Overdue Statement.xls",
            "res_model": "ir.ui.view",
            # 'datas_fname': 'Customer Overdue Statement.xls',
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search(
            [('name', '=', 'Customer Overdue Statement'),
             ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')],
            limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }

    def action_get_customer_statement(self):
        self.ensure_one()
        if self.active and self.start_date and self.end_date:
            self.sh_filter_customer_statement_ids.unlink()
            moves = self.env['account.move'].sudo().search([
                ('partner_id', '=', self.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('invoice_date', '>=', self.start_date),
                ('invoice_date', '<=', self.end_date),
                ('state', 'not in', ['draft', 'cancel'])
            ])
            if moves:
                if self.sh_filter_customer_statement_ids:
                    self.sh_filter_customer_statement_ids.unlink()
                statement_lines = []
                for move in moves:
                    statement_vals = {
                        'sh_account': self.property_account_receivable_id.name,
                        'name': str(move.name),
                        'currency_id': move.currency_id.id,
                        'sh_filter_invoice_date': move.invoice_date,
                        'sh_filter_due_date': move.invoice_date_due,
                        'sh_filter_amount': move.amount_total_signed,
                        'sh_filter_paid_amount': move.sh_paid_amount,
                        'sh_filter_balance': move.sh_balance
                    }
                    statement_lines.append((0, 0, statement_vals))
                self.sh_filter_customer_statement_ids = statement_lines

    def action_print_filter_customer_statement(self):
        return self.env.ref(
            'sh_customer_statement.action_report_sh_customer_filtered_statement'
        ).report_action(self)

    def action_send_filter_customer_statement(self):
        self.ensure_one()
        template = self.env.ref(
            'sh_customer_statement.sh_customer_filter_statement_mail_template')
        if template:
            mail = template.sudo().send_mail(self.id, force_send=True)
            mail_id = self.env['mail.mail'].sudo().browse(mail)
            if mail_id:
                self.env['sh.customer.mail.history'].sudo().create({
                    'name':
                    'Customer Account Statement by Date',
                    'sh_statement_type':
                    'customer_statement_filter',
                    'sh_current_date':
                    fields.Datetime.now(),
                    'sh_partner_id':
                    self.id,
                    'sh_mail_id':
                    mail_id.id,
                    'sh_mail_status':
                    mail_id.state,
                })

    def action_print_filter_customer_statement_xls(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        normal = xlwt.easyxf(
            'font:bold True;align: horiz center;align: vert center')
        cyan_text = xlwt.easyxf(
            'font:bold True,color aqua;align: horiz center;align: vert center')
        green_text = xlwt.easyxf(
            'font:bold True,color green;align: horiz center;align: vert center'
        )
        red_text = xlwt.easyxf(
            'font:bold True,color red;align: horiz center;align: vert center')
        bold_center = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        date = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: vert center;align: horiz right;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        totals = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        worksheet = workbook.add_sheet(u'Customer Statement Filter By Date',
                                       cell_overwrite_ok=True)

        worksheet.row(1).height = 380
        worksheet.row(2).height = 320
        worksheet.row(8).height = 400
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        worksheet.col(6).width = 5500
        worksheet.col(0).width = 5500
        worksheet.col(1).width = 6000
        worksheet.write(1, 0, "Date From", date)
        if self.start_date:
            worksheet.write(1, 1, str(self.start_date), normal)
        worksheet.write(1, 2, "Date To", date)
        if self.end_date:
            worksheet.write(1, 3, str(self.end_date), normal)
        worksheet.write_merge(4, 5, 0, 6, self.name, heading_format)
        worksheet.write(8, 0, "Number", bold_center)
        worksheet.write(8, 1, "Account", bold_center)
        worksheet.write(8, 2, "Date", bold_center)
        worksheet.write(8, 3, "Due Date", bold_center)
        worksheet.write(8, 4, "Total Amount", bold_center)
        worksheet.write(8, 5, "Paid Amount", bold_center)
        worksheet.write(8, 6, "Balance", bold_center)

        total_amount = 0
        total_paid_amount = 0
        total_balance = 0
        k = 9

        if self.sh_filter_customer_statement_ids:
            for i in self.sh_filter_customer_statement_ids:
                for j in i:
                    worksheet.row(k).height = 350
                    if j.sh_filter_amount == j.sh_filter_balance:
                        worksheet.write(k, 0, j.name, cyan_text)
                        worksheet.write(
                            k, 1, self.property_account_receivable_id.name,
                            cyan_text)
                        worksheet.write(k, 2, str(j.sh_filter_invoice_date),
                                        cyan_text)
                        if j.sh_filter_due_date:
                            worksheet.write(k, 3, str(j.sh_filter_due_date),
                                            cyan_text)
                        else:
                            worksheet.write(k, 3, '',
                                cyan_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_amount)),
                            cyan_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_paid_amount)),
                            cyan_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_balance)),
                            cyan_text)
                    elif j.sh_filter_balance == 0:
                        worksheet.write(k, 0, j.name, green_text)
                        worksheet.write(
                            k, 1, self.property_account_receivable_id.name,
                            green_text)
                        worksheet.write(k, 2, str(j.sh_filter_invoice_date),
                                        green_text)
                        if j.sh_filter_due_date:
                            worksheet.write(k, 3, str(j.sh_filter_due_date),
                                            green_text)
                        else:
                            worksheet.write(k, 3, '',
                                            green_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_amount)),
                            green_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_paid_amount)),
                            green_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_balance)),
                            green_text)
                    else:
                        worksheet.write(k, 0, j.name, red_text)
                        worksheet.write(
                            k, 1, self.property_account_receivable_id.name,
                            red_text)
                        worksheet.write(k, 2, str(j.sh_filter_invoice_date),
                                        red_text)
                        if j.sh_filter_due_date:
                            worksheet.write(k, 3, str(j.sh_filter_due_date),
                                            red_text)
                        else:
                            worksheet.write(k, 3, '',
                                            red_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_amount)), red_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_paid_amount)),
                            red_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_balance)),
                            red_text)

                    k = k + 1
                total_amount = total_amount + j.sh_filter_amount
                total_paid_amount = total_paid_amount + j.sh_filter_paid_amount
                total_balance = total_balance + j.sh_filter_balance
        if self.sh_filter_customer_statement_ids:
            worksheet.write(
                k, 4,
                str("{:.2f}".format(total_amount)),
                totals)
            worksheet.row(k).height = 350
            worksheet.write(
                k, 5,
                str("{:.2f}".format(total_paid_amount)), totals)
            worksheet.write(
                k, 6,
                str("{:.2f}".format(total_balance)), totals)

        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": "Customer Statement Filter By Date.xls",
            "res_model": "ir.ui.view",
            # 'datas_fname': 'Customer Statement Filter By Date.xls',
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search(
            [('name', '=', 'Customer Statement Filter By Date'),
             ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')],
            limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }

    def action_view_customer_history(self):
        self.ensure_one()
        return {
            'name': 'Mail Log History',
            'type': 'ir.actions.act_window',
            'res_model': 'sh.customer.mail.history',
            'view_mode': 'tree,form',
            'domain': [('sh_partner_id', '=', self.id)],
            'target': 'current',
        }

    @api.model
    def _run_auto_send_customer_statements(self):
        partner_ids = self.env['res.partner'].sudo().search([])
        for partner in partner_ids:
            #for customer
            if partner.customer:
                #for statement
                if not partner.sh_dont_send_customer_statement_auto:
                    if self.env.user.company_id.sh_customer_statement_auto_send and partner.sh_customer_statement_ids:
                        if self.env.user.company_id.sh_customer_statement_action == 'daily':
                            if self.env.user.company_id.sh_cus_daily_statement_template_id:
                                mail = self.env.user.company_id.sh_cus_daily_statement_template_id.sudo(
                                ).send_mail(partner.id, force_send=True)
                                mail_id = self.env['mail.mail'].sudo().browse(
                                    mail)
                                if mail_id and self.env.user.company_id.sh_cust_create_log_history:
                                    self.env['sh.customer.mail.history'].sudo(
                                    ).create({
                                        'name':
                                        'Customer Account Statement',
                                        'sh_statement_type':
                                        'customer_statement',
                                        'sh_current_date':
                                        fields.Datetime.now(),
                                        'sh_partner_id':
                                        partner.id,
                                        'sh_mail_id':
                                        mail_id.id,
                                        'sh_mail_status':
                                        mail_id.state,
                                    })
                        elif self.env.user.company_id.sh_customer_statement_action == 'weekly':
                            today = fields.Date.today().weekday()
                            if int(self.env.user.company_id.sh_cust_week_day
                                   ) == today:
                                if self.env.user.company_id.sh_cust_weekly_statement_template_id:
                                    mail = self.env.user.company_id.sh_cust_weekly_statement_template_id.sudo(
                                    ).send_mail(partner.id, force_send=True)
                                    mail_id = self.env['mail.mail'].sudo(
                                    ).browse(mail)
                                    if mail_id and self.env.user.company_id.sh_cust_create_log_history:
                                        self.env[
                                            'sh.customer.mail.history'].sudo(
                                            ).create({
                                                'name':
                                                'Customer Account Statement',
                                                'sh_statement_type':
                                                'customer_statement',
                                                'sh_current_date':
                                                fields.Datetime.now(),
                                                'sh_partner_id':
                                                partner.id,
                                                'sh_mail_id':
                                                mail_id.id,
                                                'sh_mail_status':
                                                mail_id.state,
                                            })
                        elif self.env.user.company_id.sh_customer_statement_action == 'monthly':
                            monthly_day = self.env.user.company_id.sh_cust_monthly_date
                            today = fields.Date.today()
                            today_date = today.day
                            if self.env.user.company_id.sh_cust_monthly_end:
                                last_day = calendar.monthrange(
                                    today.year, today.month)[1]
                                if today_date == last_day:
                                    if self.env.user.company_id.sh_cust_monthly_template_id:
                                        mail = self.env.user.company_id.sh_cust_monthly_template_id.sudo(
                                        ).send_mail(partner.id,
                                                    force_send=True)
                                        mail_id = self.env['mail.mail'].sudo(
                                        ).browse(mail)
                                        if mail_id and self.env.user.company_id.sh_cust_create_log_history:
                                            self.env[
                                                'sh.customer.mail.history'].sudo(
                                                ).create({
                                                    'name':
                                                    'Customer Account Statement',
                                                    'sh_statement_type':
                                                    'customer_statement',
                                                    'sh_current_date':
                                                    fields.Datetime.now(),
                                                    'sh_partner_id':
                                                    partner.id,
                                                    'sh_mail_id':
                                                    mail_id.id,
                                                    'sh_mail_status':
                                                    mail_id.state,
                                                })
                            else:
                                if today_date == monthly_day:
                                    if self.env.user.company_id.sh_cust_monthly_template_id:
                                        mail = self.env.user.company_id.sh_cust_monthly_template_id.sudo(
                                        ).send_mail(partner.id,
                                                    force_send=True)
                                        mail_id = self.env['mail.mail'].sudo(
                                        ).browse(mail)
                                        if mail_id and self.env.user.company_id.sh_cust_create_log_history:
                                            self.env[
                                                'sh.customer.mail.history'].sudo(
                                                ).create({
                                                    'name':
                                                    'Customer Account Statement',
                                                    'sh_statement_type':
                                                    'customer_statement',
                                                    'sh_current_date':
                                                    fields.Datetime.now(),
                                                    'sh_partner_id':
                                                    partner.id,
                                                    'sh_mail_id':
                                                    mail_id.id,
                                                    'sh_mail_status':
                                                    mail_id.state,
                                                })
                        elif self.env.user.company_id.sh_customer_statement_action == 'yearly':
                            today = fields.Date.today()
                            today_date = today.day
                            today_month = today.strftime("%B").lower()
                            if self.env.user.company_id.sh_cust_yearly_date == today_date and self.env.user.company_id.sh_cust_yearly_month == today_month:
                                if self.env.user.company_id.sh_cust_yearly_template_id:
                                    mail = self.env.user.company_id.sh_cust_yearly_template_id.sudo(
                                    ).send_mail(partner.id, force_send=True)
                                    mail_id = self.env['mail.mail'].sudo(
                                    ).browse(mail)
                                    if mail_id and self.env.user.company_id.sh_cust_create_log_history:
                                        self.env[
                                            'sh.customer.mail.history'].sudo(
                                            ).create({
                                                'name':
                                                'Customer Account Statement',
                                                'sh_statement_type':
                                                'customer_statement',
                                                'sh_current_date':
                                                fields.Datetime.now(),
                                                'sh_partner_id':
                                                partner.id,
                                                'sh_mail_id':
                                                mail_id.id,
                                                'sh_mail_status':
                                                mail_id.state,
                                            })
                #for overdue statement
                if not partner.sh_dont_send_due_customer_statement_auto:
                    if self.env.user.company_id.sh_customer_due_statement_auto_send and partner.sh_customer_due_statement_ids:
                        if self.env.user.company_id.sh_customer_due_statement_action == 'daily':
                            if self.env.user.company_id.sh_cus_due_daily_statement_template_id:
                                mail = self.env.user.company_id.sh_cus_due_daily_statement_template_id.sudo(
                                ).send_mail(partner.id, force_send=True)
                                mail_id = self.env['mail.mail'].sudo().browse(
                                    mail)
                                if mail_id and self.env.user.company_id.sh_cust_due_create_log_history:
                                    self.env['sh.customer.mail.history'].sudo(
                                    ).create({
                                        'name':
                                        'Customer Account Overdue Statement',
                                        'sh_statement_type':
                                        'customer_overdue_statement',
                                        'sh_current_date':
                                        fields.Datetime.now(),
                                        'sh_partner_id':
                                        partner.id,
                                        'sh_mail_id':
                                        mail_id.id,
                                        'sh_mail_status':
                                        mail_id.state,
                                    })
                        elif self.env.user.company_id.sh_customer_due_statement_action == 'weekly':
                            today = fields.Date.today().weekday()
                            if int(self.env.user.company_id.
                                   sh_cust_due_week_day) == today:
                                if self.env.user.company_id.sh_cust_due_weekly_statement_template_id:
                                    mail = self.env.user.company_id.sh_cust_due_weekly_statement_template_id.sudo(
                                    ).send_mail(partner.id, force_send=True)
                                    mail_id = self.env['mail.mail'].sudo(
                                    ).browse(mail)
                                    if mail_id and self.env.user.company_id.sh_cust_due_create_log_history:
                                        self.env['sh.customer.mail.history'].sudo(
                                        ).create({
                                            'name':
                                            'Customer Account Overdue Statement',
                                            'sh_statement_type':
                                            'customer_overdue_statement',
                                            'sh_current_date':
                                            fields.Datetime.now(),
                                            'sh_partner_id':
                                            partner.id,
                                            'sh_mail_id':
                                            mail_id.id,
                                            'sh_mail_status':
                                            mail_id.state,
                                        })
                        elif self.env.user.company_id.sh_customer_due_statement_action == 'monthly':
                            monthly_day = self.env.user.company_id.sh_cust_due_monthly_date
                            today = fields.Date.today()
                            today_date = today.day
                            if self.env.user.company_id.sh_cust_due_monthly_end:
                                last_day = calendar.monthrange(
                                    today.year, today.month)[1]
                                if today_date == last_day:
                                    if self.env.user.company_id.sh_cust_due_monthly_template_id:
                                        mail = self.env.user.company_id.sh_cust_due_monthly_template_id.sudo(
                                        ).send_mail(partner.id,
                                                    force_send=True)
                                        mail_id = self.env['mail.mail'].sudo(
                                        ).browse(mail)
                                        if mail_id and self.env.user.company_id.sh_cust_due_create_log_history:
                                            self.env[
                                                'sh.customer.mail.history'].sudo(
                                                ).create({
                                                    'name':
                                                    'Customer Account Overdue Statement',
                                                    'sh_statement_type':
                                                    'customer_overdue_statement',
                                                    'sh_current_date':
                                                    fields.Datetime.now(),
                                                    'sh_partner_id':
                                                    partner.id,
                                                    'sh_mail_id':
                                                    mail_id.id,
                                                    'sh_mail_status':
                                                    mail_id.state,
                                                })
                            else:
                                if today_date == monthly_day:
                                    if self.env.user.company_id.sh_cust_due_monthly_template_id:
                                        mail = self.env.user.company_id.sh_cust_due_monthly_template_id.sudo(
                                        ).send_mail(partner.id,
                                                    force_send=True)
                                        mail_id = self.env['mail.mail'].sudo(
                                        ).browse(mail)
                                        if mail_id and self.env.user.company_id.sh_cust_due_create_log_history:
                                            self.env[
                                                'sh.customer.mail.history'].sudo(
                                                ).create({
                                                    'name':
                                                    'Customer Account Overdue Statement',
                                                    'sh_statement_type':
                                                    'customer_overdue_statement',
                                                    'sh_current_date':
                                                    fields.Datetime.now(),
                                                    'sh_partner_id':
                                                    partner.id,
                                                    'sh_mail_id':
                                                    mail_id.id,
                                                    'sh_mail_status':
                                                    mail_id.state,
                                                })

                        elif self.env.user.company_id.sh_customer_due_statement_action == 'yearly':
                            today = fields.Date.today()
                            today_date = today.day
                            today_month = today.strftime("%B").lower()
                            if self.env.user.company_id.sh_cust_due_yearly_date == today_date and self.env.user.company_id.sh_cust_due_yearly_month == today_month:
                                if self.env.user.company_id.sh_cust_due_yearly_template_id:
                                    mail = self.env.user.company_id.sh_cust_due_yearly_template_id.sudo(
                                    ).send_mail(partner.id, force_send=True)
                                    mail_id = self.env['mail.mail'].sudo(
                                    ).browse(mail)
                                    if mail_id and self.env.user.company_id.sh_cust_due_create_log_history:
                                        self.env['sh.customer.mail.history'].sudo(
                                        ).create({
                                            'name':
                                            'Customer Account Overdue Statement',
                                            'sh_statement_type':
                                            'customer_overdue_statement',
                                            'sh_current_date':
                                            fields.Datetime.now(),
                                            'sh_partner_id':
                                            partner.id,
                                            'sh_mail_id':
                                            mail_id.id,
                                            'sh_mail_status':
                                            mail_id.state,
                                        })


class FilterCustomerStateMent(models.Model):
    _name = 'sh.res.partner.filter.statement'
    _description = 'Filter Customer Statement'

    partner_id = fields.Many2one('res.partner', 'Partner')
    name = fields.Char('Invoice Number')
    currency_id = fields.Many2one('res.currency', 'Currency')
    sh_account = fields.Char('Account')
    sh_filter_invoice_date = fields.Date('Invoice Date')
    sh_filter_due_date = fields.Date('Invoice Due Date')
    sh_filter_amount = fields.Monetary('Total Amount')
    sh_filter_paid_amount = fields.Monetary('Paid Amount')
    sh_filter_balance = fields.Monetary('Balance')
