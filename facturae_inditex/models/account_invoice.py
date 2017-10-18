# -*- coding: utf-8 -*-

from odoo import fields, models

import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    customer_order_ref = fields.Char(string='Customer Order Reference', copy=False)
    customer_delivery_ref = fields.Char(string='Customer Delivery Reference', copy=False)
    ple_number = fields.Char(string='PLE', copy=False)
    delivery_date = fields.Date(string='Delivery Date', copy=False)
    transport_mode_id = fields.Many2one('transport.mode', string='Transport Mode')
    net_weight = fields.Float(string='Net Weight', digits=dp.get_precision('Stock Weight'))
    volume = fields.Float(string='Volume', digits=dp.get_precision('Stock Weight'))
    number_of_cartons = fields.Integer(string='Number of Cartons')
    campaign = fields.Char(string='Campaign', size=5)

