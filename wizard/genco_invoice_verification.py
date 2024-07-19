# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api, _

class CreateTransfer(models.TransientModel):
    _name = 'ebs_ocma.genco.invoice.transfer'
    _description = 'Genco Invoice verification'

    def _get_billing_cycle_id(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', []) or []
        if active_id:
            billing_cycle = self.env['billing.cycle'].browse(active_id)
            if billing_cycle:
                return billing_cycle and billing_cycle.id or False
        return False

    @api.onchange('billing_cycle_id')
    def _onchange_billing_cycle_id(self):
        verification_lines = self.env['ebs_ocma.genco.invoice.transfer.lines'].sudo()
        self.verification_line_ids.sudo().unlink()
        verification_line_ids = self.verification_line_ids
        if self.billing_cycle_id:
            for computed_line in self.bc_genco_parameter_ids:
                for genco_line in self.nbet_genco_parameter_ids:
                    if computed_line.partner_id == genco_line.partner_id:
                        verification_line_ids = verification_lines.create(
                            {
                                'partner_id': computed_line.partner_id and computed_line.partner_id.id,
                                'nbet_capacity_payment': computed_line.capacity_payment,
                                'nbet_energy_payment': computed_line.energy_payment,
                                'nbet_total_payment': computed_line.total_payment,

                                'genco_capacity_payment': genco_line.capacity_payment,
                                'genco_energy_payment': genco_line.energy_payment,
                                'genco_total_payment': genco_line.total_payment,
                                'verification_id': self.id,
                            }
                        )

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle", default=_get_billing_cycle_id, readonly=True)

    bc_genco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.genco.invoice.billing_cycle.parameter", inverse_name="billing_cycle_id", string="Genco Parameters", related='billing_cycle_id.bc_genco_parameter_ids', readonly=False)

    nbet_genco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.nbet.genco.invoice.billing_cycle", inverse_name="billing_cycle_id", string="NBET Genco Parameters", related='billing_cycle_id.nbet_genco_parameter_ids', readonly=False)

    verification_line_ids = fields.One2many(
        comodel_name="ebs_ocma.genco.invoice.transfer.lines", inverse_name="verification_id", string="Verification Lines", readonly=False)

    def verify_invoice(self):
        for rec in self:
            return

    def select_all_nbet(self):
        for rec in self:
            for line in rec.verification_line_ids:
                line.write({
                    'nbet_verified': True
                })
        return {
                'view_mode': 'form',
                'res_model': self._name,
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                }


class CreateTransfer(models.TransientModel):
    _name = 'ebs_ocma.genco.invoice.transfer.lines'

    verification_id = fields.Many2one(comodel_name='ebs_ocma.genco.invoice.transfer', string='Genco')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')

    nbet_verified = fields.Boolean(string='NBET verified invoice')
    nbet_capacity_payment = fields.Float('NBET Capacity Payment')
    nbet_energy_payment = fields.Float('NBET Energy Payment')
    nbet_total_payment = fields.Float('NBET Total Payment')

    space = fields.Char('  ', readonly=True, default='|')

    genco_verified = fields.Boolean(string='GENCO verified invoice')
    genco_capacity_payment = fields.Float('GENCO Capacity Payment')
    genco_energy_payment = fields.Float('GENCO Energy Payment')
    genco_total_payment = fields.Float('GENCO Total Payment')
    space2 = fields.Char('  ', readonly=True, default='|')
    difference = fields.Float(string='Difference', readonly=True, compute='_compute_difference')

    remarks = fields.Char(string='Comments')

    @api.onchange('nbet_verified')
    def _onchange_nbet_verified(self):
        for rec in self:
            if rec.nbet_verified == True:
                rec.genco_verified = False
    
    @api.onchange('genco_verified')
    def _onchange_genco_verified(self):
        for rec in self:
            if rec.genco_verified == True:
                rec.nbet_verified = False

    @api.depends('genco_total_payment', 'nbet_total_payment')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.genco_total_payment - rec.nbet_total_payment