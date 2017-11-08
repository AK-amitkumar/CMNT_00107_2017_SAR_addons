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

        visited_mo = self.env['mrp.production']
        stop_search_mo = False
        for order in self:
            while not stop_search_mo:
                domain = [
                    ('procurement_group_id', '=',
                        self.procurement_group_id.id),
                    ('state', '=', 'confirmed')
                ]
                if visited_mo:
                    domain.append(('id', 'not in', visited_mo._ids))
                mo_obj = self.env['mrp.production'].search(domain, limit=1)
                if mo_obj:
                    mo_obj.move_finished_ids.action_confirm()
                    mo_obj.move_raw_ids.action_confirm()
                    track_model.set_production_task_dependencies(mo_obj)
                    # Nedd to get make to stock raw moves in the picking
                    mo_obj.action_assign()
                    visited_mo += mo_obj
                else:
                    stop_search_mo = True
        return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(SaleOrder, self).action_cancel()
        self.mapped('order_line.task_id').unlink()
        return res

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if not res.requested_date:
            res.requested_date = res.commitment_date
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    task_id = fields.Many2one('project.task', 'Task', readonly=True)
