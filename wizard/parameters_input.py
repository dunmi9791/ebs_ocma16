# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api, _


class GencoParams(models.TransientModel):
    _name = 'ebs_ocma.genco.params'
    _description = 'Genco Parameters input'

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle",)
    genco_parameters_line_ids = fields.One2many(
        comodel_name="ebs_ocma.genco.parameters.lines", inverse_name="params_id",
        string="Genco Parameters Lines", readonly=False)

    def input_genco_params(self):
        for rec in self:
            genco_params = []
            for line in rec.genco_parameters_line_ids:
                vals = {'billing_cycle_id': rec.billing_cycle_id.id,
                        'partner_id': line.partner_id.id,
                        'capacity_sent_out_mw': line.capacity_sent_out,
                        'energy_sent_out_kwh': line.energy,
                        'capacity_import': line.capacity_import,
                        'energy_import': line.energy_import,
                        }
                genco_params.append(vals)
                self.env['ebs_ocma.genco.invoice.billing_cycle.parameter'].create(genco_params)


class GencoParamsLines(models.TransientModel):
    _name = 'ebs_ocma.genco.parameters.lines'

    params_id = fields.Many2one(comodel_name='ebs_ocma.genco.params', string='Genco')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')

    capacity_sent_out = fields.Float(string='Capacity Sent Out')
    energy = fields.Float('Gross/Net Energy')
    capacity_import = fields.Float('Capacity Import')
    energy_import = fields.Float('Energy Import')


class DiscoParams(models.TransientModel):
    _name = 'ebs_ocma.disco.params'
    _description = 'Disco Parameters input'

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle",)
    disco_parameters_line_ids = fields.One2many(
        comodel_name="ebs_ocma.disco.parameters.lines", inverse_name="params_id",
        string="Disco Parameters Lines", readonly=False)

    def input_disco_params(self):
        for rec in self:
            disco_params = []
            for line in rec.disco_parameters_line_ids:
                vals = {'billing_cycle_id': rec.billing_cycle_id.id,
                        'partner_id': line.partner_id.id,
                        'capacity_delivered': line.capacity_delivered,
                        'energy_delivered': line.energy_delivered,
                        }
                disco_params.append(vals)
                self.env['ebs_ocma.disco.invoice.billing_cycle.parameter'].create(disco_params)


class DiscoParamsLines(models.TransientModel):
    _name = 'ebs_ocma.disco.parameters.lines'

    params_id = fields.Many2one(comodel_name='ebs_ocma.disco.params', string='Disco')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco')

    capacity_delivered = fields.Float(string='Capacity Delivered')
    energy_delivered = fields.Float('Energy delivered')

