from odoo import models, fields, api
from odoo.addons.ebs_ocma.models.billing_cycle import MONTHS, YEARS

class DiscoInvoicing(models.Model):
    _name = 'ebs_ocma.disco.invoicing'
    _description = 'Disco Invoicing'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    billing_cycle_id = fields.Many2one(comodel_name="billing.cycle", string="Billing Cycle", required=False)
    # month = fields.Selection(selection=MONTHS, string='Billing Month')
    month = fields.Char(string='Billing Month', compute='_get_month_name')
    date = fields.Date(string='Date', required=False)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco')
    
    contract_share = fields.Float(string='Contract Share of Energy/Capacity (%)', related='partner_id.contract_capacity_share')
    share_actual_bill = fields.Float(string='Share actually billed (%)')
    total_available_capacity = fields.Float('Total available capacity (average) MW', compute='_genco_total_capacity')
    total_disco_share = fields.Float(string='Total disco share of available capacity MW')
    share_available = fields.Float(string='Share of available capacity (MW)')
    total_energy_sent_out = fields.Float(string='Total energy sent out (MWh)', compute='_compute_total_energy_sent_out')
    total_disco_share_enegry_sent_out = fields.Float(string='Total discos share of energy sent out')
    share_energy_sent_out = fields.Float(string='Share of energy sent out (MWh)')
    aggregate_supplementary_charge = fields.Float(string='Aggregate Supplementary Charge')
    quateryly_index = fields.Float(string='Quarterly Index')

    @api.onchange('contract_share')
    def _onchange_contract_share(self):
        for rec in self:
            rec.share_actual_bill = rec.contract_share
    
    def _genco_total_capacity(self):
        for rec in self:
            related_genco_invoicing = self.env["ebs_ocma.genco.invoice"].search([("billing_cycle_id", "=", rec.billing_cycle_id.id)], limit=1)
            rec.total_available_capacity = related_genco_invoicing.total_capacity

    def _compute_total_energy_sent_out(self):
        for rec in self:
            related_genco_invoicing = self.env["ebs_ocma.genco.invoice"].search([("billing_cycle_id", "=", rec.billing_cycle_id.id)], limit=1)
            rec.total_energy_sent_out = related_genco_invoicing.total_energy_sent_out_mwh
            