from odoo import models, fields, api, _


class CbnRates(models.Model):
    _name = 'cbn.dollar.rate'

    rate_date = fields.Date(string='Rate_date', required=False)
    currency = fields.Char(string='Currency', required=False)
    rate_year = fields.Char('Rate Year')
    rate_month = fields.Char('Rate Month')
    buying_rate = fields.Float(string='Buying Rate')
    central_rate = fields.Float(string='Central Rate')
    selling_rate = fields.Float(string='Selling Rate')
    # Add more fields as necessary

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]

    @api.model
    def scheduled_import_csv(self):
        wizard = self.env['currency.import_wizard'].create({})
        wizard.import_csv()

