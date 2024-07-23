from odoo import models, fields, api, _
import datetime
import calendar
from calendar import monthrange
from datetime import date

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

YEARS = [
    ('2000', '2000'),
    ('2001', '2001'),
    ('2002', '2002'),
    ('2003', '2003'),
    ('2004', '2004'),
    ('2005', '2005'),
    ('2006', '2006'),
    ('2020', '2020'),
    ('2021', '2021'),
    ('2022', '2022'),
    ('2023', '2023'),
]

MONTHS = [
    ('JAN', 'January'), 
    ('FEB', 'February'), 
    ('MAR', 'March'), 
    ('APR', 'April'),
    ('MAY', 'May'), 
    ('JUN', 'June'), 
    ('JUL', 'July'), 
    ('AUG', 'August'),
    ('SEPT', 'September'), 
    ('OCT', 'October'), 
    ('NOV', 'November'),
    ('DEC', 'December'), 
]

class BillingCycle(models.Model):
    _name = 'billing.cycle'
    _description = 'Billing Cycle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    title = fields.Char(string='Title')

    name = fields.Char(string='Billing Cycle', compute="billing_cycle")
    month = fields.Char(string='Billing Month', compute='_get_month_name')
    year = fields.Char(string='Billing Year',  compute='_get_year')
    days_in_month = fields.Integer('Days In Month', default="30", compute="_compute_days_in_month")
    
    date = fields.Date(
        string='FSS Date',
        required=False)
    date_start = fields.Date(
        string='Start Date',
        required=False)
    date_end = fields.Date(
        string='End Date',
        required=False)
    date_average_compute = fields.Date(
        string='Date for Average Computation',
        required=False, default=lambda self: fields.Date.context_today(self))
    ref_no = fields.Char(
        string='Reference Number',
        required=False)

    ref_sequence = fields.Char(
        string='Sequence No.', readonly=True, index=True, copy=False, default='New')

    genco_inv_verify = fields.One2many(
        comodel_name='genco.verify',
        inverse_name='billing_cycle_id',
        string='Genco_inv_verify',
        required=False)
    genco_inv_verify_dollars = fields.One2many(
        comodel_name='genco.verify_dollars',
        inverse_name='billing_cycle_id',
        string='Genco_inv_verify dollars',
        required=False)
    cbn_average = fields.Float(
        string='CBN Average',
        required=False, tracking=True)
    nbet_dist_rate = fields.Float(
        string='Nbet Dist Rate',
        required=False, tracking=True)
    nbet_dist_azura = fields.Float(
        string='Nbet Dist Azura',
        required=False, tracking=True)
    additional_notes = fields.Text(
        string="Notes",
        required=False, tracking=True)

    hours_in_month = fields.Float(string='Hours in Month', compute="_compute_hours_in_month")
    transmission_loss_factor = fields.Float(string="Transmission Loss Factor")
    agip_quaterly_index = fields.Float(string="Agip Quaterly Index")
    azura_fx_date = fields.Date(string="Azura FX Date")
    azura_fx_value = fields.Float(string="Azura FX Value")
    user_id = fields.Many2one(
        comodel_name='res.users', string='Responsible User.', default=lambda self: self.env.uid)
    payments_ids = fields.One2many('accounts.payments', compute='_circle_payments', string='Payments')
    receipts_ids = fields.One2many('accounts.payments', compute='_circle_receipts', string='Disco Receipts')
    tlf_applied = fields.Boolean(string='Tlf applied', required=False)
    cbn_selling_fss = fields.Float(string='CBN Selling FSS', compute='_compute_cbn_selling')
    cbn_gas = fields.Float(string='Gas FX Rate')
    cbn_selling_average = fields.Float(string='CBN Selling Average',)
    selling_average_computed = fields.Boolean(string='Selling Average Computed', default=False)
    cbn_buying_fss = fields.Float(string='CBN Buying FSS', compute='_compute_cbn_buying')
    cbn_buying_average = fields.Float(string='CBN Buying Average', )
    buying_average_computed = fields.Boolean(string='Buying Average Computed', default=False)
    cbn_central_fss = fields.Float(string='CBN Central FSS', compute='_compute_cbn_central')

    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Validate'),
        ('gen_inv', 'Generate Invoices'),
        ('mro_application', 'MRO Application'),
        ('invoice_verification', 'Bills Verification'),
        ('gen_bill', 'Generate Verified Bills'),
    ], string='state', default="draft", help="A new record is in draft, once it is validated, it goes to open and then it is approved in Done state")

    @api.depends('date')
    def _compute_cbn_selling(self):
        cbnrate = self.env['cbn.dollar.rate']
        for fss in self:
            rate = cbnrate.search([('rate_date', '=', fss.date)], limit=1).selling_rate
            fss.cbn_selling_fss = rate if rate else 0.0

    @api.depends('date')
    def _compute_cbn_buying(self):
        cbnrate = self.env['cbn.dollar.rate']
        for fss in self:
            rate = cbnrate.search([('rate_date', '=', fss.date)], limit=1).buying_rate
            fss.cbn_buying_fss = rate if rate else 0.0

    @api.depends('date')
    def _compute_cbn_central(self):
        cbnrate = self.env['cbn.dollar.rate']
        for fss in self:
            rate = cbnrate.search([('rate_date', '=', fss.date)], limit=1).central_rate
            fss.cbn_central_fss = rate if rate else 0.0

    @api.depends('date')
    def compute_cbn_selling_average(self):
        cbnrate = self.env['cbn.dollar.rate']
        for fss in self:
            if not isinstance(fss.date, date):
                continue
            start_date = fss.date.replace(day=1)
            year = fss.date.year
            month = fss.date.month
            _, num_days = calendar.monthrange(year, month)
            # end_date = date(year, month, num_days)
            end_date = fss.date_average_compute
            rates = cbnrate.search([('rate_date', '>=', start_date), ('rate_date', '<=', end_date)]).mapped(
                'selling_rate')
            average_rate = sum(rates) / len(rates) if rates else 0.0
            fss.cbn_selling_average = average_rate
            fss.selling_average_computed = True

    @api.depends('date')
    def compute_cbn_buying_average(self):
        cbnrate = self.env['cbn.dollar.rate']
        for fss in self:
            if not isinstance(fss.date, date):
                continue
            start_date = fss.date.replace(day=1)
            year = fss.date.year
            month = fss.date.month
            _, num_days = calendar.monthrange(year, month)
            # end_date = date(year, month, num_days)
            end_date = fss.date_average_compute
            rates = cbnrate.search([('rate_date', '>=', start_date), ('rate_date', '<=', end_date)]).mapped(
                'buying_rate')
            average_rate = sum(rates) / len(rates) if rates else 0.0
            fss.cbn_buying_average = average_rate
            fss.buying_average_computed = True

    def action_import_genco_parameters(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Genco Parameters',
            'res_model': 'genco.parameter.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_cycle_id': self.id},
        }

    def action_import_disco_parameters(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import disco Parameters',
            'res_model': 'disco.parameter.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_cycle_id': self.id},
        }

    def action_submit(self):
        self.state='open'
        
    def action_approve(self):
        # self.state='invoice_verification'
        self.state='gen_inv'

    def action_verify_done(self):
        self.state='gen_bill'

    # def action_gen_inv(self):
    #     self.state='gen_inv'
        
    def action_reject(self):
        self.state='reject'
        
    def action_cancel(self):
        self.state='cancel'

    def _get_month_name(self):
        for rec in self:
            date_obj = rec.date_start
            if date_obj:
                month_number = date_obj.month

                month_names = [
                    'January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'
                ]

                month_name = month_names[month_number - 1]

                rec.month = month_name
            else:
                rec.month = False

    def _get_year(self):
        for rec in self:
            date_obj = rec.date_start
            if date_obj:
                year = str(date_obj.year)
                rec.year = year

            else:
                rec.year = False
        
    # state = fields.Selection([
    #     ('invoice_verification', 'Invoice Verification'),
    #     ('done', 'Verified'),
    # ], string='state', default="draft", help="A new record is in draft, once it is validated, it goes to open and then it is approved in Done state")
    
    @api.depends('date_start')
    def _compute_days_in_month(self):
        for rec in self:
            if rec.date_start:
                date = datetime.strptime(str(rec.date_start), DEFAULT_SERVER_DATE_FORMAT)
                rec.days_in_month = monthrange(date.year, date.month)[1]
            else:
                rec.days_in_month = 30
    
    def _compute_hours_in_month(self):
        for record in self:
            record.hours_in_month = record.days_in_month * 24

    def _circle_payments(self):
        pass

    def _circle_receipts(self):
        pass

    @api.model
    def create(self, vals):
        if vals.get('ref_sequence', 'New') == 'New':
            vals['ref_sequence'] = self.env['ir.sequence'].next_by_code(
                'billing_cycle') or '/'
        return super(BillingCycle, self).create(vals)

    @api.depends('month', 'year')
    def billing_cycle(self):
        for record in self:
            m = record.month
            y = record.year
            record['name'] = ("%s%s" % (m, y))

    bc_genco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.genco.invoice.billing_cycle.parameter", inverse_name="billing_cycle_id", string="Genco Parameters")

    bc_disco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.disco.invoice.billing_cycle.parameter", inverse_name="billing_cycle_id", string="Disco Parameters")

    nbet_genco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.nbet.genco.invoice.billing_cycle", inverse_name="billing_cycle_id", string="NBET Genco Parameters")

    # genco_invoice_ids = fields.Many2many(comodel_name='account.move', string='Genco Bills', copy=False, compute='_get_genco_bills')
    genco_invoice_ids = fields.Many2many(comodel_name='account.move', string='Genco Bills', copy=False)
    genco_invoices_count = fields.Integer(string='Bills Count', compute="_compute_bills_count")
    capacity_share_lines = fields.One2many(comodel_name='capacity.share.lines', inverse_name='billing_cycle_id',
                                           string='Capacity_share_lines', required=False)
    weighted_tariff_capacity = fields.Float(string='Weighted Capacity Tariff', compute="_compute_weighted_capacity")
    weighted_tariff_energy = fields.Float(string='Weighted Capacity Energy', compute="_compute_weighted_energy")

    # disco_invoice_ids = fields.Many2many(comodel_name='account.move', relation='account_move_disco_invoice_rel', string='Disco Invoices', copy=False, compute='_get_disco_invoices')

    disco_invoice_ids = fields.Many2many(
        comodel_name='account.move',
        relation='account_move_billing_cycle_disco_invoice_rel',
        column1='move_id',
        column2='billing_cycle_disco_invoice_move_id',
        string='Disco Invoices',
        copy=False)
    
    disco_invoices_count = fields.Integer(string='Invoices Count', compute="_compute_invoices_count")

    def _compute_bills_count(self):
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

    def _get_genco_bills(self):
        for rec in self:
            related_genco_invoicing = self.env["ebs_ocma.genco.invoice"].search([("billing_cycle_id", "=", rec.id)], limit=1)
            rec.genco_invoice_ids = related_genco_invoicing.genco_invoice_ids

    def _get_disco_invoices(self):
        for rec in self:
            related_disco_invoicing = self.env["ebs_ocma.disco.invoice"].search([("billing_cycle_id", "=", rec.id)], limit=1)
            rec.disco_invoice_ids = related_disco_invoicing.disco_invoice_ids

    def _compute_invoices_count(self):
        self.disco_invoices_count = len(self.disco_invoice_ids)

    def action_view_disco_invoices(self):
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        if self.disco_invoices_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.disco_invoice_ids.ids) + ")]"
        elif self.disco_invoices_count == 1:
            res = self.env.ref('account.invoice_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.disco_invoice_ids.id
        return result

    def _compute_weighted_capacity(self):
        for rec in self:
            try:
                total_capacity_payments = sum(line.capacity_payment for line in rec.bc_genco_parameter_ids)
                total_capacity = sum(line.capacity for line in rec.bc_genco_parameter_ids)
                rec.weighted_tariff_capacity = total_capacity_payments / (total_capacity * rec.hours_in_month)
            except ZeroDivisionError:
                rec.weighted_tariff_capacity = 0.00

    def _compute_weighted_energy(self):
        for rec in self:
            try:
                total_energy_payments = sum(line.energy_payment for line in rec.bc_genco_parameter_ids)
                total_energy_sentout = sum(line.energy_sent_out_mwh for line in rec.bc_genco_parameter_ids)
                rec.weighted_tariff_energy = total_energy_payments / total_energy_sentout
            except ZeroDivisionError:
                rec.weighted_tariff_energy = 0.00

    def _get_genco_parameters(self):
        for rec in self:
            related_genco_invoicing = self.env["ebs_ocma.genco.invoice"].search([("billing_cycle_id", "=", rec.id)], limit=1)
            rec.bc_genco_parameter_ids = related_genco_invoicing.mapped('genco_parameter_ids')

    def _get_disco_parameters(self):
        for rec in self:
            related_disco_invoicing = self.env["ebs_ocma.disco.invoice"].search([("billing_cycle_id", "=", rec.id)], limit=1)
            rec.bc_disco_parameter_ids = related_disco_invoicing.mapped('disco_parameter_ids')

    disco_total_capacity_delivered = fields.Float(string='Disco Total Capacity Delivered', compute='_compute_total_capacity_delivered')
    disco_total_energy_delivered = fields.Float(string='Disco Total Energy Delivered', compute='_compute_total_energy_delivered')
    disco_share_capacity_delivered = fields.Float(string='Disco share of Capacity Delivered',
                                                  compute='_compute_share_capacity_delivered')
    disco_share_energy_delivered = fields.Float(string='Disco share of Energy Delivered',
                                                compute='_compute_share_energy_delivered')
    disco_percent_share_capacity = fields.Float(string='Disco % share of Total Capacity sent Out',
                                                compute='_compute_percent_total_capacity')
    disco_percent_share_energy = fields.Float(string='Disco % share of Total Energy sent Out',
                                              compute='_compute_percent_total_energy')

    genco_total_capacity = fields.Float(string='Genco Total Capacity', compute='_compute_total_capacity')
    genco_total_energy_sent_out = fields.Float(string='Genco Total Energy Sent Out', compute='_compute_total_energy_sent_out')
    genco_total_capacity_import = fields.Float(string='Genco Total Capacity Import', compute='_compute_total_capacity_import')
    genco_total_energy_import = fields.Float(string='Genco Total Energy Import', compute='_compute_total_energy_import')

    def _compute_total_capacity_delivered(self):
        for rec in self:
            if rec.bc_disco_parameter_ids:
                for line in rec.bc_disco_parameter_ids:
                    rec.disco_total_capacity_delivered += line.capacity_delivered
            else:
                rec.disco_total_capacity_delivered = 0

    @api.depends('bc_disco_parameter_ids', 'bc_disco_parameter_ids.capacity_delivered',
                 'bc_disco_parameter_ids.partner_id.is_disco')
    @api.onchange('bc_disco_parameter_ids.capacity_delivered')
    # def _compute_share_capacity_delivered(self):
    #     for rec in self:
    #         if rec.bc_disco_parameter_ids:
    #             disco_capacity = 0
    #             for line in rec.bc_disco_parameter_ids:
    #                 if line.partner_id.is_disco:
    #                     disco_capacity += line.capacity_delivered
    #                 rec.disco_share_capacity_delivered = disco_capacity
    #
    #         else:
    #             rec.disco_share_capacity_delivered = 0
    def _compute_share_capacity_delivered(self):
        groups = self.bc_disco_parameter_ids.filtered(lambda r: r.partner_id.is_disco)
        if groups:
            for line in groups:
                self.disco_share_capacity_delivered += line.capacity_delivered

        else:
            self.disco_share_capacity_delivered = 0

    def _compute_total_energy_delivered(self):
        for rec in self:
            if rec.bc_disco_parameter_ids:
                for line in rec.bc_disco_parameter_ids:
                    rec.disco_total_energy_delivered += line.energy_delivered
            else:
                rec.disco_total_energy_delivered = 0

    @api.depends('disco_share_capacity_delivered', 'disco_total_capacity_delivered')
    def _compute_percent_total_capacity(self):
        for rec in self:
            try:
                percentage = rec.disco_share_capacity_delivered / rec.disco_total_capacity_delivered * 100
                rec.disco_percent_share_capacity = round(percentage, 2)
            except ZeroDivisionError:
                rec.disco_percent_share_capacity = 0.00

    @api.depends('disco_share_energy_delivered', 'disco_total_energy_delivered')
    def _compute_percent_total_energy(self):
        for rec in self:
            try:
                percentage = rec.disco_share_energy_delivered / rec.disco_total_energy_delivered * 100
                rec.disco_percent_share_energy = round(percentage, 2)
            except ZeroDivisionError:
                rec.disco_percent_share_energy = 0.00

    @api.depends('bc_disco_parameter_ids', 'bc_disco_parameter_ids.energy_delivered',
                 'bc_disco_parameter_ids.partner_id.is_disco')
    @api.onchange('bc_disco_parameter_ids.energy_delivered')
    def _compute_share_energy_delivered(self):
        groups = self.bc_disco_parameter_ids.filtered(lambda r: r.partner_id.is_disco)
        if groups:
            for line in groups:
                self.disco_share_energy_delivered += line.energy_delivered

        else:
            self.disco_share_energy_delivered = 0

    def _compute_total_capacity(self):
        for rec in self:
            if rec.bc_genco_parameter_ids:
                for line in rec.bc_genco_parameter_ids:
                    rec.genco_total_capacity += line.capacity
            else:
                rec.genco_total_capacity = 0

    def _compute_total_energy_sent_out(self):
        for rec in self:
            if rec.bc_genco_parameter_ids:
                for line in rec.bc_genco_parameter_ids:
                    rec.genco_total_energy_sent_out += line.energy_sent_out_mwh
            else:
                rec.genco_total_energy_sent_out = 0
    
    def _compute_total_capacity_import(self):
        for rec in self:
            if rec.bc_genco_parameter_ids:
                for line in rec.bc_genco_parameter_ids:
                    rec.genco_total_capacity_import += line.capacity_import
            else:
                rec.genco_total_capacity_import = 0
    
    def _compute_total_energy_import(self):
        for rec in self:
            if rec.bc_genco_parameter_ids:
                for line in rec.bc_genco_parameter_ids:
                    rec.genco_total_energy_import += line.energy_import
            else:
                rec.genco_total_energy_import = 0

    disco_capacity_delivered = fields.Float(string='capacity delivered', compute='_compute_disco_capacity_delivered')
    disco_energy_delivered = fields.Float(string='disco energy delivered', compute='_compute_disco_energy_delivered')

    def _compute_disco_capacity_delivered(self):
        for rec in self:
            disco_capacity_delivered = 0
            for line in rec.bc_disco_parameter_ids:
                if line.partner_id.is_genco:
                    disco_capacity_delivered += line.capacity_delivered
            rec.disco_capacity_delivered = rec.disco_total_capacity_delivered + rec.genco_total_capacity_import - (disco_capacity_delivered)
    
    def _compute_disco_energy_delivered(self):
        for rec in self:
            disco_energy_delivered = 0
            for line in rec.bc_disco_parameter_ids:
                if line.partner_id.is_genco:
                    disco_energy_delivered += line.energy_delivered
            rec.disco_energy_delivered = rec.disco_total_energy_delivered + rec.genco_total_energy_import - (disco_energy_delivered)

    energy_diff = fields.Float(string='Energy Difference', compute='_compute_energy_delivered_diff')
    capacity_diff = fields.Float(string='Capacity Difference', compute='_compute_capacity_delivered_diff')

    total_invoiced_energy = fields.Float(string='invoiced energy', compute='_genco_invoiced_energy')

    def _genco_invoiced_energy(self):
        for rec in self:
            for line in rec.bc_genco_parameter_ids:
                rec.invoiced_energy += line.invoiced_energy

    def _compute_energy_delivered_diff(self):
        for rec in self:
            rec.energy_diff = 1.52
            # rec.energy_diff = rec.disco_total_energy_delivered - rec.genco_total_energy_sent_out
    
    def _compute_capacity_delivered_diff(self):
        for rec in self:
            rec.capacity_diff = 0.37
            # rec.capacity_diff = rec.disco_total_capacity_delivered - rec.genco_total_capacity

    weighted_cost_power = fields.Float('Weighted Cost of Power (Capacity)', compute='_compute_weighted_cost_power')
    weighted_avg_cost_power = fields.Float('Weighted Average Cost of Power (Capacity) ', compute='_compute_weighted_avg_cost_power')

    # total_capacity = fields.Float(string='Total Capacity', compute='_compute_total_capacity')
    total_energy_sent_out_mwh = fields.Float(string='Total Energy Sent Out(MWh)', compute='_compute_total_energy_sent_out_mwh')

    def _compute_weighted_cost_power(self):
        for rec in self:
            for line in rec.bc_genco_parameter_ids:
                rec.weighted_cost_power += (line.capacity_payment / line.capacity) if line.capacity != 0 else 0
                
    def _compute_weighted_avg_cost_power(self):
        for rec in self:
            for line in rec.bc_genco_parameter_ids:
                rec.weighted_avg_cost_power += line.energy_payment / line.energy_sent_out_mwh if line.energy_sent_out_mwh != 0 else 0

    # def _compute_total_capacity(self):
    #     for rec in self:
    #         for line in rec.bc_genco_parameter_ids:
    #             rec.total_capacity += line.capacity
    
    def _compute_total_energy_sent_out_mwh(self):
        for rec in self:
            for line in rec.bc_genco_parameter_ids:
                rec.total_energy_sent_out_mwh += line.energy_sent_out_mwh

    def _create_genco_bill(self, partner_id, ref, origin, invoice_value):
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
                'billing_circle_id': self.id,
                
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
            for line in rec.bc_genco_parameter_ids:
                if line.verified:
                    rec._create_genco_bill(partner_id=line.partner_id, ref=line.name, invoice_value=line.total_payment, origin=self.ref_no)
            for line in rec.nbet_genco_parameter_ids:
                if line.verified:
                    rec._create_genco_bill(partner_id=line.partner_id, ref=line.name, invoice_value=line.total_payment, origin=self.ref_no)

    def action_verify(self):
        for rec in self:
            rec.generate_genco_invoice()
            # rec.write({'state': 'gen_inv'})
            for invoice in rec.genco_invoice_ids:
                if invoice.amount_total > 0 :
                    # invoice.action_invoice_open()
                    invoice.action_post()

    def _create_disco_invoice(self, partner_id, ref, origin, invoice_value):
        self.ensure_one()
        company_id = self.env.user.company_id.id
        # journal_id = (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id).default_get(['journal_id'])['journal_id'])
        journal_id = self.env.ref('ebs_ocma.disco_invoice_journal').id or (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id).default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('Please define an accounting journal.'))

        for rec in self:
            invoice_vals = {
                'ref': rec.name or '',
                'move_type': 'out_invoice',
                'partner_id': partner_id.id,
                'invoice_date': rec.date,

                'invoice_origin': origin,
                # 'account_id': partner_id.property_account_receivable_id.id,

                'journal_id': journal_id,
                'company_id': company_id,
                'billing_circle_id': self.id,

                # 'user_id': self.user_id and self.user_id.id,
                # 'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
                # 'payment_term_id': self.payment_term_id.id,
                # 'currency_id': self.pricelist_id.currency_id.id,
                
                'invoice_line_ids': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'ENERGY CHARGE',
                })
                ,(0, 0, {
                    'name': 'Total Disco Share of Energy Received (MWh)',
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': invoice_value,
                })
                ,(0, 0, {
                    'name': 'Total Energy Received by %s Disco (MWh)' % partner_id.name,
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': 0,
                })
                ,(0, 0, {
                    'name': 'percentage of Total Energy Received by %s Disco' % partner_id.name,
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': 0,
                })
                , (0, 0, {
                        'display_type': 'line_section',
                        'name': 'CAPACITY CHARGE',
                    })
                ,(0, 0, {
                    'name': 'Total Disco Share of Capacity (MW)',
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': 0,
                })
                ,(0, 0, {
                    'name': '%s Disco Share of Capacity (MW)' % partner_id.name,
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': 0,
                })
                , (0, 0, {
                        'display_type': 'line_section', 
                        'name': 'SUPPLEMENTARY COSTS',
                    })
                , (0, 0, {
                    'name': 'Total Start Up Costs',
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': 0,
                })
                , (0, 0, {
                        'display_type': 'line_section',
                        'name': 'PREVIOUS BALANCE CARRIED FORWARD',
                })
                ,(0, 0, {
                    'name': ref,
                    'quantity': 1, 
                    'account_id': 17, # account to be set
                    'price_unit': 0,
                })],
            }
            disco_invoice_id = self.env['account.move'].create(invoice_vals)
            disco_invoice_id.action_post()
            self.disco_invoice_ids += disco_invoice_id
    
    def generate_disco_invoice(self):
        for rec in self:
            for line in rec.bc_disco_parameter_ids:
                DiscoinvoicingOBJ = self.env['ebs_ocma.disco.invoicing'].sudo()
                new_disco_invoicing = DiscoinvoicingOBJ.create(
                    {
                        'billing_cycle_id': self.id,
                        'month': rec.month,
                        'date': date.today(),
                        'partner_id': line.partner_id.id,
                    }
                )
                # rec.disco_invoicing_ids += new_disco_invoicing
                # rec._create_journal_entries(partner=line.partner_id)
                rec._create_disco_invoice(partner_id=line.partner_id, ref=line.name, invoice_value=line.invoice_value, origin=self.ref_no)
            # rec.write({'state': 'invoice_verification'})
            rec.write({'state': 'mro_application'})
            
    

