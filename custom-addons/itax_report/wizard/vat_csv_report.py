# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Corensult Solutions. (Website: www.corensultsolutions.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################
from odoo import fields, models, api, _
import base64
import datetime
from odoo.exceptions import ValidationError
import csv
import calendar
import os
import tempfile
import logging


_logger = logging.getLogger(__name__)


class VatReportWizard(models.TransientModel):
    _name = 'vat.report.wizard'
    _description = "Vat Report"

    month_of = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'Jun'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], string="Month")
    year_of = fields.Char(string="Year")
    tax_id = fields.Many2many('account.tax', string="Tax")


    def print_sale_vat_xlsx_report(self):
        lastDayOfMonth = calendar.monthrange(
            int(self.year_of), int(self.month_of))[1]
        startDate = '%s-%s-01' % (self.year_of, self.month_of)
        endDate = '%s-%s-%s' % (self.year_of, self.month_of, lastDayOfMonth)

        invoice_objs = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('date', '>=', startDate),
            ('date', '<=', endDate),
            ('company_id', '=', self.env.company.id)
        ])
        file_fd, file_path = tempfile.mkstemp(
            suffix='.csv', prefix='sale_vat_report')
        csv_data = []
        if invoice_objs:
            for inv in invoice_objs:
                rInv = False
                has_tax = False
                if inv.move_type == 'out_refund' and inv.reversed_entry_id:
                    rInv = self.env['account.move'].search([
                        ('id', '=', inv.reversed_entry_id.id)])
                amount = 0.0
                for invoice_line in inv.line_ids:
                    for rec in self.tax_id:
                        for tax in invoice_line.tax_ids:
                            if rec.id == tax.id:
                                has_tax = True

                                price = invoice_line.price_unit * (1 - (invoice_line.discount or 0.0) / 100.0)
                                taxes = tax.compute_all(price, invoice_line.currency_id, invoice_line.quantity, product=invoice_line.product_id or False, partner=invoice_line.partner_id)
                                if inv.move_type == 'out_refund':
                                    amount += (-1 * taxes['taxes'][0]['base'])
                                else:
                                    amount += taxes['taxes'][0]['base']
                                
                account = ''
                for invoice_line in inv.invoice_line_ids:
                    account = invoice_line.account_id.name
                    continue
                    
                if has_tax:
                    # if inv.partner_id.vat:
                        data = [inv.partner_id.vat or '',
                                inv.partner_id.name or '',
                                inv.company_id.company_registry or '',
                                inv.date.strftime("%d/%m/%Y"),
                                inv.name or '',
                                account,
                                amount * inv.currency_id._get_conversion_rate(inv.currency_id, inv.company_id.currency_id, inv.company_id, inv.invoice_date),
                                '',
                                inv.reversed_entry_id.name if rInv else '',
                                inv.reversed_entry_id.date.strftime("%d/%m/%Y") if rInv else '', ]

                        csv_data.append(data)
                   
            with open(file_path, "w") as writeFile:
                writer = csv.writer(writeFile)
                # writer.writerows([[
                #'PIN Number',
                #'Customer Name',
                #'ETR Number',
                #'Invoice Date',
                #'Invoice Number',
                #'Description of Goods/Services',
                #'Taxable Amount',
                #'Amount of VAT',
                #'Relevant Invoice Number',
                #'Relevant Invoice Date'
                # ]])
                writer.writerows(csv_data)
            writeFile.close()

            result_file = open(file_path, 'rb').read()
            attachment_id = self.env['wizard.excel.report'].create({
                'name': 'Sales - %s %s.csv' % (calendar.month_name[int(self.month_of)], self.year_of),
                'report': base64.b64encode(result_file)
            })
            try:
                os.unlink(file_path)
            except (OSError, IOError):
                _logger.error(
                    'Error when trying to remove file %s' % file_path)

            return {
                'name': _('Odoo'),
                'context': self.env.context,
                'view_mode': 'form',
                'res_model': 'wizard.excel.report',
                'res_id': attachment_id.id,
                'data': None,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise ValidationError(
                _('Invoice are Not Present in this month!!!'))

    def print_purchase_vat_xlsx_report(self):
        lastDayOfMonth = calendar.monthrange(
            int(self.year_of), int(self.month_of))[1]
        startDate = '%s-%s-01' % (self.year_of, self.month_of)
        endDate = '%s-%s-%s' % (self.year_of, self.month_of, lastDayOfMonth)

        invoice_objs = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('date', '>=', startDate),
            ('date', '<=', endDate)
        ])
        file_fd, file_path = tempfile.mkstemp(
            suffix='.csv', prefix='purchase_vat_report')
        csv_data = []
        if invoice_objs:
            for inv in invoice_objs:
                rInv = False
                has_tax = False
                if inv.move_type == 'in_refund' and inv.reversed_entry_id:
                    rInv = self.env['account.move'].search([
                        ('id', '=', inv.reversed_entry_id.id)])
                amount = 0.0
                for invoice_line in inv.line_ids:
                    for rec in self.tax_id:
                        for tax in invoice_line.tax_ids:
                            if rec.id == tax.id:
                                has_tax = True
                                price = invoice_line.price_unit * (1 - (invoice_line.discount or 0.0) / 100.0)
                                taxes = tax.compute_all(price, invoice_line.currency_id, invoice_line.quantity, product=invoice_line.product_id or False, partner=invoice_line.partner_id)
                                if inv.move_type == 'in_refund':
                                    amount += (-1 * taxes['taxes'][0]['base'])
                                else:
                                    amount += taxes['taxes'][0]['base']
                account = ''
                for invoice_line in inv.invoice_line_ids:
                    account = invoice_line.account_id.name
                    continue
                    
                if has_tax:
                    # if inv.partner_id.vat:
                        data = [inv.partner_id.category_id.name,
                                inv.partner_id.vat,
                                inv.partner_id.name,
                                inv.date.strftime("%d/%m/%Y"),
                                inv.credit_note_number if inv.move_type == 'in_refund' else inv.ref,
                                account,
                                inv.custom_entry_number if inv.custom_entry_number else '',
                                amount * inv.currency_id._get_conversion_rate(inv.currency_id, inv.company_id.currency_id, inv.company_id, inv.invoice_date),
                                '',
                                inv.ref if rInv else '',
                                rInv.date.strftime("%d/%m/%Y") if rInv and rInv.date else '', ]

                        csv_data.append(data)
        

            
            with open(file_path, "w") as writeFile:
                writer = csv.writer(writeFile)
                # writer.writerows([[
                #'Type of Purchase',
                #'PIN Number',
                #'Vendor Name',
                #'Bill Date',
                #'Invoice Number',
                #'Description of Goods/Services',
                #'Custom Entry Number',
                #'Taxable Amount',
                #'Amount of VAT',
                #'Relevant Invoice Number',
                #'Relevant Invoice Date'
                # ]])
                writer.writerows(csv_data)
            writeFile.close()

            result_file = open(file_path, 'rb').read()
            attachment_id = self.env['wizard.excel.report'].create({
                'name': 'Purchases - %s %s.csv' % (calendar.month_name[int(self.month_of)], self.year_of),
                'report': base64.b64encode(result_file)
            })
            try:
                os.unlink(file_path)
            except (OSError, IOError):
                _logger.error(
                    'Error when trying to remove file %s' % file_path)
            return {
                'name': _('Odoo'),
                'context': self.env.context,
                'view_mode': 'form',
                'res_model': 'wizard.excel.report',
                'res_id': attachment_id.id,
                'data': None,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise ValidationError(
                _('Invoice are Not Present in this month!!!'))


class WizardExcelReport(models.TransientModel):
    _name = 'wizard.excel.report'
    _description = "Vat Excel Report"

    name = fields.Char('File Name', size=64)
    report = fields.Binary('Excel Report', readonly=True)
