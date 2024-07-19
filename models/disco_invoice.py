from odoo import models, fields, api, _
from datetime import date
from odoo.addons.ebs_ocma.models.billing_cycle import MONTHS, YEARS
from odoo.exceptions import UserError


class DiscoInvoice(models.Model):

    _name = 'ebs_ocma.disco.invoice'
    _description = 'Disco Invoice'
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
    disco_parameter_ids = fields.One2many(
        comodel_name="ebs_ocma.disco.invoice.parameter", inverse_name="invoice_id", string="Disco Parameters")
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Validate'),
        ('approve', 'Done'),
    ], string='state', default="draft", help="A new record is in draft, once it is validated, it goes to open and then it is approved in Done state")
    
    cbn_average = fields.Float(string='CBN Average', related='billing_cycle_id.cbn_average')
    nbet_dist_rate = fields.Float(string='Nbet Dist Rate', related='billing_cycle_id.nbet_dist_rate')
    nbet_dist_azura = fields.Float(string='Nbet Dist Azura', related='billing_cycle_id.nbet_dist_azura')
    agip_quaterly_index = fields.Float(string="Agip Quaterly Index", related='billing_cycle_id.agip_quaterly_index')
    azura_fx_date = fields.Date(string="Azura FX Date", related='billing_cycle_id.azura_fx_date')
    azura_fx_value = fields.Float(string="Azura FX Value", related='billing_cycle_id.azura_fx_value')

    total_energy_delivered = fields.Float(string="Total Energy Delivered", compute='_compute_total_energy_delivered')
    total_energy_shared = fields.Float(string="Total Energy Shared", compute='_compute_total_energy_shared')

    disco_invoicing_ids = fields.Many2many(comodel_name="ebs_ocma.disco.invoicing", string="Disco Invoices Config",)
    
    disco_invoicing_count = fields.Integer(
        string='Invoices Config Count', compute="_compute_disco_invoicing_count")

    # move_ids = fields.Many2many(comodel_name='account.move', string='Journal Entries', copy=False)

    move_ids = fields.Many2many(
        comodel_name='account.move',
        relation='account_moves_disco_invoice_rel',
        column1='journal_id',
        column2='disco_invoice_move_id',
        string='Journal Entries')

    moves_count = fields.Integer(
        string='Moves Count', compute="_compute_moves_count")

    disco_invoice_ids = fields.Many2many(comodel_name='account.move', string='Disco Invoices', copy=False)
    disco_invoices_count = fields.Integer(string='Invoices Count', compute="_compute_invoices_count")

    # @api.model
    # def create(self, vals):
    #     res = super(DiscoInvoice, self).create(vals)
    #     res._create_disco_invoice_parameter()
    #     return res

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

    def _create_disco_invoice_parameter(self):
        DiscocoParameter = self.env['ebs_ocma.disco.invoice.parameter'].sudo()
        disco_parameter_ids = self.disco_parameter_ids
        discos = self.env['res.partner'].sudo().search([('is_disco', '=', True)])
        for disco in discos:
            new_disco_parameter = DiscocoParameter.create(
                {
                    'name': disco.name,
                    'partner_id': disco.id,
                    'invoice_id': self.id,
                }
            )
            disco_parameter_ids += new_disco_parameter

    def _compute_moves_count(self):
        self.moves_count = len(self.move_ids)

    def action_view_account_moves(self):
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        if self.moves_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.move_ids.ids) + ")]"
        elif self.moves_count == 1:
            res = self.env.ref('account.view_move_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.move_ids.id
        return result

    def _compute_disco_invoicing_count(self):
        self.disco_invoicing_count = len(self.disco_invoicing_ids)


    def action_confirm(self):
        self.write({
            'state': 'open'
        })
        
    def action_approve(self):
        self.write({
            'state': 'approve'
        })
        
    @api.onchange('billing_cycle_id')
    def _onchange_billing_cycle_id(self):
        DiscoParameter = self.env['ebs_ocma.disco.invoice.parameter'].sudo()
        disco_parameter_ids = self.disco_parameter_ids
        discos = self.env['res.partner'].sudo().search([('is_disco', '=', True)])
        self.month = self.billing_cycle_id and self.billing_cycle_id.month
        self.year = self.billing_cycle_id and self.billing_cycle_id.year
        # for disco in discos:
        #     # if not disco_parameter_ids:
        #     new_disco_parameter = DiscoParameter.create(
        #         {
        #             'name': disco.name,
        #             'partner_id': disco.id,
        #             'invoice_id': self._origin.id,
        #         }
        #     )
        #     disco_parameter_ids += new_disco_parameter

    def generate_disco_invoice(self):
        for rec in self:
            for line in rec.disco_parameter_ids:
                DiscoinvoicingOBJ = self.env['ebs_ocma.disco.invoicing'].sudo()
                new_disco_invoicing = DiscoinvoicingOBJ.create(
                    {
                        'billing_cycle_id': rec.billing_cycle_id.id,
                        'month': rec.month,
                        'date': date.today(),
                        'partner_id': line.partner_id.id,
                    }
                )
                rec.disco_invoicing_ids += new_disco_invoicing
                # rec._create_journal_entries(partner=line.partner_id)
                rec._create_invoice(partner_id=line.partner_id, ref=line.name, invoice_value=line.invoice_value, origin=self.ref_no)
    
    def action_view_disco_invoicing(self):
        action = self.env.ref('ebs_ocma.disco_invoicing_action')
        result = action.read()[0]
        if self.disco_invoicing_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.disco_invoicing_ids.ids) + ")]"
        elif self.disco_invoicing_count == 1:
            res = self.env.ref('ebs_ocma.ebs_ocma_disco_invoicing_view_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.disco_invoicing_ids.id
        return result

    def _compute_total_energy_delivered(self):
        for rec in self:
            for line in rec.disco_parameter_ids:
                rec.total_energy_delivered += line.energy_delivered 

    def _compute_total_energy_shared(self):
        for rec in self:
            for line in rec.disco_parameter_ids:
                rec.total_energy_shared += line.energy_shared 

    def _create_journal_entries(self, partner):
        journal_vals = {
            'date': date.today(),
            'journal_id': 3,
            'name': self.billing_cycle_id.name,
            'currency_id': self.env.ref('base.main_company').currency_id.id,
            'company_id': 1,
            'line_ids': [(0, 0, {
                'account_id': 2,
                'partner_id': partner.id,
                'name': self.name,
                'credit': 100,
            }), (0, 0, {
                'account_id': partner.property_account_receivable_id.id,
                'partner_id': partner.id,
                'name': self.name,
                'debit': 100,
            })], 
        }
        move = self.env['account.move'].sudo().create(journal_vals)
        self.move_ids += move

    def _create_invoice(self, partner_id, ref, origin, invoice_value):
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
                'billing_circle_id': rec.billing_cycle_id.id,

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
            invoice_id = self.env['account.move'].create(invoice_vals)
            self.disco_invoice_ids += invoice_id

class DiscoParaemeter(models.Model):
    _name = 'ebs_ocma.disco.invoice.parameter'
    _description = 'Disco Parameters'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(comodel_name='res.partner', string='Disco')
    name = fields.Char(string="Name")
    capacity_delivered = fields.Float(string='Capacity Delivered', required=False)
    energy_delivered = fields.Float(string='Energy Delivered', required=False)

    capacity_shared = fields.Float(string='Capacity Shared (Mw/Month)')
    energy_shared = fields.Float(string='Energy Shared (kWh)')

    percentage_total = fields.Float(string='Percentage of total', required=False, compute='_compute_percentage_total')
    portion_capacity = fields.Float(string='Portion Capacity', required=False, compute='_compute_portion_capacity')
    portion_energy = fields.Float(string='Portion Energy', required=False, compute='_compute_portion_energy')

    percent_shared = fields.Float(string='% Shared', compute='_compute_percent_shared')
    
    invoice_value = fields.Float(string='Invoice Value', required=False)
    invoice_id = fields.Many2one(comodel_name='ebs_ocma.disco.invoice', string="Disco Invoice")
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name

    def _compute_percentage_total(self):
        for rec in self:
            rec.percentage_total = (rec.energy_delivered / rec.invoice_id.total_energy_delivered if rec.invoice_id.total_energy_delivered != 0 else 0) * 100

    def _compute_portion_capacity(self):
        for rec in self:
            related_genco_invoicing = self.env["ebs_ocma.genco.invoice"].search([("billing_cycle_id", "=", rec.invoice_id.billing_cycle_id.id)], limit=1)
            rec.portion_capacity = (rec.percentage_total / 100) * related_genco_invoicing.total_capacity
    
    def _compute_portion_energy(self):
        for rec in self:
            related_genco_invoicing = self.env["ebs_ocma.genco.invoice"].search([("billing_cycle_id", "=", rec.invoice_id.billing_cycle_id.id)], limit=1)
            rec.portion_energy = (rec.percentage_total / 100) * related_genco_invoicing.total_energy_sent_out_mwh

    def _compute_percent_shared(self):
        for rec in self:
            rec.percent_shared = rec.energy_shared / rec.invoice_id.total_energy_shared if rec.invoice_id.total_energy_shared != 0 else 0

    disco_invoice_share_ids = fields.One2many(comodel_name="ebs_ocma.disco.invoice.share.parameter", inverse_name="invoice_parameter_id", string="Disco Share Parameters")
    
class DiscoShareParaemeter(models.Model):
    _name = 'ebs_ocma.disco.invoice.share.parameter'
    _description = 'Disco Share Parameters'

    invoice_parameter_id = fields.Many2one(comodel_name='ebs_ocma.disco.invoice', string="Disco Invoice Parameters")

    contract_share = fields.Float(string="Contract share of energy & capacity")
    actual_share = fields.Float(string="Share actually billed")

    disco_invoice_share_line_ids = fields.One2many(comodel_name="ebs_ocma.disco.invoice.share.parameter.lines", inverse_name="invoice_share_lines_id", string="Disco Share Parameters")

class DiscoShareParaemeter(models.Model):
    _name = 'ebs_ocma.disco.invoice.share.parameter.lines'
    _description = 'Disco Share Parameters Lines'

    invoice_share_lines_id = fields.Many2one(comodel_name='ebs_ocma.disco.invoice.share.parameter', string="Disco Share Parameters Lines")

    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')
    share_capacity_mw_mth = fields.Float('Share of Capacity (MW/Month)')
    share_capacity_mw_hr = fields.Float('Share of Capacity (MW/Hr)')

