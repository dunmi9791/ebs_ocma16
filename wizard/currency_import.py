import base64
import csv
import io
import requests
from odoo import models, fields, api
from datetime import date

from datetime import datetime

class ImportWizard(models.TransientModel):
    _name = 'currency.import_wizard'

    def import_csv(self):
        self.ensure_one()
        url = 'https://www.cbn.gov.ng/Functions/export.asp?tablename=exchange'
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the request failed
        data = response.content.decode('utf-8')
        file_input = io.StringIO(data)
        file_input.seek(0)
        reader = csv.reader(file_input, delimiter=',', lineterminator='\r\n')
        next(reader)  # Skip the header
        for row in reader:
            if row[1] == 'US DOLLAR':
                date_str = row[0]  # Adjust the index based on your CSV structure
                date = datetime.strptime(date_str, '%m/%d/%Y').date()
                existing_record = self.env['cbn.dollar.rate'].search([('rate_date', '=', date)], limit=1)
                if not existing_record:
                    self.env['cbn.dollar.rate'].create({
                        'rate_date': date,
                        'currency': row[1],
                        'rate_year': row[2],
                        'rate_month': row[3],
                        'buying_rate': row[4],
                        'central_rate': row[5],
                        'selling_rate': row[6],
                        # Add more fields as necessary
                    })
