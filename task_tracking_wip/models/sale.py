# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_wip_id = fields.Many2one('project.project', 'Project')

    @api.multi
    def action_confirm(self):
        """
        Create a task in each order line
        """
        track_model = self.env['tracking.wip']
        for line in self.order_line:
            track_record = track_model.get_track_for_model(line._name, line)
            if track_record:
                track_record.create_task_tracking(line)
        res = super(SaleOrder, self).action_confirm()
        return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(SaleOrder, self).action_cancel()
        self.mapped('order_line.task_id').unlink()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    task_id = fields.Many2one('project.task', 'Task')