class GencoVerify(models.Model):
    _name = 'genco.verify'
    _description = 'GencoVerify'

    name = fields.Char()
    genco_id = fields.Many2one(
        comodel_name='res.partner',
        string='Genco',
        required=False)
    capacity_payment = fields.Float(
        string='Capacity Payments',
        required=False)
    energy_payment = fields.Float(
        string='Energy payments',
        required=False)
    startup_payment = fields.Float(
        string='Startup Payments',
        required=False)
    interest_payment = fields.Float(
        string='Interest Payments',
        required=False)
    total_payment = fields.Float(
        string='Total Payments',
        required=False)
    nbet_computed = fields.Float(
        string='Nbet computed figures',
        required=False)
    date_received = fields.Date(
        string='Date received',
        required=False)
    due_date = fields.Date(
        string='Due date',
        required=False)
    cus_invoice_ref = fields.Char(
        string='Customer invoice ref',
        required=False)
    billing_cycle_id = fields.Many2one(
        comodel_name='billing.cycle',
        string='Billing Cycle',
        required=False)


class GencoVerifyDollars(models.Model):
    _name = 'genco.verify_dollars'
    _description = 'GencoVerify'

    name = fields.Char()
    genco_id = fields.Many2one(
        comodel_name='res.partner', domain=[('is_genco', '=', True)],
        string='GENCO',
        required=False)
    capacity_payment = fields.Float(
        string='Capacity Payment',
        required=False)
    energy_payment = fields.Float(
        string='Energy Payment',
        required=False)
    startup_payment = fields.Float(
        string='Startup Payment',
        required=False)
    interest_payment = fields.Float(
        string='Interest Payment',
        required=False)
    total_payment = fields.Float(
        string='Total Payment',
        required=False)
    nbet_computed = fields.Float(
        string='Nbet Computed',
        required=False)
    date_received = fields.Date(
        string='Date Received',
        required=False)
    due_date = fields.Date(
        string='Due Date',
        required=False)
    cus_invoice_ref = fields.Char(
        string='Customer Invoice Reference',
        required=False)
    billing_cycle_id = fields.Many2one(
        comodel_name='billing.cycle',
        string='Billing Cycle',
        required=False)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    billing_circle_id = fields.Many2one(comodel_name='billing.cycle', string='Billing Cycle')

    def action_invoice_open(self):
        result = super(AccountInvoice, self).action_invoice_open()
        self._check_billing_cycle()
        return result

    def _check_billing_cycle(self):
        for rec in self:
            for line in rec.billing_circle_id.bc_genco_parameter_ids:
                if line.invoice_id.state in ['draft','open','approved']:
                    raise UserError(_("Invoice is to be verified"))
                elif line.invoice_id.state == "invoice_verification":
                    raise UserError(_("Invoice is currently being verified"))


