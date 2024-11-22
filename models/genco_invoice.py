from datetime import date, datetime
from odoo import models, fields, api, _
from odoo.addons.ebs_ocma16.models.billing_cycle import MONTHS, YEARS
from odoo.exceptions import UserError

class GencoInvoice(models.Model):
    _name = 'ebs_ocma.genco.invoice'
    _description = 'Genco Invoice'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Description')
    billing_cycle_id = fields.Many2one(comodel_name="billing.cycle", string="Billing Cycle")
    title = fields.Char(string='Title')
    month = fields.Selection(selection=MONTHS, string='Billing Month')
    year = fields.Selection(selection=YEARS,
                            string='Billing Year', store=True)
    days_in_month = fields.Integer('Days In Month', default="30")
    date = fields.Date(string='Date', required=False, default=lambda self: date.today())
    ref_no = fields.Char(string='Reference Number', required=False)
    genco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.genco.invoice.parameter", inverse_name="invoice_id", string="Genco Parameters")
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Validate'),
        # ('approve', 'Done'),
        ('invoice_verification', 'Invoice Verification'),
        ('done', 'Verified'),
    ], string='state', default="draft", help="A new record is in draft, once it is validated, it goes to open and then it is approved in Done state")
    
    cbn_average = fields.Float(string='CBN Average', related='billing_cycle_id.cbn_average')
    nbet_dist_rate = fields.Float(string='Nbet Dist Rate', related='billing_cycle_id.nbet_dist_rate')
    nbet_dist_azura = fields.Float(string='Nbet Dist Azura', related='billing_cycle_id.nbet_dist_azura')
    agip_quaterly_index = fields.Float(string="Agip Quaterly Index", related='billing_cycle_id.agip_quaterly_index')
    azura_fx_date = fields.Date(string="Azura FX Date", related='billing_cycle_id.azura_fx_date')
    azura_fx_value = fields.Float(string="Azura FX Value", related='billing_cycle_id.azura_fx_value')

    weighted_cost_power = fields.Float('Weighted Cost of Power (Capacity)', compute='_compute_weighted_cost_power')
    weighted_avg_cost_power = fields.Float('Weighted Average Cost of Power (Capacity) ', compute='_compute_weighted_avg_cost_power')

    total_capacity = fields.Float(string='Total Capacity', compute='_compute_total_capacity')
    total_energy_sent_out_mwh = fields.Float(string='Total Energy Sent Out(MWh)', compute='_compute_total_energy_sent_out_mwh')

    genco_invoice_ids = fields.Many2many(comodel_name='account.move', string='Genco Bills', copy=False)
    genco_invoices_count = fields.Integer(string='Invoices Count', compute="_compute_invoices_count")

    nbet_genco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.nbet.genco.invoice", inverse_name="invoice_id", string="NBET Genco Parameters")

    # @api.model
    # def create(self, vals):
    #     res = super(GencoInvoice, self).create(vals)
    #     res._create_genco_invoice_parameter()
    #     return res

    def _compute_invoices_count(self):
        self.genco_invoices_count = len(self.genco_invoice_ids)

    def action_view_genco_invoices(self):
        # action = self.env.ref('account.action_vendor_bill_template')
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        if self.genco_invoices_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.genco_invoice_ids.ids) + ")]"
        elif self.genco_invoices_count == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.genco_invoice_ids.id
        return result

    def action_confirm(self):
        self.write({
            'state': 'open'
        })
        
    # def action_approve(self):
    #     self.write({
    #         'state': 'approve'
    #     })

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'invoice_verification'})
            if not self.nbet_genco_parameter_ids:
                GencoParameter = self.env['ebs_ocma.nbet.genco.invoice'].sudo()
                genco_parameter_ids = self.nbet_genco_parameter_ids
                for line in rec.genco_parameter_ids:
                    new_genco_parameter = GencoParameter.create(
                        {
                            'name': line.partner_id and line.partner_id.name,
                            'partner_id': line.partner_id and line.partner_id.id,
                            'invoice_id': self.id,
                            # 'capacity_payment': line.capacity_payment,
                            # 'energy_payment': line.energy_payment,
                        }
                    )
                    genco_parameter_ids += new_genco_parameter

    def _create_genco_invoice_parameter(self):
        GencoParameter = self.env['ebs_ocma.genco.invoice.parameter'].sudo()
        genco_parameter_ids = self.genco_parameter_ids
        if self.billing_cycle_id and self.billing_cycle_id.genco_inv_verify:
            for line in self.billing_cycle_id.genco_inv_verify:
                new_genco_parameter = GencoParameter.create(
                    {
                        'name': line.genco_id and line.genco_id.name,
                        'partner_id': line.genco_id and line.genco_id.id,
                        'invoice_id': self.id,
                        'capacity_payment': line.capacity_payment,
                        'energy_payment': line.energy_payment,
                    }
                )
                genco_parameter_ids += new_genco_parameter
        else:
            gencos = self.env['res.partner'].sudo().search([('is_genco', '=', True)])
            for genco in gencos:
                new_genco_parameter = GencoParameter.create(
                    {
                        'name': genco.name,
                        'partner_id': genco.id,
                        'invoice_id': self.id,
                    }
                )
                genco_parameter_ids += new_genco_parameter

    # @api.onchange('billing_cycle_id')
    # def _onchange_billing_cycle_id(self):
    #     GencoParameter = self.env['ebs_ocma.genco.invoice.parameter'].sudo()
    #     self.genco_parameter_ids.sudo().unlink()
    #     genco_parameter_ids = self.genco_parameter_ids
        # gencos = self.env['res.partner'].sudo().search([('is_genco', '=', True)])
        # if self.billing_cycle_id:
            
        #     self.month = self.billing_cycle_id and self.billing_cycle_id.month
        #     self.year = self.billing_cycle_id and self.billing_cycle_id.year
        #     for line in self.billing_cycle_id.genco_inv_verify:
        #         new_genco_parameter = GencoParameter.create(
        #             {
        #                 'name': line.genco_id and line.genco_id.name,
        #                 'partner_id': line.genco_id and line.genco_id.id,
        #                 'invoice_id': self._origin.id,
        #                 'capacity_payment': line.capacity_payment,
        #                 'energy_payment': line.energy_payment,
        #             }
        #         )
        #         genco_parameter_ids += new_genco_parameter
    
    def _compute_weighted_cost_power(self):
        for rec in self:
            for line in rec.genco_parameter_ids:
                rec.weighted_cost_power += (line.capacity_payment / line.capacity) if line.capacity != 0 else 0
                
    def _compute_weighted_avg_cost_power(self):
        for rec in self:
            for line in rec.genco_parameter_ids:
                rec.weighted_avg_cost_power += line.energy_payment / line.energy_sent_out_mwh if line.energy_sent_out_mwh != 0 else 0

    def _compute_total_capacity(self):
        for rec in self:
            for line in rec.genco_parameter_ids:
                rec.total_capacity += line.capacity
    
    def _compute_total_energy_sent_out_mwh(self):
        for rec in self:
            for line in rec.genco_parameter_ids:
                rec.total_energy_sent_out_mwh += line.energy_sent_out_mwh

    def _create_invoice(self, partner_id, ref, origin, invoice_value):
        self.ensure_one()
        company_id = self.env.user.company_id.id
        # journal_id = (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id).default_get(['journal_id'])['journal_id'])
        journal_id = self.env.ref('ebs_ocma.genco_invoice_journal').id or (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id).default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('Please define an accounting journal.'))

        for rec in self:
            invoice_vals = {
                'ref': rec.name or '',
                'move_type': 'in_invoice',
                'billing_circle_id': rec.billing_cycle_id.id,
                
                'partner_id': partner_id.id,
                'invoice_date': rec.date,

                'invoice_origin': origin,
                # 'account_id': partner_id.property_account_receivable_id.id,

                'journal_id': journal_id,
                'company_id': company_id,

                # 'user_id': self.user_id and self.user_id.id,
                # 'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
                # 'payment_term_id': self.payment_term_id.id,
                # 'currency_id': self.pricelist_id.currency_id.id,
                
                'invoice_line_ids': [(0, 0, {
                    'name': ref,
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': invoice_value,
                })],
            }
            invoice_id = self.env['account.move'].create(invoice_vals)
            self.genco_invoice_ids += invoice_id

    def generate_genco_invoice(self):
        for rec in self:
            for line in rec.genco_parameter_ids:
                if line.verified:
                    rec._create_invoice(partner_id=line.partner_id, ref=line.name, invoice_value=line.total_payment, origin=self.ref_no)
            for line in rec.nbet_genco_parameter_ids:
                if line.verified:
                    rec._create_invoice(partner_id=line.partner_id, ref=line.name, invoice_value=line.total_payment, origin=self.ref_no)

    def action_verify(self):
        for rec in self:
            rec.generate_genco_invoice()
            rec.write({'state': 'done'})
            for invoice in rec.genco_invoice_ids:
                if invoice.amount_total > 0 :
                    # invoice.action_invoice_open()
                    invoice.action_post()

