# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_related_project(self):
        """
        Search related sale of procurement group to get the project
        """
        for pick in self:
            project_id = False
            if pick.group_id:
                domain = [('procurement_group_id', '=', pick.group_id.id)]
                sale_obj = self.env['sale.order'].search(domain, limit=1)
                if sale_obj:
                    project_id = sale_obj.project_wip_id.id
            if not project_id and pick.move_lines \
                    and pick.move_lines[0].move_dest_id:
                project_id = pick.move_lines[0].move_dest_id.\
                    picking_id.project_wip_id.id
            pick.project_wip_id = project_id

    task_id = fields.Many2one('project.task', 'Task', readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Project',
                                     compute='_get_related_project')

    @api.multi
    def write(self, vals):
        """
        Propagate to task da date expected to date end
        """
        res = super(StockPicking, self).write(vals)
        if 'min_date' in vals:
            for pick in self:
                if pick.task_id and \
                        pick.task_id.date_end != pick.min_date:
                    pick.task_id.date_end = pick.min_date
        return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(StockPicking, self).action_cancel()
        self.mapped('task_id').unlink()
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_related_project(self):
        """
        Search related sale of procurement group to get the project
        """
        for move in self:
            project_id = False
            if move.group_id:
                domain = [('procurement_group_id', '=', move.group_id.id)]
                sale_obj = self.env['sale.order'].search(domain, limit=1)
                if sale_obj:
                    project_id = sale_obj.project_wip_id.id
            if not project_id and move.move_dest_id:
                project_id = move.move_dest_id.project_wip_id.id
            move.project_wip_id = project_id

    task_id = fields.Many2one('project.task', 'Task', readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Project',
                                     compute='_get_related_project')

    @api.multi
    def assign_picking(self):
        track_model = self.env['tracking.wip']
        res = super(StockMove, self).assign_picking()
        for move in self:
            pick = move.picking_id
            if pick and not pick.task_id:
                track_record = track_model.get_track_for_model(pick._name,
                                                               pick)
                if track_record:
                    track_record.create_task_tracking(pick)

            # Create parent-child relationship
            if move.task_id and pick.task_id:
                # We need both writes
                pick.move_lines.mapped('task_id').\
                    write({'parent_id': pick.task_id.id})
                move.task_id.write({'parent_id': pick.task_id.id})
            return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(StockMove, self).action_cancel()
        self.mapped('picking_id.task_id').unlink()
        self.mapped('task_id').unlink()
        return res

    @api.multi
    def action_confirm(self):
        """
        """
        # import ipdb; ipdb.set_trace()
        res = False
        if not self._context.get('no_confirm', False):
            res = super(StockMove, self).action_confirm()
        return res

    @api.model
    def create(self, vals):
        track_model = self.env['tracking.wip']
        res = super(StockMove, self).create(vals)
        track_record = track_model.get_track_for_model(res._name, res)
        if track_record:
            track_record.create_task_tracking(res)

        return res

    @api.multi
    def write(self, vals):
        """
        Propagate to task da date expected to date end
        """
        res = super(StockMove, self).write(vals)
        if 'date_expected' in vals:
            for move in self:
                if move.task_id and \
                        move.task_id.date_end != move.date_expected:
                    move.task_id.date_end = move.date_expected
        return res