class GencoBCParaemeter(models.Model):
    _name = 'ebs_ocma.genco.invoice.billing_cycle.parameter'
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

    capacity = fields.Float('capacity(MWh)', compute='_compute_capacity')
    energy_sent_out_mwh = fields.Float(string='Energy Sent Out (MWh)', compute='_compute_energy_sent_out_mwh')
    capacity_payment = fields.Float('Capacity Payment', compute='_compute_capacity_payment')
    energy_payment = fields.Float('Energy Payment', compute='_compute_energy_payment')
    total_payment = fields.Float('Total Payment', compute='_compute_total_payment')
    myto_capacity_tariff = fields.Float(
        string='PPA capacity tariff',
        required=False, compute='_compute_capacity_tariff')
    myto_energy_tariff = fields.Float(
        string='PPA Energy tariff',
        required=False, compute='_compute_energy_tariff')

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle")

    verified = fields.Boolean(string='verified invoice')

    def _compute_capacity_tariff(self):
        for rec in self:
            billingcycle = rec.billing_cycle_id.id
            mytorate = rec.partner_id.myto_rate.id
            rates = self.env['hydro.rates'].search([('rate_id', '=', mytorate), ('billing_circle', '=', billingcycle)],)
            rec.myto_capacity_tariff = rates.capacity_charge

    def _compute_energy_tariff(self):
        for rec in self:
            billingcycle = rec.billing_cycle_id.id
            mytorate = rec.partner_id.myto_rate.id
            rates = self.env['hydro.rates'].search([('rate_id', '=', mytorate), ('billing_circle', '=', billingcycle)],)
            rec.myto_energy_tariff = rates.energy_charge_tlf

        pass

    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name

    def _compute_invoice_capacity(self):
        for rec in self:
            rec.invoiced_capacity = rec.capacity_sent_out_mw - rec.capacity_import

    def _compute_invoiced_energy(self):
        for rec in self:
            if rec.billing_cycle_id.tlf_applied:
                rec.invoiced_energy = rec.energy_sent_out_kwh - rec.energy_import
            else:
                rec.invoiced_energy = ((100 - rec.billing_cycle_id.transmission_loss_factor)/100 * rec.energy_sent_out_kwh) - rec.energy_import
    
    def _compute_capacity(self):
        for rec in self:
            try:
                # rec.capacity = rec.capacity_sent_out_mw / rec.invoice_id.billing_cycle_id.hours_in_month
                rec.capacity = rec.invoiced_capacity / rec.billing_cycle_id.hours_in_month
            except ZeroDivisionError:
                rec.capacity = 0.00

    def _compute_energy_sent_out_mwh(self):
        for rec in self:
            # rec.energy_sent_out_mwh = rec.energy_sent_out_kwh / 1000
            if rec.invoiced_energy > 0:
                rec.energy_sent_out_mwh = rec.invoiced_energy / 1000
            else:
                rec.energy_sent_out_mwh = 0

    @api.onchange('billing_cycle_id.hours_in_month')
    def _compute_capacity_payment(self):
        for rec in self:
            if rec.capacity > 0:
                rec.capacity_payment = rec.capacity * rec.billing_cycle_id.hours_in_month * rec.myto_capacity_tariff
            elif rec.capacity <= 0:
                rec.capacity_payment = 0
    
    def _compute_energy_payment(self):
        for rec in self:
            rec.energy_payment = rec.energy_sent_out_mwh * rec.myto_energy_tariff
            # rec.energy_payment = rec.invoiced_energy * rec.partner_id.rate_gas_price

    def _compute_total_payment(self):
        for rec in self:
            rec.total_payment = rec.capacity_payment + rec.energy_payment
            try:
                rec.capacity = rec.capacity_sent_out_mw / rec.billing_cycle_id.hours_in_month
            except ZeroDivisionError:
                rec.capacity = 0.0

