from odoo import models, fields, api, _


class UsCpiIndices(models.Model):
    _name = 'uscpi.indices'
    _description = 'UsCpiIndices'
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    us_cpi = fields.Float(
        string='Us CPI',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


class FxCbn(models.Model):
    _name = 'fx.cbn'
    _description = 'CBN rate'
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    fx_cbn = fields.Float(
        string='FX (CBN Rate)',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


class Ncpi(models.Model):
    _name = 'ncpi.indices'
    _description = 'NCPI '
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    ng_cpi = fields.Float(
        string='NCPI',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


class UsPpiIndices(models.Model):
    _name = 'usppi.indices'
    _description = 'Us Ppi Indices'
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    us_ppi = fields.Float(
        string='Us PPI',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


class NigerianCpiIndices(models.Model):
    _name = 'nigeriancpi.indices'
    _description = 'Nigerian CpiIndices'
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    nigerian_cpi = fields.Float(
        string='Nigerian CPI',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


class FxCbnSelling(models.Model):
    _name = 'fx.cbn.selling'
    _description = 'CBN Selling rates'
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    fx_cbn_selling = fields.Float(
        string='CBN Selling Rate',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


class FxCbnBuying(models.Model):
    _name = 'fx.cbn.buying'
    _description = 'CBN Buying rates'
    _order = 'date'

    date = fields.Date(
        string='Date',
        required=False)
    fx_cbn_buying = fields.Float(
        string='CBN Buying Rate',
        required=False)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'only one rate for a day is allowed'),
    ]


