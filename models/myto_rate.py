from odoo import models, fields, api, _


class MytoRate(models.Model):
    _name = 'ebs_ocma.myto.rate'
    _description = 'Myto Rate'
    _order = 'create_date desc'

    name = fields.Char('Description')
    date_start = fields.Date('From')
    date_end = fields.Date('To')
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Owner")
    user_id = fields.Many2one(comodel_name="res.users", string="User", invisible=True)
    approved_by = fields.Many2one(comodel_name="hr.employee", string="Approved by")
    line_ids = fields.One2many(comodel_name="ebs_ocma.myto.rate.line", inverse_name="rate_id", string="Rates")
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'To Approve'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled'),
    ], string='state', default="draft", readonly=True)
    active = fields.Boolean(string='Active', default=True)
    
    def action_submit(self):
        self.state='open'
        
    def action_approve(self):
        self.state='approve'
        
    def action_reject(self):
        self.state='reject'
        
    def action_cancel(self):
        self.state='cancel'

class MytoRateLine(models.Model):
    _name = 'ebs_ocma.myto.rate.line'
    _description = 'Myto Rate Line'

    # Update to Genco or disco
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    capacity_tarrif = fields.Float('Capacity Tarrif')
    energy_tarrif = fields.Float('Energy Tarrif')
    rate_id = fields.Many2one('ebs_ocma.myto.rate', string='Rate')

class MytoRateCategory(models.Model):
    _name = 'ebs_ocma.myto.rate.cateogry'
    _description = 'Myto Rate Category'
    _order = 'create_date desc'

    name = fields.Selection([
        ('hydros', 'Hydros'),
        ('successor_gencos', 'Successor Gencos'),
        ('fipl', 'FIPL (Rivers)'),
        ('shell', 'SHELL (AFAM VI)'),
        ('agip', 'AGIP (OKPAI)'),
        ('olorunsogo', 'Olorunsogo & Omotosho'),
        ('ibom', 'IBOM POWER'),
        ('nipps', 'NIPPS'),
        ('calabar_nipp', 'CALABAR NIPP'),
        ('gbarain_nipp', 'GBARAIN NIPP'),
    ], string='Name')

    active = fields.Boolean(string='Active', default=True)

    cateogry_line_ids = fields.One2many(comodel_name="ebs_ocma.myto.rate.cateogry.line", inverse_name="category_id", string="Rates Category")

class MytoRateCategoryLine(models.Model):
    _name = 'ebs_ocma.myto.rate.cateogry.line'
    _description = 'Myto Rate Category.line'
    _order = 'create_date desc'

    name = fields.Selection([
        ('usd_naira_fx', 'USD/Naira fx (CBN Rate)'),
        ('us_cpi_index', 'US CPI (Index)'),
        ('fixed_om', 'FIXED O&M (N/MW/Hr)'),
        ('variable_om', 'VARIABLE O&M (N/MWh)'),
        ('capital_recovery', 'Capital Recovery (N/MW/Hr)'),
        ('energy_charge', 'Energy Charge (N/MW/Hr)'),
        ('capacity_charge', 'Capacity Charge (N/MW/Hr)'),
        ('wholsale_charge', 'Wholesale Charge (N/MW/Hr)'),
    ], string='Description')

    base_myto  = fields.Float(string = "Base Myto")
    base_tarrif  = fields.Float(string = "Base tarrif")

    category_id = fields.Many2one(comodel_name="ebs_ocma.myto.rate.cateogry", string="Category")

    @api.onchange('usd_naira_fx')
    def _onchange_usd_naira_fx(self):
        for rec in self:
            if rec.category_id.name == "hydros":
                related_billing_cycle = self.env["billing.cycle"].search([], limit=1)
                rec.base_tarrif = related_billing_cycle.cbn_average