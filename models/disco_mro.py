# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _

class DiscoMRO(models.Model):
    _name = 'ebs_ocma.disco.mro'
    _description = 'Disco MRO'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date DESC"
    
    state = fields.Selection(selection=[
        ('draft', "New"),
        ('submit', "Submitted"),
        ('approve', "Approved"),
        ('reject', "Rejected"),
    ], string="State", readonly=True, default="draft", copy=False)

    name = fields.Char(string="Name", copy=False)
    date = fields.Date(string='Date', default=date.today(), required=True)
    
    mro_line_ids = fields.One2many(comodel_name="ebs_ocma.disco.mro.line", inverse_name="mro_id", string="MRO Lines")

    def button_submit(self):
        self.state = 'submit'

    def button_approve(self):
        self.state = 'approve'

    def button_reject(self):
        self.state = 'reject'

class DiscoMROLine(models.Model):
    _name = 'ebs_ocma.disco.mro.line'
    _description = 'Disco MRO Line'

    mro_id = fields.Many2one(comodel_name="ebs_ocma.disco.mro", string='Disco MRO')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco', domain="[('is_disco', '=', True)]", required=True)
    percentage = fields.Float(string='Percentage (%)', required=True)