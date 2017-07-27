# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountAnalyticTag(models.Model):
    """Se representará la temporada como una etiqueta de cuentas analíticas"""

    _inherit = "account.analytic.tag"

    type = fields.Selection([('season', 'Season')], "Type")
    active = fields.Boolean("Active", default=True)
    code = fields.Char()
