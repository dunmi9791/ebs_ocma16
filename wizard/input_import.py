# -*- coding:utf-8 -*-

import base64
import csv
import xlrd
from xlrd import open_workbook
import datetime
from odoo import models,fields,api,_ , exceptions
from odoo.exceptions import ValidationError
from openerp.exceptions import UserError
import openpyxl
from openpyxl import load_workbook
import base64
from io import BytesIO
from odoo.exceptions import UserError
import pandas as pd


class ImportBudgetLineWizard(models.TransientModel):
    _name = "import.input.line.wizard"

    files = fields.Binary(
        string="Import Excel File",
    )
    datas_fname = fields.Char(
        string='Import File Name'
    )
    billing_cycle_id = fields.Many2one(
        comodel_name='billing.cycle',
        string='Billing_cycle_id',
        required=False)

    def input_genco_file(self):
        if not self.files:
            raise exceptions.UserError('No file found for import.')

        excel_file_data = base64.b64decode(self.files)
        dataframe = pd.read_excel(BytesIO(excel_file_data))

        for index, row in dataframe.iterrows():
            # Search for the user by their name
            genco = row['genco']
            user = self.env['res.partner'].search([('name', '=', genco)], limit=1)

            if not user:
                raise exceptions.UserError(f'Genco with name "{genco}" not found.')

            # Create a new genco parameter record with the parsed data
            self.env['ebs_ocma.genco.invoice.billing_cycle.parameter'].create({
                'billing_cycle_id': self.billing_cycle_id.id,
                'partner_id': user.id,
                'capacity_sent_out_mw': row['capacity_sent_out_mw'],
                'energy_sent_out_kwh': row['energy_sent_out_kwh'],
                'capacity_import': row['capacity_import'],
                'energy_import': row['energy_import'],
            })


class ImportDiscoLineWizard(models.TransientModel):
    _name = "import.disco.line.wizard"

    files = fields.Binary(
        string="Import Excel File",
    )
    datas_fname = fields.Char(
        string='Import File Name'
    )
    billing_cycle_id = fields.Many2one(
        comodel_name='billing.cycle',
        string='Billing_cycle_id',
        required=False)

    def input_disco_file(self):
        if not self.files:
            raise exceptions.UserError('No file found for import.')

        excel_file_data = base64.b64decode(self.files)
        dataframe = pd.read_excel(BytesIO(excel_file_data))

        for index, row in dataframe.iterrows():
            # Search for the user by their name
            disco = row['disco']
            user = self.env['res.partner'].search([('name', '=', disco)], limit=1)

            if not user:
                raise exceptions.UserError(f'Disco with name "{disco}" not found.')

            # Create a new disco parameter record with the parsed data
            self.env['ebs_ocma.disco.invoice.billing_cycle.parameter'].create({
                'billing_cycle_id': self.billing_cycle_id.id,
                'partner_id': user.id,
                'capacity_delivered': row['capacity_delivered'],
                'energy_delivered': row['energy_delivered'],
            })

