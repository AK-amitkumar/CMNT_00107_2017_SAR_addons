# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_wip_id = fields.Many2one('project.project', 'Project')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    task_id = fields.Many2one('project.task', 'Task')
