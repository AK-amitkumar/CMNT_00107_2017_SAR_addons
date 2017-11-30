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
            if not hasattr(self.env[model_name], 'task_id') or \
                    not hasattr(self.env[model_name], 'task_ids'):
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
        """
        Write parent task like predecessors for the task recs.
        """
        if task_recs and parent_task:
            vals = {
                'parent_task_id': parent_task.id,
                'type': link_move
            }
            task_recs.write({'predecessor_ids': [(0, 0, vals)]})

    @api.model
    def set_pick_task_dependencies(self, o):
        print "############DEPENDENCY FOR PICKING#####################"
        print o.name + " | " + o.origin
        print "#######################################################"
        task_recs = self.env['project.task']
        parent_task = o.task_ids[0]
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
            task_recs = o.task_ids[0]
            parent_task = rel_mov.picking_id.task_ids[0]

        elif rel_mov and rel_mov.production_id:
            task_recs = o.task_ids[0]
            parent_task = rel_mov.production_id.task_ids and \
                rel_mov.production_id.task_ids[0] or False

        self.link_predecessor_task(task_recs, parent_task)
        return

    @api.model
    def set_move_task_dependencies(self, o):
        print "###########DEPENDENCY FOR MOVE###################"
        print o.name + " | " + o.origin
        print "#################################################"
        task_recs = self.env['project.task']
        # Set dependency of move_dest_id task
        if o.procurement_id and o.procurement_id.sale_line_id:
            task_recs += o.procurement_id.sale_line_id.task_id
        # Set dependecy in sale_line_id task
        elif o.move_dest_id:
            if o.move_dest_id.raw_material_production_id:
                task_recs += o.move_dest_id.raw_material_production_id.\
                    move_finished_ids.mapped('task_ids')
            else:
                task_recs += o.move_dest_id.task_ids
        # Set dependency of consume moves to finished move in production
        # elif o.raw_material_production_id:
        #     task_recs = o.raw_material_production_id.move_finished_ids.\
        #         mapped('task_id')

        # Write dependency if exists
        parent_task = o.task_ids[0]
        self.link_predecessor_task(task_recs, parent_task)

        if o.task_ids and o.production_id and o.production_id.task_ids:
            o.task_ids.write({'parent_id': o.production_id.task_ids[0].id})

    @api.model
    def set_production_task_dependencies(self, o):
        task_recs = self.env['project.task']
        parent_task = False
        if o.move_raw_ids:
            domain = [('move_dest_id', '=', o.move_raw_ids[0].id)]
            prev_move = self.env['stock.move'].search(domain)
            parent_task = prev_move.picking_id.task_ids and \
                prev_move.picking_id.task_ids[0] or False
        task_recs = o.task_ids
        self.link_predecessor_task(task_recs, parent_task)
        return

    @api.model
    def set_workorder_task_dependencies(self, o):
        task_recs = self.env['project.task']
        # Set dependency of move_dest_id task
        if o.production_id and o.production_id.move_finished_ids:
            task_recs += o.production_id.task_ids
        # Write dependency if exists
        parent_task = o.task_ids[0]
        self.link_predecessor_task(task_recs, parent_task)
        return

    @api.model
    def _get_task_sale_id(self, o):
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
            else:
                # Incoming move, whithout distribution lines
                if o._name == 'stock.move':
                    dest_id_sales = o.move_dest_id.mapped('task_ids.sale_id')
                elif o._name == 'stock.picking':
                    dest_id_sales = o.mapped('move_lines.task_ids.sale_id')

                if dest_id_sales:
                    res = dest_id_sales[0].id
        return res

    @api.multi
    def create_task_tracking(self, o):
        """
        If not task created, create a task and
        link it to record.
        """
        self.ensure_one()
        exist_task = False
        if o._name not in ['stock.move', 'stock.picking', 'mrp.production'] \
                and o.task_id:
            exist_task = True
        if o._name in ['stock.move', 'stock.picking', 'mrp.production'] \
                and o.task_ids:
            exist_task = True

        if not exist_task:
            date_start = False
            date_end = False
            if o._name == 'sale.order.line':
                date_start = o.order_id.date_order
                date_end = o.order_id.commitment_date
            elif o._name == 'stock.picking':
                date_start = o.min_date
                date_end = o.min_date
                if o.move_lines and o.move_lines[0].purchase_line_id:
                    date_start = o.move_lines[0].purchase_line_id.date_order
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
                'sale_id': self._get_task_sale_id(o),
            }
            task_obj = self.env['project.task'].create(vals)
            if o._name not in ['stock.move', 'stock.picking',
                               'mrp.production']:
                o.write({'task_id': task_obj.id})
            else:
                o.write({'task_ids': [(6, 0, [task_obj.id])]})

            if o._name == 'stock.picking':
                self.set_pick_task_dependencies(o)
            if o._name == 'stock.move':
                self.set_move_task_dependencies(o)
            elif o._name == 'mrp.production':
                self.set_production_task_dependencies(o)
            elif o._name == 'mrp.workorder':
                self.set_workorder_task_dependencies(o)

    @api.multi
    def create_move_tasks_tracking(self, o):
        """
        Called when creating moves from purchase line or when update
        a distribution for a move.
        o reference is allways a move.
        Create  a task for each distribution lines
        """
        self.ensure_one()
        date_start = o.date_expected
        date_end = o.date_expected
        task_objs = self.env['project.task']
        for line in o.wip_line_ids:
            next_task = line.task_id
            vals = {
                'name': eval(self.name_eval),
                'project_id': next_task.project_id.id,
                'date_start': date_start,
                'date_end': date_end if date_end > date_start else date_start,
                'model_reference': o._name + ',' + str(o.id),
                'color_gantt': self.color_gantt,
                'color_gantt_set': True,
                'sale_id': line.sale_id.id,
            }

            created_task = self.env['project.task'].create(vals)
            # Write dependency if exists.
            # Write next_task predecessor = created_task
            self.link_predecessor_task(next_task, created_task)
            task_objs += created_task

        o.write({'task_ids': [(6, 0, task_objs.ids)]})

    @api.multi
    def manage_parent_child_tasks(self, o):
        """
        o is picking
        Update task_ids in picking, one for each sale related in move's tasks.
        Get parent - child relationship between them.
        Wè siposse child task dependencies are setted so we link picking tasks
        with the nex picking related
        """

        # Group move tasks by sale
        tasks_by_sale = {}
        for move in o.move_lines:
            for task in move.task_ids:
                if task.sale_id.id not in tasks_by_sale:
                    tasks_by_sale[task.sale_id.id] = self.env['project.task']
                tasks_by_sale[task.sale_id.id] += task

        # If not task ids in moves delete all tasks and finish
        if not o.move_lines.task_ids:
            o.task_ids.unlink()

        # TODO this must not hapen, MAYBE RESOLVED
        tasks_without_sale = o.task_ids.filtered(lambda t: not t.sale_id)
        tasks_without_sale.unlink()

        for sale_id in tasks_by_sale:
            so_task = False
            child_tasks = tasks_by_sale[sale_id]
            so_task = o.task_ids.\
                filtered(lambda t: t.sale_id.id == sale_id)
            # Create New grouping task
            if not so_task:
                ref_task = child_tasks[0]
                vals = {
                    'name': eval(self.name_eval),
                    'project_id': ref_task.project_id.id,
                    'date_start': ref_task.date_start,
                    'date_end': ref_task.date_end
                    if ref_task.date_end > ref_task.date_start
                    else ref_task.date_start,
                    'model_reference': o._name + ',' + str(o.id),
                    'color_gantt': self.color_gantt,
                    'color_gantt_set': True,
                    'sale_id': sale_id,
                }
                so_task = self.env['project.task'].create(vals)
                o.write({'task_ids': [(4, so_task.id)]})
            # Create parent-child relationship
            child_tasks.write({'parent_id': so_task.id})

            # Set grouping task dependecies
            if not so_task.sucessor_ids:
                if child_tasks[0].sucessor_ids \
                        and child_tasks[0].sucessor_ids[0].task_id.parent_id:
                    next_task = child_tasks[0].sucessor_ids[0].task_id.\
                        parent_id
                    # Write dependency if exists.
                    # Write next_task predecessor = so_task
                    self.link_predecessor_task(next_task, so_task)

        # Delete old parent tasks witch sale_id not in th related task moves
        task_to_delete = o.task_ids.\
            filtered(lambda t: t.sale_id.id not in tasks_by_sale)
        task_to_delete.unlink()

    @api.model
    def recompute_move_task_ids(self, o):
        """
        Recreate task based in distribution lines.
        Link sucessors and recompute parent task in the related picking
        """
        track_model = self.env['tracking.wip']
        o.task_ids.unlink()
        track_record = track_model.get_track_for_model(o._name, o)
        if track_record:
            # Not task record when incoming move without distribution lines
            # It couldent eval project_wip_id
            track_record.create_move_tasks_tracking(o)

        picking = o.picking_id
        track_record = track_model.get_track_for_model(picking._name,
                                                       picking)
        if track_record:
            track_record.manage_parent_child_tasks(picking)
        elif not picking.mapped('move_lines.task_ids'):
            # Not task record when incoming move without distribution lines
            # It couldent eval project_wip_id
            picking.task_ids.unlink()

    # @api.model
    # def recompute_tasks_from_reserve(self, move):
    #     """
    #     """
    #     # import ipdb; ipdb.set_trace()
    #     orig_moves = self.env['stock.move']
    #     for quant in move.reserved_quant_ids:
    #         orig_moves += quant._get_latest_move()

    #     if move.task_ids:
    #         for orig_move in orig_moves:
    #             for task in orig_move.task_ids:
    #                 self.link_predecessor_task(move.task_ids, task)
