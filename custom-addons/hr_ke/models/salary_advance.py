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
# © 2019 Bernard K Too<bernard.too@optima.co.ke>
"""
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
LOGGER = logging.getLogger(__name__)


class KeSalaryAdvance(models.Model):
    """ Salary Advance request model"""
    _name = "ke.advance"
    _description = "Salary Advance Request"
    _inherit = ["mail.thread", 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    
    def _employee_get(self):
        return self.employee_id.search(
            [('user_id', '=', self.env.user.id)], limit=1).id


    def check_login_user(self):
        """ set boolean value based on login user """
        for record in self:
            record.same_user = bool(record.env.user.id == record.user_id.id)

    name = fields.Char(
        'Request details',
        required=True,
        readonly=True,
        track_visibility='onchange',
        states={
            'draft': [
                ('readonly',
                 False)]})
    dept_id = fields.Many2one(
        'hr.department',
        'Department',
        track_visibility='always',
        related='employee_id.department_id')
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee Name',
        default=_employee_get,
        required=True,
        track_visibility='always',
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
    amount = fields.Monetary(
        'Amount',
        currency_field='currency_id',
        track_visibility='onchange', readonly=True, states={
            'draft': [
                ('readonly',
                 False)]})
    description = fields.Html(
        'Reasons for Request',
        required=True,
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]}, track_visibility='onchange')
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        required=True,
        track_visibility='always',
        domain="[('employee_id','=', employee_id)]",
        readonly=True,
        states={
            'draft': [
                ('readonly',
                 False)]})
    same_user = fields.Boolean(compute='check_login_user')

    currency_id = fields.Many2one(
        related='employee_id.company_id.currency_id',
        track_visibility='onchange')

    
    def advance_approval(self):
        """ sets the draft salary advance request to waiting approval"""
        for record in self:
            if not record.employee_id:
                raise ValidationError('Missing Employee record')
            elif not record.employee_id.parent_id:
                raise ValidationError(
                    'Your manager is not added in your HR records,\
                            no one to approve your salary advance request.Please consult HR')
            elif not record.employee_id.parent_id.user_id:
                raise ValidationError(
                    'Your manager does have access to the HR system to \
                            approve your salary advance request. Please consult HR')
            else:
                # record.message_subscribe_users(
                #    user_ids=[record.employee_id.parent_id.user_id.id])
                return record.write({'state': 'approval'})

    
    def advance_approved(self):
        """ approves a salary advance request """
        for record in self:
            deduction_type = self.env.ref('hr_ke.ke_deduction2')
            if not deduction_type:
                raise ValidationError(
                    "No salary rule found for processing salary advance in your payroll system!")
            values = {
                'employee_id': record.employee_id.id,
                'computation': 'fixed',
                'deduction_id': deduction_type.id,
                'rule_id': deduction_type.rule_id.id,
                'fixed': record.amount
            }
            if values:
                self.env['ke.deductions'].create(values)
            else:
                raise ValidationError(
                    'Missing Salary Advance details. Please consult payroll department')
            record.write({'state': 'approved'})

    
    def advance_disapproved(self):
        """ disapproves a salary advance request """
        for record in self:
            record.write({'state': 'disapproved'})

    
    def advance_reset(self):
        """ resets a salary adanve request currently waiting approval"""
        for record in self:
            record.write({'state': 'draft'})