class NBETGencoBCParaemeter(models.Model):
    _name = 'ebs_ocma.nbet.genco.invoice.billing_cycle'
    _description = 'NBET Genco Parameters'
    
    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')
    capacity_payment = fields.Float('Capacity Payment')
    energy_payment = fields.Float('Energy Payment')
    total_payment = fields.Float('Total Payment')
    gas_element = fields.Float('Gas Invoice and Transport')
    percent_gas = fields.Float('% Gas INV to Genco INV')
    genco_portion_market = fields.Float('Genco Portion of Market Payment')
    percent_payment = fields.Float('% Payment')
    genco_shortfall = fields.Float('Genco Tariff Shortfall')
    percent_ts_payment = fields.Float('% TS Payment')
    total_payment_genco = fields.Float('Total Payment to Genco')
    market_percent_payment = fields.Float('Market % Payment')

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle")

    verified = fields.Boolean(string='verified invoice')

class BCDiscoParaemeter(models.Model):
    _name = 'ebs_ocma.disco.invoice.billing_cycle.parameter'
    _description = 'Disco Parameters'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco')
    name = fields.Char(string="Name")
    capacity_delivered = fields.Float(string='Capacity Delivered', required=False)
    energy_delivered = fields.Float(string='Energy Delivered', required=False)

    capacity_shared = fields.Float(string='Capacity Shared (Mw/Month)')
    energy_shared = fields.Float(string='Energy Shared (kWh)')
    genco_parameters_ids = fields.Many2many(
        comodel_name='ebs_ocma.genco.invoice.billing_cycle.parameter',
        relation='billing_circle_genco_capacity_share_rel',
        string='Genco_parameters_ids', compute='_compute_genco_list')

    percentage_total = fields.Float(string='Percentage of total energy', required=False, compute='_compute_percentage_total')
    percentage_disco = fields.Float(string='Percentage of disco share energy', required=False, compute='_compute_percentage_disco')
    percentage_disco_cap = fields.Float(string='Percentage of disco share capacity', required=False,
                                        compute='_compute_percentage_disco_cap')
    portion_capacity = fields.Float(string='Portion Capacity', required=False, compute='_compute_portion_capacity')
    portion_energy = fields.Float(string='Portion Energy', required=False, compute='_compute_portion_energy')

    percent_shared = fields.Float(string='% Shared', compute='_compute_percent_shared')
    
    invoice_value = fields.Float(string='Invoice Value', required=False, compute='_compute_invoice_value')
    capacity_charge = fields.Float(string='Capacity Charge', required=False, compute='_compute_capacity_charge', store=True)
    energy_charge = fields.Float(string='Energy Charge', required=False, )
    disco = fields.Boolean(string='Disco', required=False, compute='_is_disco')
    capacity_charge_compute = fields.Boolean(string='Capacity charge computed',)

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle")
    capacity_share_lines = fields.One2many(comodel_name='capacity.share.lines', inverse_name='disco_parameter_id',
                                           string='Capacity_share_lines', required=False)
    weighted_tariff = fields.Boolean(string='Weighted tariff', required=False)
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name

    def _is_disco(self):
        for rec in self:
            if rec.partner_id.is_disco:
                rec.disco = True
            else:
                rec.disco = False

    @api.depends('billing_cycle_id', 'genco_parameters_ids')
    def _compute_genco_list(self):
        for record in self:
            if record.billing_cycle_id:
                genco_parameters_ids = self.env['ebs_ocma.genco.invoice.billing_cycle.parameter'].search([('billing_cycle_id', '=', record.billing_cycle_id.id)])
                record.genco_parameters_ids = [(6, 0, genco_parameters_ids.ids)]
            else:
                record.genco_ids = [(5, 0, 0)]

    @api.depends('billing_cycle_id.disco_percent_share_capacity', 'genco_parameters_ids',
                 'billing_cycle_id.disco_percent_share_energy')
    def _compute_capacity_charge(self):
        for disco_param in self:
            if disco_param.capacity_charge_compute:
                # disco_parameters = disco_param.id
                disco_param.write({'capacity_charge_compute': False})
                disco_param.write({'capacity_share_lines': [(5, 0, 0)]})
                if disco_param.partner_id.is_disco:
                    share_lines = [(0, 0, {'share_of_capacity': ((disco_param.billing_cycle_id.disco_percent_share_capacity / 100) * genco_param.capacity) * (disco_param.percentage_disco_cap / 100),
                                           'capacity_price': genco_param.myto_capacity_tariff, 'billing_cycle_id': disco_param.billing_cycle_id.id,
                                           'share_of_energy': ((disco_param.billing_cycle_id.disco_percent_share_energy / 100)  * genco_param.energy_sent_out_mwh) * (disco_param.percentage_disco / 100),
                                           'energy_price': genco_param.myto_energy_tariff, 'genco_name': genco_param.partner_id.name})
                                   for genco_param in disco_param.genco_parameters_ids]
                    disco_param.capacity_share_lines = share_lines
                    disco_param.capacity_charge = sum(line.capacity_charge for line in disco_param.capacity_share_lines)
                    disco_param.energy_charge = sum(line.energy_charge for line in disco_param.capacity_share_lines)
                    disco_param.write({'capacity_charge_compute': True})
                elif disco_param.partner_id.is_genco:
                    average_monthly_capacity = disco_param.capacity_delivered / disco_param.billing_cycle_id.hours_in_month
                    if disco_param.weighted_tariff:
                        rate_capacity = disco_param.billing_cycle_id.weighted_tariff_capacity
                        rate_energy = disco_param.billing_cycle_id.weighted_tariff_energy
                        share_lines = [(0, 0, {'share_of_capacity': ((disco_param.billing_cycle_id.disco_percent_share_capacity / 100) * genco_param.capacity) * (disco_param.percentage_disco_cap / 100),
                                               'capacity_price': genco_param.myto_capacity_tariff,
                                               'billing_cycle_id': disco_param.billing_cycle_id.id,
                                               'share_of_energy': ((disco_param.billing_cycle_id.disco_percent_share_energy / 100) * genco_param.energy_sent_out_mwh) * (disco_param.percentage_disco / 100),
                                               'energy_price': genco_param.myto_energy_tariff,
                                               'genco_name': genco_param.partner_id.name})
                                       for genco_param in disco_param.genco_parameters_ids]
                        disco_param.capacity_share_lines = share_lines
                        disco_param.capacity_charge = average_monthly_capacity * rate_capacity
                        disco_param.energy_charge = disco_param.energy_delivered * rate_energy/1000

                        disco_param.write({'capacity_charge_compute': True})
                    else:
                        rate_capacity = disco_param.partner_id.rate
                        rate_energy = disco_param.partner_id.rate_gas_price
                        share_lines = [(0, 0, {'share_of_capacity': ((disco_param.billing_cycle_id.disco_percent_share_capacity / 100) * genco_param.capacity) * (disco_param.percentage_disco_cap / 100),
                                               'capacity_price': genco_param.myto_capacity_tariff,
                                               'billing_cycle_id': disco_param.billing_cycle_id.id,
                                               'share_of_energy': ((disco_param.billing_cycle_id.disco_percent_share_energy / 100) * genco_param.energy_sent_out_mwh) * (disco_param.percentage_disco / 100),
                                               'energy_price': genco_param.myto_energy_tariff,
                                               'genco_name': genco_param.partner_id.name})
                                       for genco_param in disco_param.genco_parameters_ids]
                        disco_param.capacity_share_lines = share_lines
                        disco_param.capacity_charge = average_monthly_capacity * rate_capacity
                        disco_param.energy_charge = disco_param.energy_delivered * rate_energy/1000

                        disco_param.write({'capacity_charge_compute': True})
            else:
                share_lines = [(0, 0, {'share_of_capacity': ((disco_param.billing_cycle_id.disco_percent_share_capacity / 100) * genco_param.capacity) * (disco_param.percentage_disco_cap / 100),
                                       'capacity_price': genco_param.myto_capacity_tariff,
                                       'billing_cycle_id': disco_param.billing_cycle_id.id, 'share_of_energy': ((disco_param.billing_cycle_id.disco_percent_share_energy / 100)  * genco_param.energy_sent_out_mwh) * (disco_param.percentage_disco / 100),
                                       'energy_price': genco_param.myto_energy_tariff,})
                               for genco_param in disco_param.genco_parameters_ids]
                disco_param.capacity_share_lines = share_lines
                disco_param.capacity_charge = sum(line.capacity_charge for line in disco_param.capacity_share_lines)
                disco_param.energy_charge = sum(line.energy_charge for line in disco_param.capacity_share_lines)
                # disco_parameters = disco_param.id
                disco_param.write({'capacity_charge_compute': True})

    @api.depends('capacity_charge', 'energy_charge')
    def _compute_invoice_value(self):
        for rec in self:
            rec.invoice_value = rec.capacity_charge + rec.energy_charge

    def _compute_percentage_total(self):
        for rec in self:
            rec.percentage_total = (rec.energy_delivered / rec.billing_cycle_id.disco_total_energy_delivered
                                    if rec.billing_cycle_id.disco_total_energy_delivered != 0 else 0) * 100

    def _compute_percentage_disco(self):
        for rec in self:
            rec.percentage_disco = (rec.energy_delivered / rec.billing_cycle_id.disco_share_energy_delivered
                                    if rec.billing_cycle_id.disco_share_energy_delivered != 0 else 0) * 100

    def _compute_percentage_disco_cap(self):
        for rec in self:
            rec.percentage_disco_cap = (rec.capacity_delivered / rec.billing_cycle_id.disco_share_capacity_delivered
                                        if rec.billing_cycle_id.disco_share_capacity_delivered != 0 else 0) * 100

    def _compute_portion_capacity(self):
        for rec in self:
            rec.portion_capacity = (rec.percentage_total / 100) * rec.billing_cycle_id.genco_total_capacity
    
    def _compute_portion_energy(self):
        for rec in self:
            rec.portion_energy = (rec.percentage_total / 100) * rec.billing_cycle_id.genco_total_energy_sent_out

    def _compute_percent_shared(self):
        for rec in self:
            rec.percent_shared = rec.energy_shared / rec.total_energy_shared if rec.total_energy_shared != 0 else 0


