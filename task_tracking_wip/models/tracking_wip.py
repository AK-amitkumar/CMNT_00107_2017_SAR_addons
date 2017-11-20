# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class TrackingWip(models.Model):
    """ Inherits partner and adds Tasks information in the partner form """
    _name = 'tracking.wip'

    name = fields.Char('Name', required=True)
    model_id = fields.Many2one('ir.model', 'Model to track', required=True)
    condition_eval = fields.Text('Condition', required=True)
    project_eval = fields.Text('Project')
    name_eval = fields.Text('Task Name')
    # start_date_eval = fields.Text('Start Date')
    # end_date_eval = fields.Text('End Date')
    state = fields.Selection([('deactivated', 'Deactivated'),
                              ('active', 'Active')], 'State',
                             default='deactivated')
    color_gantt = fields.Char(
        string="Color Task Bar",
        help="Choose your color for Task Bar",
        default="#FFFFFF"
    )

    @api.multi
    def deactivate(self):
        # self._revert_methods()
        self.write({'state': 'deactivated'})
        return True

    @api.multi
    def activate(self):
        self.write({'state': 'active'})
        return True

    @api.multi
    @api.constrains('model_id')
    def check_related_model_task_id(self):
        """
        Check if related model has task_id
        """
        for track in self:
            model_name = self.model_id.model
            if not hasattr(self.env[model_name], 'task_id'):
                raise ValidationError(_(
                    "The selected model can not be tracked because is not "
                    "related with task model"))

    @api.model
    def get_track_for_model(self, model_name, o):
        """
        Search a track.wip model actived and for the required model
        """
        domain = [('model_id.model', '=', model_name),
                  ('state', '=', 'active')]
        track_objs = self.search(domain)
        for track in track_objs:
            if eval(track.condition_eval):
                print "***********************************"
                print track.name
                print "***********************************"
                return track
        return False

    @api.model
    def link_predecessor_task(self, task_recs, parent_task, link_move="FS"):
        if task_recs and parent_task:
            vals = {
                'parent_task_id': parent_task.id,
                'type': link_move
            }
            task_recs.write({'predecessor_ids': [(0, 0, vals)]})

    @api.model
    def set_pick_task_dependencies(self, o):
        print "#################################################"
        print o.name + " | " + o.origin
        print "#################################################"
        task_recs = self.env['project.task']
        parent_task = o.task_id
        pick_move = o.move_lines and o.move_lines[0]
        if not pick_move:
            return
        # Set dependency for out pickings to the sale
        if pick_move and pick_move.procurement_id and \
                pick_move.procurement_id.sale_line_id:
            task_recs += pick_move.picking_id.\
                mapped('move_lines.procurement_id.sale_line_id.task_id')

            self.link_predecessor_task(task_recs, parent_task, "FF")

        domain = [('move_dest_id', '=', pick_move.id)]
        rel_mov = self.env['stock.move'].search(domain, limit=1)
        parent_task = False
        if rel_mov and rel_mov.picking_id:
            task_recs = o.task_id
            parent_task = rel_mov.picking_id.task_id

        elif rel_mov and rel_mov.production_id:
            task_recs = o.task_id
            parent_task = rel_mov.production_id.task_id

        self.link_predecessor_task(task_recs, parent_task)
        return

    @api.model
    def set_move_task_dependencies(self, o):
        task_recs = self.env['project.task']
        # Set dependency of move_dest_id task
        if o.procurement_id and o.procurement_id.sale_line_id:
            task_recs += o.procurement_id.sale_line_id.task_id
        # Set dependecy in sale_line_id task
        elif o.move_dest_id:
            if o.move_dest_id.raw_material_production_id:
                task_recs += o.move_dest_id.raw_material_production_id.\
                    move_finished_ids.mapped('task_id')
            else:
                task_recs += o.move_dest_id.task_id
        # Set dependency of consume moves to finished move in production
        # elif o.raw_material_production_id:
        #     task_recs = o.raw_material_production_id.move_finished_ids.\
        #         mapped('task_id')

        # Write dependency if exists
        parent_task = o.task_id
        self.link_predecessor_task(task_recs, parent_task)

        if o.task_id and o.production_id and o.production_id.task_id:
            o.task_id.write({'parent_id': o.production_id.task_id.id})

    @api.model
    def set_production_task_dependencies(self, o):
        task_recs = self.env['project.task']
        parent_task = False
        if o.move_raw_ids:
            domain = [('move_dest_id', '=', o.move_raw_ids[0].id)]
            prev_move = self.env['stock.move'].search(domain)
            parent_task = prev_move.picking_id.task_id
        task_recs = o.task_id
        self.link_predecessor_task(task_recs, parent_task)
        return

    @api.model
    def set_workorder_task_dependencies(self, o):
        task_recs = self.env['project.task']
        # Set dependency of move_dest_id task
        if o.production_id and o.production_id.move_finished_ids:
            task_recs += o.production_id.task_id
        # Write dependency if exists
        parent_task = o.task_id
        self.link_predecessor_task(task_recs, parent_task)
        return

    @api.model
    def _get_task_tale_id(self, o):
        res = False
        proc_group = False
        if o._name in ['stock.picking', 'stock.move']:
            proc_group = o.group_id
        elif o._name == 'sale.order.line':  # Need do it after action confirm
            proc_group = o.order_id and o.order_id.procurement_group_id or \
                False
        elif o._name == 'mrp.production':
            proc_group = o.procurement_group_id
        elif o._name == 'mrp.workorder':
            proc_group = o.production_id and \
                o.production_id.procurement_group_id or False

        if proc_group:
            domain = [('procurement_group_id', '=', proc_group.id)]
            sale_obj = self.env['sale.order'].search(domain, limit=1)
            if sale_obj:
                res = sale_obj.id

        return res

    @api.multi
    def create_task_tracking(self, o):
        """
        If not task created, create a task and
        link it to record.
        """
        self.ensure_one()
        if not o.task_id:
            date_start = False
            date_end = False
            if o._name == 'sale.order.line':
                date_start = o.order_id.date_order
                date_end = o.order_id.commitment_date
            elif o._name == 'stock.picking':
                date_start = o.min_date
                date_end = o.min_date
                if o.move_lines and o.move_lines[0].purchase_line_id:
                    date_start = o.purchase_line_id.date_order
            elif o._name == 'stock.move':
                date_start = o.date_expected
                date_end = o.date_expected
            elif o._name == 'mrp.production':
                date_start = o.date_planned_start
                date_end = o.date_planned_finished
            elif o._name == 'mrp.workorder':
                date_start = o.date_planned_start
                date_end = o.date_planned_finished
            vals = {
                'name': eval(self.name_eval),
                'project_id': eval(self.project_eval),
                'date_start': date_start,
                'date_end': date_end if date_end > date_start else date_start,
                'model_reference': o._name + ',' + str(o.id),
                'color_gantt': self.color_gantt,
                'color_gantt_set': True,
                'sale_id': self._get_task_tale_id(o),
            }
            task_obj = self.env['project.task'].create(vals)
            o.write({'task_id': task_obj.id})

            if o._name == 'stock.picking':
                self.set_pick_task_dependencies(o)
            if o._name == 'stock.move':
                self.set_move_task_dependencies(o)
            elif o._name == 'mrp.production':
                self.set_production_task_dependencies(o)
            elif o._name == 'mrp.workorder':
                self.set_workorder_task_dependencies(o)
