# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Domiup (<http://domiup.com>).
#
##############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import Warning
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class MultiApproval(models.Model):
	_name = 'multi.approval'
	_inherit = ['mail.thread']
	_description = 'Multi Aproval'

	code = fields.Char(default=_('New'))
	name = fields.Char(string='Title', required=True)
	user_id = fields.Many2one(
		string='Request by', comodel_name="res.users",
		required=True, default=lambda self: self.env.uid)
	priority = fields.Selection(
		[('0', 'Normal'),
		('1', 'Medium'),
		('2', 'High'),
		('3', 'Very High')], string='Priority', default='0')
	request_date = fields.Datetime(
		string='Request Date', default=fields.Datetime.now)
	type_id = fields.Many2one(
		string="Type", comodel_name="multi.approval.type", required=True)
	description = fields.Html('Description')
	state = fields.Selection(
		[('Draft', 'Draft'),
		 ('Submitted', 'Submitted'),
		 ('Approved', 'Approved'),
		 ('Refused', 'Refused'),
		 ('Cancel', 'Cancel')], default='Draft', tracking=True)

	document_opt = fields.Selection(
		string="Document opt", default='Optional',
		readonly=True, related='type_id.document_opt')
	attachment_ids = fields.Many2many('ir.attachment', string='Documents')

	contact_opt = fields.Selection(
		string="Contact opt", default='None',
		readonly=True, related='type_id.contact_opt')
	contact_id = fields.Many2one('res.partner', string='Contact')

	date_opt = fields.Selection(
		string="Date opt", default='None',
		readonly=True, related='type_id.date_opt')
	date = fields.Date('Date')

	period_opt = fields.Selection(
		string="Period opt", default='None',
		readonly=True, related='type_id.period_opt')
	date_start = fields.Date('Start Date')
	date_end = fields.Date('End Date')

	item_opt = fields.Selection(
		string="Item opt", default='None',
		readonly=True, related='type_id.item_opt')
	item_id = fields.Many2one('product.product', string='Item')

	multi_items_opt = fields.Selection(
		string="Multi Items opt", default='None',
		readonly=True, related='type_id.multi_items_opt')
	item_ids = fields.Many2many('product.product', string='Items')


	quantity_opt = fields.Selection(
		string="Quantity opt", default='None',
		readonly=True, related='type_id.quantity_opt')
	quantity = fields.Float('Quantity')

	amount_opt = fields.Selection(
		string="Amount opt", default='None',
		readonly=True, related='type_id.amount_opt')
	amount = fields.Float('Amount')

	payment_opt = fields.Selection(
		string="Payment opt", default='None',
		readonly=True, related='type_id.payment_opt')
	payment = fields.Float('Payment')

	reference_opt = fields.Selection(
		string="Reference opt", default='None',
		readonly=True, related='type_id.reference_opt')
	reference = fields.Char('Reference')

	location_opt = fields.Selection(
		string="Location opt", default='None',
		readonly=True, related='type_id.location_opt')
	location = fields.Char('Location')
	line_ids = fields.One2many('multi.approval.line', 'approval_id',
							   string="Lines")
	line_id = fields.Many2many('multi.approval.line', string="Line", copy=False)
	deadline = fields.Date(string='Deadline', related='line_id.deadline')
	pic_ids = fields.Many2many(
		'res.users', string='Approver')
	is_pic = fields.Boolean(compute='_check_pic')
	follower = fields.Text('Following Users', default='[]', copy=False)

	# copy the idea of hr_expense
	attachment_number = fields.Integer(
		'Number of Attachments', compute='_compute_attachment_number')

	def _check_pic(self):
		for r in self:
			val = [c.id for c in r.pic_ids if self.env.uid == c.id]
			if val:
				r.is_pic = True
			else:
				r.is_pic = False


	def _compute_attachment_number(self):
		attachment_data = self.env['ir.attachment'].read_group(
			[('res_model', '=', 'multi.approval'), ('res_id', 'in', self.ids)],
			['res_id'], ['res_id'])
		attachment = dict((data['res_id'], data['res_id_count'])
						  for data in attachment_data)
		for r in self:
			r.attachment_number = attachment.get(r.id, 0)

	def action_cancel(self):
		recs = self.filtered(lambda x: x.state == 'Draft')
		recs.write({'state': 'Cancel'})

	def action_submit(self):
		recs = self.filtered(lambda x: x.state == 'Draft')
		for r in recs:
			# Check if document is required
			if r.document_opt == 'Required' and r.attachment_number < 1:
				raise Warning(_('Document is required !'))
			if not r.type_id.line_ids:
				raise Warning(_(
					'There is no approver of the type "{}" !'.format(
						r.type_id.name)))
			r.state = 'Submitted'
		recs._create_approval_lines()
  

	@api.model
	def get_follow_key(self, user_id=None):
		if not user_id:
			user_id = self.env.uid
		k = '[res.users:{}]'.format(user_id)
		return k

	def update_follower(self, user_id):
		self.ensure_one()
		k = self.get_follow_key(user_id)
		follower = self.follower
		if k not in follower:
			self.follower = follower + k

	# #update target model status
	# def update_target_model_status(self, updated_state):
	#     self.ensure_one()
	#     target_obj = str(self.origin_ref)
	#     x = target_obj[0:target_obj.find("(")]
	#     rec = self.env[x].search([('id','=',self.origin_ref.id)])
	#     print ('FOUND >>>>', rec)
	#     rec.update({'state': updated_state})`									

	def send_email(self, rec, line):
		msg = _('Please approve this record')
		notification_ids = []
		notification_ids.append((0,0,{
			'res_partner_id':line.user_id.partner_id.id,
			'notification_type':'inbox'}))
		self.sudo().message_post(body=msg, message_type='notification', author_id=self.env.user.partner_id.id, notification_ids=notification_ids)
		
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		approval_url = base_url +'/web#id=' + str(rec.id) + '&model=multi.approval&view_type=form'
		_subject = 'Approval Required:: ' + rec.name 
		_body = 'You have a pending ' + rec.name + '. \
				<br/><p>Click on the link (<a href="' + approval_url + '">' + rec.code +'</a>) to approve</p>' 
		_email_from = rec.user_id.login
		_email_to = line.user_id.login
		self.generate_email(_subject, _body, _email_from, _email_to)

	# 13.0.1.1
	def set_approved(self):
		self.ensure_one()
		self.state = 'Approved'

	def set_refused(self, reason=''):
		self.ensure_one()
		self.state = 'Refused'

	def action_approve(self):
		ret_act = None
		recs = self.filtered(lambda x: x.state == 'Submitted')
		for rec in recs:
			if not rec.is_pic:
				msg = _('{} do not have the authority to approve this request !'.format(rec.env.user.name))
				self.sudo().message_post(body=msg)
				return False
			lines = rec.line_id
			for line in lines:
				pic_ids = line.user_id
				if not line or line.state != 'Waiting for Approval':
					# Something goes wrong!
					self.message_post(body=_('Something goes wrong!'))
					return False

				# Update follower
				rec.update_follower(self.env.uid)

				# check if this line is required
				other_lines = rec.line_ids.filtered(
					lambda x: x.sequence >= line.sequence and x.state == 'Draft')	
				if not other_lines:
					ret_act = rec.set_approved()
				else:
					required_vals = other_lines.filtered(
						lambda r: r.require_opt == 'Required' and r.state == 'Draft')				
					if required_vals:
						next_line = required_vals.sorted('sequence')[0]
						next_line.write({
							'state': 'Waiting for Approval',
						})
						rec.line_id = next_line
						rec.pic_ids = rec.line_id.user_id
						msg = _('Please approve this record')
						self.send_email(rec, next_line)
					else:
						optional_vals = other_lines.filtered(
							lambda r: r.require_opt == 'Optional' and r.state == 'Draft')
						if optional_vals:
							rec.pic_ids = None
							rec.line_id = None
							for option in optional_vals:
								option.write({
									'state': 'Waiting for Approval'
									})	
								rec.line_id += option
								rec.pic_ids += option.user_id
								msg = _('Please approve this record')
								self.send_email(rec, option)
						else:
							_logger.error("entered optional vals")
							ret_act = rec.set_approved
				line.set_approved()
				break
			msg = _('I approved')	
			rec.message_post(body=msg)
		if ret_act:
			return ret_act

	def action_refuse(self, reason=''):
		ret_act = None
		recs = self.filtered(lambda x: x.state == 'Submitted')
		for rec in recs:
			if not rec.is_pic:
				msg = _('{} do not have the authority to approve this request !'.format(rec.env.user.name))
				self.sudo().message_post(body=msg)
				return False
			lines = rec.line_id
			for line in lines:
				if not line or line.state != 'Waiting for Approval':
					# Something goes wrong!
					self.message_post(body=_('Something goes wrong!'))
					return False

				# Update follower
				rec.update_follower(self.env.uid)

				# check if this line is required
				if line.require_opt == 'Required':
					ret_act = rec.set_refused(reason)
					draft_lines = rec.line_ids.filtered(lambda x: x.state == 'Draft')
					if draft_lines:
						draft_lines.state = 'Cancel'
				else:  # optional
					other_lines = rec.line_ids.filtered(
						lambda x: x.sequence >= line.sequence and x.state == 'Draft')
					if not other_lines:
						ret_act = rec.set_refused(reason)
					else:
						required_vals = other_lines.filtered(
						lambda r: r.require_opt == 'Required' and r.state == 'Draft')				
					if required_vals:
						next_line = required_vals.sorted('sequence')[0]
						next_line.write({
							'state': 'Waiting for Approval',
						})
						rec.line_id = next_line
						rec.pic_ids = rec.line_id.user_id
						msg = _('Please approve this record')
						self.send_email(rec, next_line)
					else:
						optional_vals = other_lines.filtered(
							lambda r: r.require_opt == 'Optional' and r.state == 'Draft')
						if optional_vals:
							rec.pic_ids = None
							rec.line_id = None
							for option in optional_vals:
								option.write({
									'state': 'Waiting for Approval'
									})	
								rec.line_id += option
								rec.pic_ids += option.user_id
								msg = _('Please approve this record')
								self.send_email(rec, option)
						else:
							_logger.error("entered optional vals")
							ret_act = rec.set_refused(reason)
				line.set_refused(reason)
				break
			msg = _('I refused due to this reason: {}'.format(reason))
			rec.message_post(body=msg)				
		if ret_act:
			return ret_act

	def _create_approval_lines(self):
		ApprovalLine = self.env['multi.approval.line']
		for r in self:
			lines = r.type_id.line_ids.sorted('sequence')
			last_seq = 0
			first_approver_id = 0
			r.line_id = None
			r.pic_ids = None
			for l in lines:
				line_seq = l.sequence
				if not line_seq or line_seq <= last_seq:
					line_seq = last_seq + 1
				last_seq = line_seq
				vals = {
					'name': l.name,
					'user_id': l.get_user(),
					'sequence': line_seq,
					'require_opt': l.require_opt,
					'approval_id': r.id
				}
				if lines[0].require_opt == 'Required' and l == lines[0]:
					vals.update({'state' : 'Waiting for Approval'})
					r.pic_ids = lines[0].user_id
					
				elif lines[0].require_opt == 'Optional':		
					if l.require_opt == 'Optional':
						vals.update({'state': 'Waiting for Approval'})
						r.pic_ids += l.user_id

				
				approval = ApprovalLine.create(vals)
				
				if lines[0].require_opt == 'Required' and l == lines[0]:
					r.line_id = approval
					self.send_email(r, lines[0])	
				elif lines[0].require_opt == 'Optional':
					if l.require_opt == 'Optional':
						r.line_id += approval
						self.send_email(r, l)
				
				#Get the first approver id
				if first_approver_id == 0:
					first_approver_id = l.get_user()

	@api.model
	def create(self, vals):
		seq_date = vals.get('request_date', fields.Datetime.now())
		vals['code'] = self.env['ir.sequence'].next_by_code(
			'multi.approval', sequence_date=seq_date) or _('New')
		result = super(MultiApproval, self).create(vals)

		return result

	def generate_email(self, subject, body, email_from, email_to):
		template_obj = self.env['mail.mail']
		template_data = {
				'subject': subject,
				'body_html': body,
				'email_from': email_from,
				'email_to': email_to #", ".join(recipients)
				}
		template_out = template_obj.sudo().create(template_data)
		template_out.sudo().send()


