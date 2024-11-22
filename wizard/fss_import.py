from odoo import models, fields, api
import base64
import io
import pandas as pd
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class GencoParameterImportWizard(models.TransientModel):
    _name = 'genco.parameter.import.wizard'
    _description = 'Import Genco Parameters Wizard'

    file = fields.Binary(string="Excel File", required=True)
    file_name = fields.Char(string="File Name")
    line_ids = fields.One2many('genco.parameter.import.wizard.line', 'wizard_id', string="Genco Parameters")
    billing_cycle_id = fields.Many2one('billing.cycle', string="Billing Cycle")

    @api.model
    def default_get(self, fields):
        res = super(GencoParameterImportWizard, self).default_get(fields)
        billing_cycle_id = self.env.context.get('default_billing_cycle_id')
        if billing_cycle_id:
            res.update({'billing_cycle_id': billing_cycle_id})
        _logger.info(f"Genco wizard opened with Billing Cycle ID: {billing_cycle_id}")
        return res

    def import_file(self):
        if not self.file:
            raise UserError("Please upload an Excel file.")

        # Decode the file
        file_data = base64.b64decode(self.file)
        file_like = io.BytesIO(file_data)

        # Read the Excel file
        try:
            df = pd.read_excel(file_like)
        except Exception as e:
            raise UserError(f"Error reading Excel file: {e}")

        required_columns = ['Name', 'Genco', 'Capacity Sent Out (MW)', 'Energy Sent Out (kWh)', 'Capacity Import (MW)',
                            'Energy Import (kWh)', ]
        for col in required_columns:
            if col not in df.columns:
                raise UserError(f"Missing required column: {col}")

        lines = []
        for index, row in df.iterrows():
            partner = self.env['res.partner'].search([('name', '=', row['Genco'])], limit=1)
            if not partner:
                raise UserError(f"Partner {row['Genco']} not found.")
            lines.append((0, 0, {
                'name': row['Name'],
                'partner_id': partner.id,
                'capacity_sent_out_mw': row['Capacity Sent Out (MW)'],
                'energy_sent_out_kwh': row['Energy Sent Out (kWh)'],
                'capacity_import': row['Capacity Import (MW)'],
                'energy_import': row['Energy Import (kWh)'],
            }))

        self.line_ids = lines

        _logger.info(f"Imported {len(lines)} lines successfully")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'genco.parameter.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def confirm_import(self):
        for line in self.line_ids:
            self.env['ebs_ocma.genco.invoice.billing_cycle.parameter'].create({
                'billing_cycle_id': self.billing_cycle_id.id,
                # 'name': line.name,
                'partner_id': line.partner_id.id,
                'capacity_sent_out_mw': line.capacity_sent_out_mw,
                'energy_sent_out_kwh': line.energy_sent_out_kwh,
                'capacity_import': line.capacity_import,
                'energy_import': line.energy_import,
            })

        return {'type': 'ir.actions.act_window_close'}


class GencoParameterImportWizardLine(models.TransientModel):
    _name = 'genco.parameter.import.wizard.line'
    _description = 'Genco Parameter Import Wizard Line'

    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Genco')
    capacity_sent_out_mw = fields.Float(string='Capacity Sent Out (MW)')
    energy_sent_out_kwh = fields.Float(string='Energy Sent Out (kWh)')
    capacity_import = fields.Float(string='Capacity Import (MW)')
    energy_import = fields.Float(string='Energy Import (kWh)')
    wizard_id = fields.Many2one('genco.parameter.import.wizard', string="Wizard")


