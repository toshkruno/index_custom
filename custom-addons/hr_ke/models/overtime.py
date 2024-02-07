# -*- coding: utf-8 -*-
"""
# License LGPL-3.0 or later (https://opensource.org/licenses/LGPL-3.0).
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT section below).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
#########COPYRIGHT#####
# © 2016 Bernard K Too<bernard.too@optima.co.ke>
"""
import logging
import datetime
from datetime import datetime, date, time
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import dateutil.parser
LOGGER = logging.getLogger(__name__)
import pdb


class KeDepartment(models.Model):
    """ inherited to add overtime related features """
    _inherit = ["hr.department"]

    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id')
    overtime = fields.Monetary(
        'Overtime Hourly rate',
        currency_field='company_currency_id', track_visibility='onchange')


class KeOvertime(models.Model):
    """ Overtime request model """
    _name = "ke.overtime"
    _description = "Overtime Request"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    # _inherit = ['mail.channel']
    _order = "id desc"

    def default_date(self):
        """ returns today's date and time """
        return fields.Datetime.now(self)


    def _employee_get(self):
        return self.employee_id.search(
            [('user_id', '=', self.env.user.id)], limit=1).id


    def check_login_user(self):
        """ sets boolean value depending on the login user """
        for record in self:
            record.same_user = bool(record.env.user.id == record.user_id.id)


    def check_user_dept(self):
        """ sets boolean value depending on user department """
        for record in self:
            record.same_dept = bool(record.employee_id.search(
                [('user_id', '=', record.env.user.id)], limit=1).department_id.id == record.dept_id.id)

    name = fields.Char(
        'Brief Title', required=True, readonly=True, states={
            'draft': [
                ('readonly', False)]}, track_visibility='always')
    dept_id = fields.Many2one(
        'hr.department',
        'Department',
        related='employee_id.department_id', track_visibility='always')
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee Name',
        track_visibility='always',
        default=_employee_get,
        required=False,
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]})
    user_id = fields.Many2one(
        'res.users',
        related='employee_id.user_id',
        track_visibility='always')
    state = fields.Selection([('draft',
                               'Draft'),
                              ('approval',
                               'Waiting Approval'),
                              ('approved',
                               'Approved'),
                              ('disapproved',
                               'Dis-approved')],
                             'Status',
                             default='draft', track_visibility='onchange')
    date_from = fields.Datetime(
        'Date',
        required=True,
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]},
        default=default_date,
        track_visibility='onchange')
    extra_salary = fields.Many2one("extra.salary",
                                   string='Overtime Rate',
                                   required=True,
                                   readonly=True,
                                   states={
                                                'draft': [
                                                    ('readonly',
                                                     False)]},
                                   track_visibility='onchange')
    hours = fields.Float(
        'Hours',
        required=False,
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]},
        store=True,
        track_visibility='onchange')
    description = fields.Html(
        'Work Details', required=True, readonly=True, states={
            'draft': [
                ('readonly', False)]}, track_visibility='onchange')
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        required=False,
        domain="[('employee_id','=', employee_id)]",
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]}, track_visibility='always')
    employee_list_ids = fields.One2many(
        'emp.list',
        'employee_list_id',
        string='Employees List',
        required=True,
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]}, track_visibility='always')
    same_user = fields.Boolean(compute='check_login_user')
    same_dept = fields.Boolean(compute='check_user_dept')

    # @api.depends('date_from', 'date_to')
    # def _total_minutes(self):
    #     if self.date_from or self.date_to:
    #         start_dt = fields.Datetime.from_string(self.date_from)
    #         finish_dt = fields.Datetime.from_string(self.date_to)
    #         difference = relativedelta(finish_dt, start_dt)
    #         hours = difference.hours or 0
    #         days = difference.days*24 or 0
    #         minui = difference.minutes/60 or 0
    #         self.hours = hours + days + minui
    #
    #         if self.hours < 0:
    #             raise ValidationError(
    #                     "'End Date' is older than 'Start Date' in time entry. Please correct this")


    def overtime_approval(self):
        """Send a request for approval"""
        for rec in self:
            if not rec.employee_list_ids:
                raise ValidationError('Missing Employee record')
            for record in rec.employee_list_ids:
                if not record.Emp_name.parent_id:
                    raise ValidationError(
                        'Your manager is not added in your HR records,\
                                no one to approve your Overtime request.Please consult HR')
                elif not record.Emp_name.parent_id.user_id:
                    raise ValidationError(
                        'Your manager does have access to the HR system\
                                to approve your overtime request. Please consult HR')
            return rec.write({'state': 'approval'})


    def overtime_approved(self):
        """ Approves the overtime request """
        for rec in self:
            for record in rec.employee_list_ids:
                allowance_type = self.env.ref('hr_ke.ke_cash_allowance3')
                if not allowance_type:
                    raise ValidationError(
                        'No salary rule found for processing overtime\
                                allowances in your payroll system!')
                hourly_rate = 0
                if record.contract_id.rem_type in ['monthly']:
                    hourly_rate = (record.contract_id.wage / 195) * record.employee_list_id.extra_salary.name
                elif record.contract_id.rem_type in ['daily']:
                    hourly_rate = (record.contract_id.wage / 7.5) * record.employee_list_id.extra_salary.name
                values = {
                    'cash_allowance_id': allowance_type.id,
                    'contract_id': record.contract_id.id,
                    'computation': 'fixed',
                    'rule_id': allowance_type.rule_id.id,
                    'fixed': record.worked_hours * hourly_rate
                }
                # employee = self.env['hr.employee'].browse(employee_id)
                if values:
                    self.env['ke.cash_allowances'].create(values)
                else:
                    raise ValidationError(
                        'Missing Overtime details. Please consult HR')
                record.employee_list_id.write({'state': 'approved'})


    def overtime_disapproved(self):
        """ disapproves the overtime request """
        for record in self:
            record.write({'state': 'disapproved'})


    def overtime_reset(self):
        """ Resets an overtime request currently waiting approval"""
        for record in self:
            record.write({'state': 'draft'})


class EmployeesList(models.Model):
    _name = "emp.list"
    _description = "Employees List"

    employee_list_id = fields.Many2one('ke.overtime')
    Emp_name = fields.Many2one('hr.employee', string="Employee Name")
    worked_hours = fields.Float('Worked Hours')
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        required=True,
        domain="[('employee_id','=', Emp_name)]")


    @api.constrains('worked_hours')
    def overtime_worked_hours(self):
        for rec in self:
            if rec.worked_hours == 0:
                raise ValidationError('Please Enter a Valid Worked Hours')


class ExtraSalary(models.Model):
    _name = "extra.salary"
    _description = "Extra Salary"

    name = fields.Float("Extra Salary")
