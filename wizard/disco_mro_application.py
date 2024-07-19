# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date

class MROApplication(models.TransientModel):
    _name = 'ebs_ocma.mro.application'
    _description = 'MRO Application'

    def _get_billing_cycle_id(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', []) or []
        if active_id:
            billing_cycle = self.env['billing.cycle'].browse(active_id)
            if billing_cycle:
                return billing_cycle and billing_cycle.id or False
        return False

    def _get_mro_id(self):
        mro_id = self.env["ebs_ocma.disco.mro"].search([], order='date desc', limit=1)
        if mro_id:
            return mro_id.id
        return False

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle", default=_get_billing_cycle_id, readonly=False)
    mro_id = fields.Many2one(comodel_name="ebs_ocma.disco.mro", string='Disco MRO', default=_get_mro_id)
    mro_line_ids = fields.One2many(comodel_name='ebs_ocma.mro.application.lines', inverse_name="mro_id", string='MRO Lines', copy=False)

    @api.onchange('billing_cycle_id')
    def _onchange_billing_cycle_id(self):
        MROlines = self.env['ebs_ocma.mro.application.lines'].sudo()
        self.mro_line_ids.sudo().unlink()
        mro_line_ids = self.mro_line_ids
        if self.billing_cycle_id:
            for line in self.billing_cycle_id.disco_invoice_ids:
                mro_line_ids = MROlines.create(
                    {
                        'partner_id': line.partner_id and line.partner_id.id,
                        'invoice_id': line.id,
                        'invoice_value': line.amount_total,
                        'mro_id': self.id,
                    }
                )

    @api.onchange('mro_id')
    def _onchange_mro_id(self):
        for line in self.mro_line_ids:
            for mro_line in self.mro_id.mro_line_ids:
                if line.partner_id == mro_line.partner_id:
                    line.percent_mro = mro_line.percentage

    def apply_mro(self):
        for rec in self:
            self.generate_credit_note()

    def _create_disco_credit_note(self, partner_id, invoice_value):
        self.ensure_one()
        company_id = self.env.user.company_id.id
        # journal_id = (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id).default_get(['journal_id'])['journal_id'])
        journal_id = self.env.ref('ebs_ocma.disco_invoice_journal').id or (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id).default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('Please define an accounting journal.'))

        for rec in self:
            invoice_vals = {
                'ref': str(f"Credit Note for {partner_id.name}") or '',
                'move_type': 'out_refund',
                'partner_id': partner_id.id,
                'invoice_date': date.today(),

                # 'invoice_origin': origin,
                # 'account_id': partner_id.property_account_receivable_id.id,

                'journal_id': journal_id,
                'company_id': company_id,
                'billing_circle_id': self.billing_cycle_id.id,

                # 'user_id': self.user_id and self.user_id.id,
                # 'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
                # 'payment_term_id': self.payment_term_id.id,
                # 'currency_id': self.pricelist_id.currency_id.id,
                
                'invoice_line_ids': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'MRO',
                })
                ,(0, 0, {
                    'name': 'Total Disco Share of Energy Received (MWh)',
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': invoice_value,
                })],
            }
            disco_invoice_id = self.env['account.move'].create(invoice_vals)
            disco_invoice_id.action_post()
            # self.disco_invoice_ids += disco_invoice_id
    
    def generate_credit_note(self):
        for rec in self:
            for line in rec.mro_line_ids:
                if line.percent_mro > 0:
                    percentage_mro = (float(100) - line.percent_mro) / float(100)
                    credit_invoice_value = line.invoice_value * percentage_mro
                    rec._create_disco_credit_note(partner_id=line.partner_id, invoice_value = credit_invoice_value)
            rec.billing_cycle_id.state = 'invoice_verification'

class MROApplicationLines(models.TransientModel):
    _name = 'ebs_ocma.mro.application.lines'
    _description = 'MRO Application'

    mro_id = fields.Many2one(comodel_name='ebs_ocma.mro.application', string='MRO Application')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco')
    invoice_value = fields.Float(string='Invoice value')
    percent_mro = fields.Float(string='Percentage MRO(%)')
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice')
