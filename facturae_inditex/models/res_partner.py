# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    seller_party_id = fields.Char("Seller Id")
    buyer_party_id = fields.Char("Buyer Id")
