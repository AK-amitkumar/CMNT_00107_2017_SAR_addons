# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    task_id = fields.Many2one('project_task', 'Task')

