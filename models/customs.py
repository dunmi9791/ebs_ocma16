from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    disco_credit_account_id = fields.Many2one('account.account', string='Disco Credit Account')
    disco_sales_account_id = fields.Many2one('account.account', string='Disco Sales Account')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    disco_credit_account_id = fields.Many2one(
        related='company_id.disco_credit_account_id',
        string="Disco Credit Account",
        readonly=False
    )
    disco_sales_account_id = fields.Many2one(
        related='company_id.disco_sales_account_id',
        string="Disco Sales Account",
        readonly=False
    )