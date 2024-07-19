# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from calendar import monthrange


class RateCoputation(models.TransientModel):
    _name = 'ebs_ocma.rate.computation'
    _description = 'Rate computation '

    calculation_type = fields.Selection([
        ('hydros', 'Hydros'),
        ('successor_gencos', 'Successor Gencos'),
        ('transcorp_ugheli', 'Transcorp Ugheli'),
        ('fipl', 'FIPL (Trans Amadi)'),
        ('fiplo', 'FIPL (Omoku and Rivers)'),
        ('shell', 'SHELL (AFAM VI)'),
        ('agip', 'AGIP (OKPAI)'),
        ('olorunsogo', 'Olorunsogo'),
        ('omotosho', 'Omotosho'),
        ('ibom', 'IBOM POWER'),
        ('nipps', 'NIPPS'),
        ('calabar_nipp', 'CALABAR NIPP'),
        ('gbarain_nipp', 'GBARAIN NIPP'),
        ('mabon', 'MABON (Dadin Kowa Hydro)'),
        ('direct_input', 'Direct Input'),
    ], string='Calculation Type')
    myto_rate_id = fields.Many2one(
        comodel_name='ocma.myto.rate',
        string='Myto_rate_id',
        required=False)

    usd_fx_cbn = fields.Float(string='Usd/naira fx CBN', required=False,)
    usd_fx_cbn_cur = fields.Float(string='Usd/naira fx CBN', required=False, compute='_usd_fx_cbn_cur', store=True, readonly=False)
    usd_fx_cbn_cur_gas = fields.Float(string='Usd/naira fx Gas', required=False, compute='_usd_fx_cbn_cur_gas', store=True,
                                  readonly=False)
    usd_fx_cbn_sell_cur = fields.Float(string='Usd/naira fx CBN Selling', required=False, compute='_usd_fx_cbn_sell_cur')
    us_cpi = fields.Float(string='US Cpi (index)', required=False,)
    us_ppi = fields.Float(string='US ppi (index)', required=False, )
    old_tlf = fields.Float(string='Old TLF', required=False, default=8.05)
    new_tlf = fields.Float(string='New TLF', required=False, compute='_new_tlf', store=True,)
    us_cpi_cur = fields.Float(string='US Cpi (index)', required=False,)
    us_ppi_cur = fields.Float(string='US ppi (index)', required=False, )
    fixed_o_m = fields.Float(string='Fixed O & M(n/mw/hr)', required=False, )
    fixed_o_m_noncompute = fields.Float(string='Fixed O & M(n/mw/hr)', required=False, default=397)
    fixed_o_m_cur = fields.Float(
        string='Fixed O & M(n/mw/hr)',
        required=False, compute='_fix_om_cur')
    variable_o_m = fields.Float(string='Variable O & M(n/mw/hr)', required=False, )
    variable_o_m_noncompute = fields.Float(string='Variable O & M(n/mw/hr)', required=False, default=1101)
    variable_o_m_cur = fields.Float(string='Variable O & M(n/mw/hr)', required=False, compute='_variable_om_cur')
    fixed_o_m_dollar = fields.Float(string='Fixed O & M($/mw/hr)', required=False, digits='Ocma')
    fixed_o_m_dollar_cur = fields.Float(string='Fixed O & M($/mw/hr)', required=False, compute='_fixed_om_dollar', digits='Ocma')
    variable_o_m_dollar = fields.Float(string='Variable O & M($/mw/hr)', required=False, digits='Ocma')
    variable_o_m_dollar_cur = fields.Float(string='Variable O & M($/mw/hr)', required=False,
                                           compute='_variable_om_dollar', digits='Ocma')
    capital_recovery_dollar = fields.Float(string='Capital recovery($/mw/hr)', required=False, digits='Ocma')
    capital_recovery_dollar_cur = fields.Float(string='Capital recovery($/mw/hr)', required=False,
                                               compute='_capital_recovery_dollar_cur' )
    capital_recovery = fields.Float(string='Capital recovery(n/mw/hr)', required=False, )
    capital_recovery_cur = fields.Float(string='Capital recovery(n/mw/hr)', required=False,
                                        compute='_capital_recovery_cur')
    energy_charge = fields.Float(string='Energy charge(n/mw/hr)', required=False, )
    energy_charge_dollar = fields.Float(string='Energy charge($/mw/hr)', required=False, digits='Ocma')
    energy_charge_dollar_cur = fields.Float(string='Energy charge($/mw/hr)', required=False, digits='Ocma',
                                            compute='_energy_charge_dollar_cur')
    energy_charge_cur = fields.Float(string='Energy charge(n/mw/hr)', required=False, compute='_energy_charge_cur')
    energy_charge_cur_noncompute = fields.Float(string='Energy charge(n/mw/hr)', required=False,)
    energy_charge_tlf = fields.Float(string='Energy charge new TLF(n/mw/hr)', required=False, compute='_energy_charge_tlf')
    capacity_charge = fields.Float(string='Capacity charge(n/mw/hr)', required=False, )
    capacity_charge_dollar = fields.Float(string='Capacity charge($/mw/hr)', required=False, digits='Ocma')
    capacity_charge_dollar_cur = fields.Float(string='Capacity charge($/mw/hr)', required=False, digits='Ocma',
                                              compute='_capacity_charge_dollar_cur')
    capacity_charge_dollar_dup = fields.Float(string='Capacity charge($/mw/hr)', required=False, digits='Ocma',
                                              compute='_capacity_charge_dollar_dup')
    capacity_charge_cur = fields.Float(string='Capacity charge(n/mw/hr)', required=False, compute='_capacity_charge_cur')
    capacity_charge_cur_noncompute = fields.Float(string='Capacity charge(n/mw/hr)', required=False, )
    wholesale_charge = fields.Float(string='Wholesale charge(n/mw/hr)', required=False)
    wholesale_charge_cur = fields.Float(string='Wholesale charge(n/mw/hr)', required=False, compute='_wholesale_charge_cur')
    billing_circle = fields.Many2one(comodel_name='billing.cycle', string='Billing cycle', required=True,)
    gas_fuel_price_dollar = fields.Float(string='Gas Fuel Price($/mmbtu)', required=False, )
    gas_fuel_price_dollar_cur = fields.Float(string='Gas Fuel Price($/mmbtu)', required=False, )
    gas_fuel_price_naira = fields.Float(string='Gas Fuel Price(N/mmbtu)', required=False, compute='_gas_price_naira')
    gas_hhv_price = fields.Float(string='Gas Price HHV(N/mmbtu)', required=False, )
    gas_hhv_price_cur = fields.Float(string='Gas Price HHV(N/mmbtu)', required=False, compute="_gas_hhv_price_naira")
    gas_hhv_price_dollar = fields.Float(string='Gas Price HHV($/mmbtu)', required=False)
    gas_hhv_price_dollar_cur = fields.Float(string='Gas Price HHV($/mmbtu)', required=False)
    vfcr = fields.Float(string='VFCR(n/mwh)', required=False)
    vfcr_cur = fields.Float(string='VFCR(n/mwh)', required=False, compute='_vfcr_cur')
    vfcr_dollar = fields.Float(string='VFCR($/mwh)', required=False)
    vfcr_dollar_cur = fields.Float(string='VFCR($/mwh)', required=False, compute='_vfcr_cur_dollar')
    ncpi = fields.Float(string='NCPI(index)', required=False)
    ncpi_cur = fields.Float(string='NCPI(index)', required=False)
    # us_ppi = fields.Float(string='US PPI(Index)', required=False, )
    investment_dollar = fields.Float(string='Investment($/kw/month)', required=False, digits='Ocma')
    investment_dollar_cur = fields.Float(string='Investment($/kw/month)', required=False,
                                         compute='_investment_dollar_cur', digits='Ocma')
    general_expenses_dollar = fields.Float(string='General Expenses($/kw/month)', required=False, digits='Ocma')
    general_expenses_dollar_cur = fields.Float(string='General Expenses($/kw/month)', required=False,
                                               compute='_expenses_dollar_cur', digits='Ocma')
    insurance_dollar = fields.Float(string='Insurance($/kw/month)', required=False, digits='Ocma')
    insurance_dollar_cur = fields.Float(string='Insurance($/kw/month)', required=False, compute='_insurance_dollar_cur', digits='Ocma')
    fuel_dollar = fields.Float(string='Fuel ($/mw/hr)', required=False, digits='Ocma')
    fuel_dollar_cur = fields.Float(string='Fuel($/mw/hr)', required=False, compute='_fuel_dollar_cur', digits='Ocma')
    investment_naira = fields.Float(string='Investment(n/kw/month)', required=False, compute='_investment_naira')
    general_expenses_naira = fields.Float(string='General Expenses(n/kw/month)', required=False,
                                          compute='_general_expenses_naira')
    insurance_naira = fields.Float(string='Insurance(n/kw/month)', required=False, compute='_insurance_naira')
    fuel_naira = fields.Float(string='Fuel(n/mw/hr)', required=False, compute='_fuel_naira')
    fuel_naira_cur = fields.Float(string='Wholesale charge(n/mw/hr)', required=False)
    tax_cost_cur = fields.Float(string='Tax Cost(n/mw/hr)', required=False, default=974)
    tax_cost = fields.Float(string='Tax cost(n/mw/hr)', required=False)
    capital_cost = fields.Float(string='Capital cost(n/mw/hr)', required=False)
    capital_cost_cur = fields.Float(string='Capital cost(n/mw/hr)', required=False, default=3257)
    startup_dollar = fields.Float(string='Startup dollar', required=False)
    startup_dollar_cur = fields.Float(string='Startup dollar', required=False, compute='_startup_dollar_cur')
    startup_naira = fields.Float(string='Startup Naira', required=False, compute='_startup_naira')
    fuel_cost_dollar = fields.Float(string='Fuel cost dollar', required=False, )
    fuel_cost_naira = fields.Float(string='Fuel cost Naira', required=False, )
    fuel_cost_dollar_cur = fields.Float(string='Fuel cost dollar', required=False, compute='_fuel_cost_cur')
    fuel_cost_naira_cur = fields.Float(string='Fuel cost Naira', required=False, compute='_fuel_cost_cur_naira')
    hhv_to_lhv = fields.Float(string='HHV to LHV Ratio', required=False)
    efficiency = fields.Float(string='Efficiency %', required=False)
    hhv_to_lhv_cur = fields.Float(string='HHV to LHV Ratio', required=False, default=1.10)
    efficiency_cur = fields.Float(string='Efficiency %', required=False, default=32.00)
    trans_loss_cost_cur = fields.Float(string='trans loss cost', default=735)
    trans_loss_cost = fields.Float(string='transmission loss cost(0.75%)')
    capacity_inv = fields.Float(string='Capacity Invoice', compute='_capacity_invoice')
    agip_dependable_capacity = fields.Float(string='Agip Dependable Capacity')
    hours_month = fields.Float(string='Hours in the Month', compute='_compute_hours_in_month')
    days_month = fields.Float(string='days in month', compute='_compute_days_in_month')

    def fix_om_cur(self):
        for record in self:
            rates = self.env['hydro.rates'].create({
                'rate_id': record.myto_rate_id.id,
                'fixed_o_m': record.fixed_o_m_cur,
                'usd_fx_cbn': record.usd_fx_cbn_cur,
                'us_cpi': record.us_cpi_cur,
                'new_tlf': record.new_tlf,
                'variable_o_m': record.variable_o_m_cur,
                'capital_recovery': record.capital_recovery_cur,
                'energy_charge': record.energy_charge_cur,
                'energy_charge_tlf': record.energy_charge_tlf,
                'capacity_charge': record.capacity_charge_cur,
                'wholesale_charge': record.wholesale_charge_cur,
                'billing_circle': record.billing_circle.id,
                })

    @api.depends('billing_circle.date_start')
    def _compute_days_in_month(self):
        for rec in self:
            if rec.billing_circle.date_start:
                date = datetime.strptime(str(rec.billing_circle.date_start), DEFAULT_SERVER_DATE_FORMAT)
                rec.days_month = monthrange(date.year, date.month)[1]
            else:
                rec.days_month = 30

    @api.depends('days_month')
    def _compute_hours_in_month(self):
        for record in self:
            record.hours_month = record.days_month * 24


    @api.depends('billing_circle')
    def _new_tlf(self):
        for record in self:
            if record.billing_circle.transmission_loss_factor:
                record.new_tlf = record.billing_circle.transmission_loss_factor
            else:
                record.new_tlf = 0

    @api.depends('vfcr_dollar', 'us_ppi_cur', 'us_ppi')
    def _vfcr_cur_dollar(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell']:
                    record.vfcr_dollar_cur = record.vfcr_dollar * record.us_ppi_cur / record.us_ppi
                else:
                    record.vfcr_dollar_cur = 0

    @api.depends('billing_circle')
    def _usd_fx_cbn_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'successor_gencos', 'transcorp_ugheli', 'olorunsogo',
                                               'omotosho', 'ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp', 'mabon' ]:
                    record.usd_fx_cbn_cur = record.billing_circle.cbn_selling_fss
                elif record.calculation_type in ['shell']:
                    record.usd_fx_cbn_cur = record.billing_circle.cbn_central_fss
                elif record.calculation_type in ['agip']:
                    record.usd_fx_cbn_cur = record.billing_circle.cbn_buying_average
                else:
                    record.usd_fx_cbn_cur = 0

    @api.depends('billing_circle')
    def _usd_fx_cbn_cur_gas(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'successor_gencos', 'transcorp_ugheli', 'olorunsogo',
                                               'omotosho', 'ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp', 'mabon']:
                    record.usd_fx_cbn_cur_gas = record.billing_circle.cbn_gas
                elif record.calculation_type in ['shell']:
                    record.usd_fx_cbn_cur_gas = record.billing_circle.cbn_gas
                elif record.calculation_type in ['agip']:
                    record.usd_fx_cbn_cur_gas = record.billing_circle.cbn_gas
                else:
                    record.usd_fx_cbn_cur_gas = 0

    @api.depends('billing_circle')
    def _usd_fx_cbn_sell_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['fipl', 'fiplo']:
                    record.usd_fx_cbn_sell_cur = record.billing_circle.cbn_selling_fss
                else:
                    record.usd_fx_cbn_sell_cur = 0

    @api.depends('vfcr', 'usd_fx_cbn_cur', 'gas_fuel_price_dollar_cur', 'vfcr_dollar_cur', 'usd_fx_cbn_sell_cur')
    def _vfcr_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['successor_gencos', 'transcorp_ugheli',  'olorunsogo', 'omotosho']:
                    record.vfcr_cur = record.vfcr * (record.usd_fx_cbn_cur / record.usd_fx_cbn) * \
                                      (record.gas_fuel_price_dollar_cur / record.gas_fuel_price_dollar)
                elif record.calculation_type in ['fipl', 'fiplo']:
                    record.vfcr_cur = record.vfcr * (record.usd_fx_cbn_sell_cur / record.usd_fx_cbn) * \
                                      (record.gas_fuel_price_dollar_cur / record.gas_fuel_price_dollar)
                elif record.calculation_type in ['shell']:
                    record.vfcr_cur = round(record.usd_fx_cbn_cur * record.vfcr_dollar_cur, 2)
                else:
                    record.vfcr_cur = 0

    @api.depends('investment_dollar', 'us_ppi_cur')
    def _investment_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.investment_dollar_cur = record.investment_dollar * record.us_ppi_cur / record.us_ppi
                else:
                    record.investment_dollar_cur = 0

    @api.depends('investment_dollar', 'us_ppi_cur')
    def _capacity_invoice(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.capacity_inv = record.capacity_charge_dollar_cur * (record.agip_dependable_capacity * 1000)
                else:
                    record.capacity_inv = 0

    @api.depends('insurance_dollar', 'us_ppi_cur', 'us_ppi')
    def _insurance_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.insurance_dollar_cur = record.insurance_dollar * record.us_ppi_cur / record.us_ppi
                else:
                    record.insurance_dollar_cur = 0

    @api.depends('general_expenses_dollar')
    def _expenses_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.general_expenses_dollar_cur = record.general_expenses_dollar
                else:
                    record.general_expenses_dollar_cur = 0

    @api.depends('fuel_dollar', 'us_ppi_cur', 'us_ppi')
    def _fuel_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.fuel_dollar_cur = record.fuel_dollar * record.us_ppi_cur / record.us_ppi
                else:
                    record.fuel_dollar_cur = 0

    @api.depends('fixed_o_m_dollar', 'us_ppi_cur', 'us_ppi')
    @api.onchange('us_ppi_cur')
    def _fixed_om_dollar(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell']:
                    record.fixed_o_m_dollar_cur = round((0.33 * record.fixed_o_m_dollar) *
                                                        (record.us_ppi_cur / record.us_ppi) + (record.fixed_o_m_dollar * 0.67), 2)
                elif record.calculation_type in ['agip']:
                    record.fixed_o_m_dollar_cur = record.fixed_o_m_dollar * record.us_ppi_cur / record.us_ppi
                else:
                    record.fixed_o_m_dollar_cur = 0

    @api.depends('variable_o_m_dollar', 'us_ppi_cur', 'us_ppi')
    def _variable_om_dollar(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell', 'agip']:
                    record.variable_o_m_dollar_cur = round(record.variable_o_m_dollar * record.us_ppi_cur/record.us_ppi, 4)
                else:
                    record.variable_o_m_dollar_cur = 0

    @api.depends('startup_dollar', 'us_ppi_cur', 'us_ppi')
    def _startup_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell', ]:
                    record.startup_dollar_cur = record.startup_dollar * record.us_ppi_cur/record.us_ppi
                else:
                    record.startup_dollar_cur = 0

    @api.depends('fuel_dollar_cur', 'variable_o_m_dollar_cur')
    def _energy_charge_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip', ]:
                    record.energy_charge_dollar_cur = record.fuel_dollar_cur + record.variable_o_m_dollar_cur
                else:
                    record.energy_charge_dollar_cur = 0

    @api.depends('investment_dollar_cur', 'fixed_o_m_dollar_cur', 'insurance_dollar_cur', 'general_expenses_dollar_cur')
    def _capacity_charge_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip',]:
                    record.capacity_charge_dollar_cur = record.investment_dollar_cur + record.fixed_o_m_dollar_cur +\
                                                        record.insurance_dollar_cur + record.general_expenses_dollar_cur
                else:
                    record.capacity_charge_dollar_cur = 0

    @api.depends('capacity_inv', 'agip_dependable_capacity', 'hours_month')
    def _capacity_charge_dollar_dup(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip', ]:
                    record.capacity_charge_dollar_dup = round(record.capacity_inv / (record.agip_dependable_capacity * record.hours_month), 6)
                else:
                    record.capacity_charge_dollar_dup = 0

    @api.depends('investment_dollar_cur', 'usd_fx_cbn_cur')
    def _investment_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip', ]:
                    record.investment_naira = record.investment_dollar_cur * record.usd_fx_cbn_cur

                else:
                    record.investment_naira = 0

    @api.depends('insurance_dollar_cur', 'usd_fx_cbn_cur')
    def _insurance_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip', ]:
                    record.insurance_naira = record.insurance_dollar_cur * record.usd_fx_cbn_cur

                else:
                    record.insurance_naira = 0

    @api.depends('general_expenses_dollar_cur', 'usd_fx_cbn_cur')
    def _general_expenses_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip', ]:
                    record.general_expenses_naira = record.general_expenses_dollar_cur * record.usd_fx_cbn_cur

                else:
                    record.general_expenses_naira = 0

    @api.depends('fuel_dollar_cur', 'usd_fx_cbn_cur')
    def _fuel_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip', ]:
                    record.fuel_naira = record.fuel_dollar_cur * record.usd_fx_cbn_cur_gas * 1000

                else:
                    record.fuel_naira = 0

    @api.depends('startup_dollar_cur', 'usd_fx_cbn_cur')
    def _startup_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell', ]:
                    record.startup_naira = record.startup_dollar_cur * record.usd_fx_cbn_cur
                else:
                    record.startup_naira = 0

    @api.depends('gas_hhv_price_dollar_cur', 'hhv_to_lhv_cur', 'efficiency_cur')
    @api.onchange('gas_hhv_price_dollar_cur')
    def _fuel_cost_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.fuel_cost_dollar_cur = record.gas_hhv_price_dollar_cur * ((record.hhv_to_lhv_cur * 3.412) / (record.efficiency_cur/100))
                else:
                    record.fuel_cost_dollar_cur = 0

    @api.depends('fuel_cost_dollar_cur', 'usd_fx_cbn_cur')
    def _fuel_cost_cur_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.fuel_cost_naira_cur = record.fuel_cost_dollar_cur * record.usd_fx_cbn_cur_gas
                else:
                    record.fuel_cost_naira_cur = 0

    @api.depends('gas_fuel_price_dollar', 'hhv_to_lhv', 'efficiency')
    def _fuel_cost(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    try:
                        record.fuel_cost_dollar = record.gas_fuel_price_dollar * record.hhv_to_lhv * 3.412 / record.efficiency
                    except:
                        record.fuel_cost_dollar = 0
                else:
                    record.fuel_cost_dollar = 0

    @api.depends('fuel_cost_dollar', 'usd_fx_cbn')
    def _fuel_cost_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.fuel_cost_naira = record.fuel_cost_dollar * record.usd_fx_cbn_cur_gas
                else:
                    record.fuel_cost_naira = 0

    @api.depends('gas_fuel_price_dollar_cur', 'usd_fx_cbn_cur')
    def _gas_price_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.gas_fuel_price_naira = record.gas_fuel_price_dollar_cur * record.usd_fx_cbn_cur_gas
                else:
                    record.gas_fuel_price_naira = 0

    @api.depends('gas_fuel_price_dollar_cur', 'usd_fx_cbn_cur')
    def _gas_hhv_price_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.gas_hhv_price_cur = record.gas_hhv_price_dollar_cur * record.usd_fx_cbn_cur_gas
                else:
                    record.gas_hhv_price_cur = 0

    @api.depends('fixed_o_m', 'usd_fx_cbn_cur', 'us_cpi_cur', 'usd_fx_cbn', 'us_cpi', 'ncpi_cur', 'ncpi', 'fixed_o_m_dollar_cur')
    @api.onchange('us_cpi_cur', 'ncpi_cur', 'usd_fx_cbn_cur')
    def _fix_om_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros','successor_gencos','transcorp_ugheli']:
                    record.fixed_o_m_cur = record.fixed_o_m * (record.usd_fx_cbn_cur / record.usd_fx_cbn) * (record.us_cpi_cur / record.us_cpi)
                elif record.calculation_type in ['fipl', 'fiplo']:
                    record.fixed_o_m_cur = record.fixed_o_m * (record.ncpi_cur/record.ncpi)
                elif record.calculation_type in ['shell', 'agip']:
                    record.fixed_o_m_cur = record.fixed_o_m_dollar_cur * record.usd_fx_cbn_cur
                elif record.calculation_type in ['olorunsogo', 'omotosho']:
                    record.fixed_o_m_cur = record.fixed_o_m * (0.85 * (record.us_cpi_cur/record.us_cpi) + (1 - 0.85) *
                                                               (record.ncpi_cur/record.ncpi)) + (0.85 * record.fixed_o_m) *\
                                           ((record.usd_fx_cbn_cur / record.usd_fx_cbn) - 1) * record.us_cpi_cur/record.us_cpi
                elif record.calculation_type in ['mabon']:
                    record.fixed_o_m_cur = record.fixed_o_m * (0.23 + 0.77 * (record.us_cpi_cur/record.us_cpi) *
                                                               (record.usd_fx_cbn_cur/record.usd_fx_cbn))
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.fixed_o_m_cur = record.fixed_o_m_noncompute

                else:
                    record.fixed_o_m_cur = 0

    @api.depends('variable_o_m', 'usd_fx_cbn_cur', 'us_cpi_cur', 'usd_fx_cbn', 'us_cpi', 'usd_fx_cbn_cur', 'ncpi_cur', 'ncpi', 'variable_o_m_dollar_cur')
    @api.onchange('us_cpi_cur', 'ncpi_cur', 'usd_fx_cbn_cur')
    def _variable_om_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'successor_gencos', 'transcorp_ugheli']:
                    record.variable_o_m_cur = record.variable_o_m * (record.usd_fx_cbn_cur / record.usd_fx_cbn) * (
                                record.us_cpi_cur / record.us_cpi)
                elif record.calculation_type in ['fipl', 'fiplo']:
                    record.variable_o_m_cur = record.variable_o_m * (record.ncpi_cur/record.ncpi)
                elif record.calculation_type in ['shell']:
                    record.variable_o_m_cur = record.variable_o_m_dollar_cur * record.usd_fx_cbn_cur
                elif record.calculation_type in ['agip']:
                    record.variable_o_m_cur = record.variable_o_m_dollar_cur * record.usd_fx_cbn_cur * 1000
                elif record.calculation_type in ['olorunsogo', 'omotosho', ]:
                    record.variable_o_m_cur = record.variable_o_m * (0.85 * (record.us_cpi_cur/record.us_cpi)
                                                                     + (1 - 0.85) * (record.ncpi_cur/record.ncpi)) + \
                                              (0.85 * record.variable_o_m) * ((record.usd_fx_cbn_cur/record.usd_fx_cbn)
                                                                              - 1) * record.us_cpi_cur/record.us_cpi
                elif record.calculation_type in ['mabon']:
                    record.variable_o_m_cur = record.variable_o_m
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.variable_o_m_cur = record.variable_o_m_noncompute

                else:
                    record.variable_o_m_cur = 0

    @api.depends('capital_recovery_dollar', 'us_ppi_cur', 'us_ppi')
    def _capital_recovery_dollar_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell', ]:
                    record.capital_recovery_dollar_cur = (record.capital_recovery_dollar * 0.67) + \
                                                         (record.capital_recovery_dollar * 0.33) * (record.us_ppi_cur / record.us_ppi)
                elif record.calculation_type in ['agip']:
                    record.capital_recovery_dollar_cur = 0
                else:
                    record.capital_recovery_dollar_cur = 0

    @api.depends('capital_recovery', 'usd_fx_cbn_cur', 'usd_fx_cbn', 'capital_recovery_dollar_cur')
    def _capital_recovery_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'successor_gencos', 'transcorp_ugheli', 'fipl', 'fiplo', 'olorunsogo', 'omotosho' ]:
                    record.capital_recovery_cur = record.capital_recovery * (record.usd_fx_cbn_cur / record.usd_fx_cbn)
                elif record.calculation_type in ['shell']:
                    record.capital_recovery_cur = record.capital_recovery_dollar_cur * record.usd_fx_cbn_cur
                elif record.calculation_type in ['mabon']:
                    record.capital_recovery_cur = record.capital_recovery * (0.25 + 0.75 * (record.usd_fx_cbn_cur/record.usd_fx_cbn))
                elif record.calculation_type in ['agip']:
                    record.capital_recovery_cur = 0
                else:
                    record.capital_recovery_cur = 0

    @api.onchange('usd_fx_cbn_cur')
    def _onchange_cbn_fx(self):
        self._vfcr_cur()

    @api.depends('variable_o_m_cur', 'vfcr_cur', 'fuel_cost_naira_cur', 'trans_loss_cost_cur', 'tax_cost_cur',
                 'variable_o_m_noncompute', 'energy_charge_cur_noncompute')
    @api.onchange('energy_charge_cur_noncompute')
    def _energy_charge_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type == 'hydros':
                    record.energy_charge_cur = record.variable_o_m_cur
                elif record.calculation_type in ['successor_gencos', 'fipl', 'transcorp_ugheli', 'fiplo', 'shell', 'olorunsogo', 'omotosho']:
                    record.energy_charge_cur = record.vfcr_cur + record.variable_o_m_cur
                elif record.calculation_type in ['agip']:
                    record.energy_charge_cur = record.fuel_naira + record.variable_o_m_cur
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp' ]:
                    record.energy_charge_cur = record.fuel_cost_naira_cur + record.variable_o_m_noncompute + \
                                               record.trans_loss_cost_cur + (1/3 * record.tax_cost_cur)
                elif record.calculation_type in ['mabon']:
                    record.energy_charge_cur = record.energy_charge
                elif record.calculation_type in ['direct_input']:
                    record.energy_charge_cur = record.energy_charge_cur_noncompute
                else:
                    record.energy_charge_cur = 0

    @api.depends('energy_charge_cur')
    def _energy_charge_tlf(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'successor_gencos', 'transcorp_ugheli', 'olorunsogo', 'omotosho', 'fipl', 'fiplo']:
                    record.energy_charge_tlf = record.energy_charge_cur - record.wholesale_charge_cur * (1-((100-record.old_tlf) / (100-record.new_tlf)))
                elif record.calculation_type in ['shell', ]:
                    record.energy_charge_tlf = record.energy_charge_cur / ((100 - record.new_tlf)/100)
                elif record.calculation_type in ['agip', ]:
                    record.energy_charge_tlf = record.energy_charge_cur * (0.997 / ((100 - record.new_tlf)/100))
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp', 'mabon', 'direct_input']:
                    record.energy_charge_tlf = record.energy_charge_cur
                else:
                    record.energy_charge_tlf = 0

    @api.depends('capital_recovery_cur', 'fixed_o_m_cur', 'fixed_o_m_noncompute', 'capital_cost_cur', 'tax_cost_cur',
                 'capacity_charge_cur_noncompute')
    @api.onchange('capacity_charge_cur_noncompute')
    def _capacity_charge_cur(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'successor_gencos', 'transcorp_ugheli', 'fipl', 'fiplo', "shell", 'olorunsogo', 'omotosho', 'mabon']:
                    record.capacity_charge_cur = record.capital_recovery_cur + record.fixed_o_m_cur
                elif record.calculation_type in ['agip']:
                    try:
                        record.capacity_charge_cur = record.capacity_charge_dollar_dup * record.usd_fx_cbn_cur
                    except ZeroDivisionError:
                        record.capacity_charge_cur = 0.00
                    # record.capacity_charge_cur = record.investment_naira + record.fixed_o_m_cur + record.insurance_naira \
                    #                              + record.general_expenses_naira
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.capacity_charge_cur = record.fixed_o_m_noncompute + record.capital_cost_cur + (0.666 * record.tax_cost_cur)
                elif record.calculation_type in ['direct_input']:
                    record.capacity_charge_cur = record.capacity_charge_cur_noncompute
                else:
                    record.capacity_charge_cur = 0

    @api.depends('capacity_charge_cur', 'energy_charge_cur')
    def _wholesale_charge_cur(self):
        for record in self:
            if record.calculation_type:
                record.wholesale_charge_cur = record.capacity_charge_cur + record.energy_charge_cur