class GencoParaemeter(models.Model):
    _name = 'ebs_ocma.genco.invoice.parameter'
    _description = 'Genco Parameters'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')
    capacity_sent_out_mw = fields.Float(string='Capacity Sent Out (MW)')
    energy_sent_out_kwh = fields.Float(string='Energy Sent Out (kWh)')
    capacity_import = fields.Float(string='Capacity Import (MW)')
    energy_import = fields.Float(string='Energy Import (kWh)')

    invoiced_capacity = fields.Float(string='Invoiced Capacity', compute='_compute_invoice_capacity')
    invoiced_energy = fields.Float(string='Invoiced Energy', compute='_compute_invoiced_energy')

    capacity = fields.Float('capacity', compute='_compute_capacity')
    energy_sent_out_mwh = fields.Float(string='Energy Sent Out (MWh)', compute='_compute_energy_sent_out_mwh')
    capacity_payment = fields.Float('Capacity Payment', compute='_compute_capacity_payment')
    energy_payment = fields.Float('Energy Payment', compute='_compute_energy_payment')
    total_payment = fields.Float('Total Payment', compute='_compute_total_payment')

    invoice_id = fields.Many2one(comodel_name='ebs_ocma.genco.invoice', string="Genco Invoice")

    verified = fields.Boolean(string='verified invoice')
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name

    def _compute_invoice_capacity(self):
        for rec in self:
            rec.invoiced_capacity = rec.capacity_sent_out_mw - rec.capacity_import

    def _compute_invoiced_energy(self):
        for rec in self:
            rec.invoiced_energy = (rec.invoice_id.billing_cycle_id.transmission_loss_factor/100 * rec.energy_sent_out_kwh) - rec.energy_import
    
    def _compute_capacity(self):
        for rec in self:
            try:
                # rec.capacity = rec.capacity_sent_out_mw / rec.invoice_id.billing_cycle_id.hours_in_month
                rec.capacity = rec.invoiced_capacity / rec.invoice_id.billing_cycle_id.hours_in_month
            except ZeroDivisionError:
                rec.capacity = 0.00

    def _compute_energy_sent_out_mwh(self):
        for rec in self:
            # rec.energy_sent_out_mwh = rec.energy_sent_out_kwh / 1000
            if rec.invoiced_energy > 0:
                rec.energy_sent_out_mwh = rec.invoiced_energy / 1000
            else:
                rec.energy_sent_out_mwh = 0

    def _compute_capacity_payment(self):
        for rec in self:
            rec.capacity_payment = rec.capacity * rec.invoice_id.billing_cycle_id.hours_in_month * rec.partner_id.rate
    
    def _compute_energy_payment(self):
        for rec in self:
            rec.energy_payment = rec.energy_sent_out_mwh * rec.partner_id.rate_gas_price
            # rec.energy_payment = rec.invoiced_energy * rec.partner_id.rate_gas_price

    def _compute_total_payment(self):
        for rec in self:
            rec.total_payment = rec.capacity_payment + rec.energy_payment
            try:
                rec.capacity = rec.capacity_sent_out_mw / rec.invoice_id.billing_cycle_id.hours_in_month
            except ZeroDivisionError:
                rec.capacity = 0.0

class GencoParaemeter(models.Model):
    _name = 'ebs_ocma.nbet.genco.invoice'
    _description = 'NBET Genco Parameters'
    
    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')
    capacity_payment = fields.Float('Capacity Payment')
    energy_payment = fields.Float('Energy Payment')
    total_payment = fields.Float('Total Payment')

    invoice_id = fields.Many2one(comodel_name='ebs_ocma.genco.invoice', string="Genco Invoice")

    verified = fields.Boolean(string='verified invoice')