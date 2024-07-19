# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    disco_category = fields.Selection(selection=[
        ('vesting_contract', "Vesting contract"),
        ('no_vesting_contract', "Without Vesting Contract"),
    ], string='Category')
    contract_capacity_share = fields.Float('Contract Capacity Share')
    is_genco = fields.Boolean(string='Genco')
    is_disco = fields.Boolean(string='Disco')
    myto_rate = fields.Many2one(
        comodel_name='ocma.myto.rate',
        string='Myto rate',
        required=False)
    rate_category = fields.Many2one(comodel_name='ebs_ocma.myto.rate.cateogry', string='Rate Category')

    rate = fields.Float(string='Rate (Capacity Tariff)', compute='_compute_capacity_tariff')
    rate_gas_price = fields.Float(string='Tariff (New gas Price)', compute='_compute_energy_tariff')

    disco_short_code = fields.Char(string='Short Code')

    # current_mro = fields.Float(string='Current MRO (%)', tracking=True)

    def _compute_capacity_tariff(self):
        for rec in self:
            mytorate = rec.myto_rate.id
            rates = self.env['hydro.rates'].search([('rate_id', '=', mytorate)], limit=1, order='id desc')
            rec.rate = rates.capacity_charge

            # def get_latest_record(self):
            #     latest_record = self.search([], limit=1, order='id desc')
            #     # limit=1 will return only one record and order='id desc' will sort the records in descending order by id
            #     # which will give you the latest record first
            #     return latest_record and latest_record[0] or False

    def _compute_energy_tariff(self):
        for rec in self:
            mytorate = rec.myto_rate.id
            rates = self.env['hydro.rates'].search([('rate_id', '=', mytorate)], limit=1, order='id desc')
            rec.rate_gas_price = rates.energy_charge_tlf


