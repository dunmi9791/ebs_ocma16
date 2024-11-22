from odoo import models, fields, api
import base64
import io
import pandas as pd
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DiscoParameterImportWizard(models.TransientModel):
    _name = 'disco.parameter.import.wizard'
    _description = 'Import Disco Parameters Wizard'

    file = fields.Binary(string="Excel File", required=True)
    file_name = fields.Char(string="File Name")
    line_ids = fields.One2many('disco.parameter.import.wizard.line', 'wizard_id', string="Disco Parameters")
    billing_cycle_id = fields.Many2one('billing.cycle', string="Billing Cycle")

    @api.model
    def default_get(self, fields):
        res = super(DiscoParameterImportWizard, self).default_get(fields)
        billing_cycle_id = self.env.context.get('default_billing_cycle_id')
        if billing_cycle_id:
            res.update({'billing_cycle_id': billing_cycle_id})
        _logger.info(f"Disco wizard opened with Billing Cycle ID: {billing_cycle_id}")
        return res

    def import_file(self):
        if not self.file:
            raise UserError("Please upload an Excel file.")

        # Decode the file
        file_data = base64.b64decode(self.file)
        file_like = io.BytesIO(file_data)

        # Read the Excel file
        df = pd.read_excel(file_like)

        lines = []
        for index, row in df.iterrows():
            partner = self.env['res.partner'].search([('name', '=', row['Disco'])], limit=1)
            if not partner:
                raise UserError(f"Partner {row['Disco']} not found.")
            lines.append((0, 0, {
                'name': row['Name'],
                'partner_id': partner.id,
                # Match the partner_id appropriately
                'capacity_delivered': row['Capacity Delivered (MW)'],
                'energy_delivered': row['Energy Delivered (kWh)'],
                'capacity_shared': row['Capacity Shared (MW)'],
                'energy_shared': row['Energy Shared (kWh)'],

            }))

        self.line_ids = lines

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'disco.parameter.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def confirm_import(self):
        for line in self.line_ids:
            self.env['ebs_ocma.disco.invoice.billing_cycle.parameter'].create({
                'billing_cycle_id': self.billing_cycle_id.id,
                # 'name': line.name,
                'partner_id': line.partner_id.id,
                'capacity_delivered': line.capacity_delivered,
                'energy_delivered': line.energy_delivered,
                'capacity_shared': line.capacity_shared,
                'energy_shared': line.energy_shared,
            })

        return {'type': 'ir.actions.act_window_close'}


class DiscoParameterImportWizardLine(models.TransientModel):
    _name = 'disco.parameter.import.wizard.line'
    _description = 'Disco Parameter Import Wizard Line'

    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name='res.partner', string='disco')
    capacity_delivered = fields.Float(string='Capacity Delivered (MW)')
    energy_delivered = fields.Float(string='Energy delivered (kWh)')
    capacity_shared = fields.Float(string='Capacity Shared (MW)')
    energy_shared = fields.Float(string='Energy Shared (kWh)')
    wizard_id = fields.Many2one('disco.parameter.import.wizard', string="Wizard")