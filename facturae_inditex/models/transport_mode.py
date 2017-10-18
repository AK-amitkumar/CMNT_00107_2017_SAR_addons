# -*- coding: utf-8 -*-

from odoo import models, fields


class TransportMode(models.Model):
    _name = "transport.mode"

    name = fields.Char('Name', required=True, translate=True)