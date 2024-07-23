from odoo import models, fields, api, _
from calendar import monthrange
from datetime import date

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError


class MytoRates(models.Model):
    _name = 'ocma.myto.rate'
    _description = 'Myto Rate'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Description', track_visibility='onchange')
    approved_by = fields.Many2one(comodel_name="hr.employee", string="Approved by")
    line_ids = fields.One2many(comodel_name="hydro.rates", inverse_name="rate_id", string="Rates")
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'To Approve'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled'),
    ], string='state', default="draft", readonly=True)
    active = fields.Boolean(string='Active', default=True)
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
    ], string='Calculation Type', track_visibility='onchange')

    usd_fx_cbn = fields.Float(
        string='Usd/naira fx CBN',
        required=False, track_visibility='onchange')
    us_cpi = fields.Float(
        string='US Cpi (index)',
        required=False, track_visibility='onchange')
    old_tlf = fields.Float(
        string='Old TLF',
        required=False, track_visibility='onchange')
    fixed_o_m = fields.Float(string='Fixed O & M(n/mw/hr)', required=False, digits='Ocma', track_visibility='onchange')
    variable_o_m = fields.Float(
        string='Variable O & M(n/mw/hr)',
        required=False, track_visibility='onchange', digits='Ocma')
    fixed_o_m_dollar = fields.Float(string='Fixed O & M($/mw/hr)', required=False, digits='Ocma', track_visibility='onchange')
    variable_o_m_dollar = fields.Float(string='Variable O & M($/mw/hr)', required=False, digits='Ocma', track_visibility='onchange')

    capital_recovery = fields.Float(string='Capital recovery(n/mw/hr)', required=False, track_visibility='onchange', digits='Ocma')
    capital_recovery_dollar = fields.Float(string='Capital recovery($/mw/hr)', required=False, track_visibility='onchange', digits='Ocma')
    energy_charge = fields.Float(string='Energy charge(n/mw/hr)', required=False, compute="_energy_charge", track_visibility='onchange', digits='Ocma')
    capacity_charge = fields.Float(string='Capacity charge(n/mw/hr)', required=False, compute="_capacity_charge", track_visibility='onchange', digits='Ocma')
    energy_charge_dollar = fields.Float(string='Energy charge($/mw/hr)', required=False, digits='Ocma',
                                        compute="_energy_charge_dollar", track_visibility='onchange')
    capacity_charge_dollar = fields.Float(string='Capacity charge($/mw/hr)', required=False,
                                          compute="_capacity_charge_dollar", track_visibility='onchange', digits='Ocma')
    wholesale_charge = fields.Float(string='Wholesale charge(n/mw/hr)', required=False, compute="_wholesale_charge", track_visibility='onchange', digits='Ocma')
    billing_circle = fields.Many2one(
        comodel_name='billing.cycle',
        string='Billing cycle',
        required=False)
    gas_fuel_price = fields.Float(string='Gas Fuel Price(N/mmbtu)', required=False, digits='Ocma')
    gas_fuel_price_dollar = fields.Float(string='Gas Fuel Price($/mmbtu)', required=False, digits='Ocma')
    gas_hhv_price = fields.Float(string='Gas Price HHV(N/mmbtu)', required=False, compute="_gas_price_naira")
    gas_hhv_price_dollar = fields.Float(string='Gas Price HHV($/mmbtu)', required=False)
    vfcr = fields.Float(string='VFCR(n/mwh)', required=False, track_visibility='onchange', digits='Ocma')
    vfcr_dollar = fields.Float(string='VFCR($/mwh)', required=False, track_visibility='onchange', digits='Ocma')
    startup_dollar = fields.Float(string='Startup dollar', required=False)
    startup_naira = fields.Float(string='Startup Naira', required=False, compute='_startup_naira')

    ncpi = fields.Float(string='NCPI(index)', required=False, track_visibility='onchange',  digits='Ocma')
    us_ppi = fields.Float(string='US PPI(Index)', required=False, digits='Ocma')
    investment_dollar = fields.Float(string='Investment($/kw/month)', required=False, digits='Ocma')
    general_expenses_dollar = fields.Float(string='General Expenses($/kw/month)', required=False, digits='Ocma')
    insurance_dollar = fields.Float(string='Insurance($/kw/month)', required=False, digits='Ocma')
    fuel_dollar = fields.Float(string='Fuel($/mw/hr)', required=False, digits='Ocma', compute='_fuel_cost_dollar')
    fuel_dollar_input = fields.Float(string='Fuel($/mw/hr)', required=False, digits='Ocma',)
    investment_naira = fields.Float(
        string='Investment(n/kw/month)',
        required=False)
    general_expenses_naira = fields.Float(
        string='General Expenses(n/kw/month)',
        required=False)
    insurance_naira = fields.Float(
        string='Insurance(n/kw/month)',
        required=False)
    fuel_naira = fields.Float(string='Fuel Cost(n/mw/hr)', required=False, compute='_fuel_cost_naira')
    hhv_to_lhv = fields.Float(string='HHV to LHV Conversion ratio', required=False)
    efficiency = fields.Float(string='Efficiency %', required=False)
    capital_cost = fields.Float(string='Capital cost(n/mw/hr)', required=False)
    tax_cost = fields.Float(string='Tax Cost(n/mw/hr)', required=False)
    transmission_loss_cost = fields.Float(string='Transmission Loss Cost(0.75%)', required=False)
    wholesale_charge_net = fields.Float(string='Wholesale Tariff net HYPADEC(N/MW/Hr)', required=False,
                                        compute='_wholesale_charge_net')

    def action_submit(self):
        self.state = 'open'

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'reject'

    def action_cancel(self):
        self.state = 'cancel'

    def _startup_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['shell']:
                    record.startup_naira = record.startup_dollar * record.usd_fx_cbn
                else:
                    record.startup_naira = 0

    def _gas_price_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.gas_hhv_price = record.gas_hhv_price_dollar * record.usd_fx_cbn
                elif record.calculation_type in ['mabon', 'hydros', 'successor_gencos']:
                    record.gas_hhv_price = 0
                else:
                    record.gas_hhv_price = 0

    def _fuel_cost_dollar(self):
        for record in self:
            if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                if record.efficiency > 0:
                    record.fuel_dollar = record.gas_hhv_price_dollar * record.hhv_to_lhv * 3.412 / (
                                record.efficiency / 100)
                else:
                    record.fuel_dollar = 0  # Or handle the zero efficiency case appropriately
            elif record.calculation_type == 'agip':
                record.fuel_dollar = record.fuel_dollar_input
            elif record.calculation_type in ['mabon', 'hydros', 'successor_gencos']:
                record.fuel_dollar = 0
            else:
                record.fuel_dollar = 0

    def _fuel_cost_naira(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.fuel_naira = record.fuel_dollar * record.usd_fx_cbn
                elif record.calculation_type in ['mabon', 'hydros', 'successor_gencos']:
                    record.fuel_naira = 0
                else:
                    record.fuel_naira = 0

    def _capacity_charge(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'mabon']:
                    record.capacity_charge = record.capital_recovery + record.fixed_o_m
                elif record.calculation_type in ['successor_gencos', 'transcorp_ugheli', 'fipl', 'fiplo', 'olorunsogo', 'omotosho']:
                    record.capacity_charge = record.capital_recovery + record.fixed_o_m
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.capacity_charge = record.fixed_o_m + record.capital_cost + (2/3 * record.tax_cost)
                elif record.calculation_type in ['shell', 'agip']:
                    record.capacity_charge = 0
                else:
                    record.capacity_charge = 0

    def _capacity_charge_dollar(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.capacity_charge_dollar = record.investment_dollar + record.fixed_o_m_dollar + \
                                                    record.insurance_dollar + record.general_expenses_dollar
                elif record.calculation_type in ['olorunsogo', 'omotosho', 'ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.capacity_charge_dollar = 0
                else:
                    record.capacity_charge_dollar = 0

    def _energy_charge(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['hydros', 'mabon']:
                    record.energy_charge = record.variable_o_m
                elif record.calculation_type in ['successor_gencos', 'transcorp_ugheli', 'fipl', 'fiplo', 'olorunsogo', 'omotosho']:
                    record.energy_charge = record.vfcr + record.variable_o_m
                elif record.calculation_type in ['ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.energy_charge = record.fuel_naira + record.variable_o_m + record.transmission_loss_cost + (1/3 * record.tax_cost)
                elif record.calculation_type in ['shell', 'agip']:
                    record.energy_charge = 0
                else:
                    record.energy_charge = 0

    def _energy_charge_dollar(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['agip']:
                    record.energy_charge_dollar = record.fuel_dollar + record.variable_o_m_dollar
                # if record.calculation_type in ['olorunsogo', 'omotosho', 'ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                #     record.energy_charge_dollar = 0
                else:
                    record.energy_charge_dollar = 0

    def _wholesale_charge_net(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type in ['mabon']:
                    record.wholesale_charge_net = record.capacity_charge + record.energy_charge
                else:
                    record.wholesale_charge_net = 0

    def _wholesale_charge(self):
        for record in self:
            if record.calculation_type:
                if record.calculation_type == 'hydros':
                    record.wholesale_charge = record.capacity_charge + record.energy_charge
                elif record.calculation_type in ['successor_gencos', 'transcorp_ugheli', 'fipl', 'fiplo', 'olorunsogo',
                                               'omotosho', 'ibom', 'nipps', 'calabar_nipp', 'gbarain_nipp']:
                    record.wholesale_charge = record.capacity_charge + record.energy_charge
                elif record.calculation_type in ['mabon']:
                    record.wholesale_charge = record.wholesale_charge_net
                elif record.calculation_type in ['shell', 'agip']:
                    record.wholesale_charge = 0

                else:
                    record.wholesale_charge = 0


class HydroRates(models.Model):
    _name = 'hydro.rates'
    _description = 'Hydro Rates'

    name = fields.Char()
    # rates_category = fields.Many2one(
    #     comodel_name='rate.category',
    #     string='Rates category',
    #     required=False)
    usd_fx_cbn = fields.Float(
        string='Usd/naira fx CBN',
        required=False)
    us_cpi = fields.Float(
        string='US Cpi (index)',
        required=False)
    new_tlf = fields.Float(
        string='New TLF (index)',
        required=False)
    rate_id = fields.Many2one(
        comodel_name='ocma.myto.rate',
        string='Rate_id',
        required=False)
    fixed_o_m = fields.Float(
        string='Fixed O & M(n/mw/hr)',
        required=False)
    variable_o_m = fields.Float(
        string='Variable O & M(n/mw/hr)',
        required=False)
    fixed_o_m_dollar = fields.Float(
        string='Fixed O & M($/mw/hr)',
        required=False)
    variable_o_m_dollar = fields.Float(
        string='Variable O & M($/mw/hr)',
        required=False)

    capital_recovery = fields.Float(
        string='Capital recovery(n/mw/hr)',
        required=False)
    energy_charge = fields.Float(
        string='Energy charge(n/mw/hr)',
        required=False)
    energy_charge_tlf = fields.Float(
        string='Energy charge new TLF(n/mw/hr)',
        required=False)
    capacity_charge = fields.Float(
        string='Capacity charge(n/mw/hr)',
        required=False)
    wholesale_charge = fields.Float(
        string='Wholesale charge(n/mw/hr)',
        required=False)
    billing_circle = fields.Many2one(
        comodel_name='billing.cycle',
        string='Billing cycle',
        required=False)
    gas_fuel_price = fields.Float(
        string='Gas Fuel Price($/mmbtu)',
        required=False)
    vfcr = fields.Float(
        string='VFCR(n/mwh)',
        required=False)
    ncpi = fields.Float(
        string='NCPI(index)',
        required=False)
    us_ppi = fields.Float(
        string='US PPI(Index)',
        required=False)
    investment_dollar = fields.Float(
        string='Investment($/kw/month)',
        required=False)
    general_expenses_dollar = fields.Float(
        string='General Expenses($/kw/month)',
        required=False)
    insurance_dollar = fields.Float(
        string='Insurance($/kw/month)',
        required=False)
    fuel_dollar = fields.Float(
        string='Wholesale charge($/mw/hr)',
        required=False)
    investment_naira = fields.Float(
        string='Investment(n/kw/month)',
        required=False)
    general_expenses_naira = fields.Float(
        string='General Expenses(n/kw/month)',
        required=False)
    insurance_naira = fields.Float(
        string='Insurance(n/kw/month)',
        required=False)
    fuel_naira = fields.Float(
        string='Wholesale charge(n/mw/hr)',
        required=False)
    # wholesale_charge = fields.Float(
    #     string='Wholesale charge(n/mw/hr)',
    #     required=False)
    # wholesale_charge = fields.Float(
    #     string='Wholesale charge(n/mw/hr)',
    #     required=False)
    # wholesale_charge = fields.Float(
    #     string='Wholesale charge(n/mw/hr)',
    #     required=False)
    # wholesale_charge = fields.Float(
    #     string='Wholesale charge(n/mw/hr)',
    #     required=False)
    # wholesale_charge = fields.Float(
    #     string='Wholesale charge(n/mw/hr)',
    #     required=False)
    # wholesale_charge = fields.Float(
    #     string='Wholesale charge(n/mw/hr)',
    #     required=False)