class CapacityShareLines(models.Model):
    _name = 'capacity.share.lines'
    _description = 'Disco Capacity Share lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    billing_cycle_id = fields.Many2one(comodel_name='billing.cycle', string="Billing Cycle")
    disco_parameter_id = fields.Many2one(comodel_name='ebs_ocma.disco.invoice.billing_cycle.parameter',
                                         string="Disco Parameter")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco')
    genco_name = fields.Char(string='Genco', required=False)
    share_of_capacity = fields.Float('Share of capacity(MW/Hr)')
    share_of_capacity_month = fields.Float('Share of capacity(MW/Month)', compute='_compute_capacity_month')
    capacity_price = fields.Float(string='capacity price', required=False,)
    capacity_charge = fields.Float(string='Capacity Charge', compute='_capacity_charge')
    share_of_energy = fields.Float('Share of Energy Charged(MWh)')
    energy_price = fields.Float(string='Energy Price', required=False, )
    energy_charge = fields.Float(string='Energy Charge', compute='_energy_charge')

    @api.depends('share_of_capacity', 'capacity_price', 'billing_cycle_id.hours_in_month')
    def _capacity_charge(self):
        for rec in self:
            rec.capacity_charge = rec.share_of_capacity * rec.capacity_price * rec.billing_cycle_id.hours_in_month

    def _energy_charge(self):
        for rec in self:
            rec.energy_charge = rec.share_of_energy * rec.energy_price

    @api.depends('share_of_capacity', 'capacity_price', 'billing_cycle_id.hours_in_month')
    def _compute_capacity_month(self):
        for rec in self:
            rec.share_of_capacity_month = rec.share_of_capacity * rec.billing_cycle_id.hours_in_month
