# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _get_related_project(self):
        """
        Search related sale of procurement group to get the project
        """
        for mo in self:
            project_id = False
            if mo.procurement_group_id:
                domain = [
                    ('procurement_group_id', '=', mo.procurement_group_id.id)
                ]
                sale_obj = self.env['sale.order'].search(domain, limit=1)
                if sale_obj:
                    project_id = sale_obj.project_wip_id.id
            mo.project_wip_id = project_id

    task_ids = fields.One2many('project.task', 'production_id', 'Tasks',
                               readonly=True)
    project_wip_id = fields.Many2one('project.project', 'Initial Project',
                                     compute='_get_related_project')

    @api.multi
    def _generate_moves(self):
        """
        Instead in create beacause of action_confirm in generate_moves
        """
        track_model = self.env['tracking.wip']
        super(MrpProduction, self)._generate_moves()
        for mo in self:
            track_record = track_model.get_track_for_model(mo._name, mo)
            if track_record:
                track_record.create_task_tracking(mo)

            # Create parent-child relationship
            if mo.task_ids:
                    mo.move_finished_ids.mapped('task_ids').\
                        write({'parent_id': mo.task_ids[0].id})
        return mo

    @api.multi
    def write(self, vals):
        """
        Propagate to task da date expected to date end
        """
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_finished' in vals:
            for mo in self:
                if mo.task_ids and \
                        mo.task_ids[0].date_end != mo.date_planned_finished:
                    mo.task_ids.write({'date_end': mo.date_planned_finished})
        return res

    @api.multi
    def action_cancel(self):
        """
        Remove related task when cancel sale order
        """
        res = super(MrpProduction, self).action_cancel()
        self.mapped('task_ids').unlink()
        return res

    @api.model
    def _create_subcontrated_procurement(self, bom_line, line_data):
        """
        Create a procurement for the subcontrated products in the BoM.
        """
        if self.move_finished_ids and self.move_finished_ids[0].procurement_id:
            warehouse_id = self.move_finished_ids[0].procurement_id.\
                warehouse_id.id
        if not warehouse_id:
            warehouse_id = self.env['stock.warehouse'].search([], limit=1).id
        vals = {
            'name': 'SUBCONTRATED ' + bom_line.product_id.name,
            'origin': self.name,
            'date_planned': datetime.strptime(self.date_planned_start,
                                              DEFAULT_SERVER_DATETIME_FORMAT),
            'product_id': bom_line.product_id.id,
            'product_qty': line_data['qty'],
            'product_uom': bom_line.product_uom_id.id,
            'company_id': self.company_id.id,
            'group_id': self.procurement_group_id.id,
            'warehouse_id': warehouse_id
        }
        new_proc = self.env["procurement.order"].create(vals)
        new_proc.run()
        return

    def _generate_raw_move(self, bom_line, line_data):
        """
        When a subcontrated service is in the bom, create a procurement, in
        order to get the purchase order of the service
        """
        res = super(MrpProduction, self).\
            _generate_raw_move(bom_line, line_data)
        if bom_line.product_id.type == 'service' and \
                bom_line.product_id.property_subcontracted_service:
            self._create_subcontrated_procurement(bom_line, line_data)
        return res
