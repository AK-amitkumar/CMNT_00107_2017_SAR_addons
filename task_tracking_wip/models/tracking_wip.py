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
                return track
        return False

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
        if task_recs:
            vals = {
                'parent_task_id': o.task_id.id,
                'type': 'FS'
            }
            task_recs.write({
                'predecessor_ids': [(0, 0, vals)]
            })
        return

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
                date_start = o.order_id.create_date
                date_end = o.order_id.commitment_date
            elif o._name == 'stock.move':
                date_start = o.date_expected
                date_end = o.date_expected
            vals = {
                'name': eval(self.name_eval),
                'project_id': eval(self.project_eval),
                'date_start': date_start,
                'date_end': date_end if date_end > date_start else date_start,
                'model_reference': o._name + ',' + str(o.id)
            }
            task_obj = self.env['project.task'].create(vals)
            o.write({'task_id': task_obj.id})

            if o._name == 'stock.move':
                self.set_move_task_dependencies(o)

# ----------------------------------------------------------------------------#
# -------------------------- MONKEY-PATCHING ---------------------------------#
# ----------------------------------------------------------------------------#
    # def _register_hook(self):
    #     """
    #     Apply patches in the actived rule models. Called always in load
    #      module
    #     """
    #     super(TrackingWip, self)._register_hook()
    #     if not self:
    #         self = self.search([('state', '=', 'active')])
    #     return self._patch_methods()

    # @api.model
    # def create(self, vals):
    #     """ Update the hooks when a new track is created."""
    #     new_record = super(TrackingWip, self).create(vals)
    #     # Used with multiprocess
    #     if new_record._register_hook():
    #         modules.registry.RegistryManager.signal_registry_change(
    #             self.env.cr.dbname)
    #     return new_record

    # @api.multi
    # def write(self, vals):
    #     """ Update the hooks when a new track is writed."""
    #     res = super(TrackingWip, self).write(vals)
    #     # Used with multiprocess
    #     if self._register_hook():
    #         modules.registry.RegistryManager.signal_registry_change(
    #             self.env.cr.dbname)
    #     return res

    # @api.multi
    # def unlink(self):
    #     """ Restore Monkey-patching to original methods"""
    #     self.deactivate()
    #     return super(TrackingWip, self).unlink()

    # @api.multi
    # def _patch_methods(self):
    #     for track in self:
    #         # Avoid deactived tracking models
    #         if track.state == 'deactived':
    #             continue
    #         track_model = self.env[track.model_id.model]
    #         track_model._patch_method('create', track._make_create())
    #         track_model._patch_method('write', track._make_write())
    #         track_model._patch_method('unlink', track._make_unlink())
    #     return True

    # @api.multi
    # def _revert_methods(self):
    #     """ Restore original ORM methods of models defined in tracks. """
    #     updated = False
    #     for track in self:
    #         model_model = self.env[track.model_id.model]
    #         for method in ['create', 'write', 'unlink']:
    #             if hasattr(getattr(model_model, method), 'origin'):
    #                 model_model._revert_method(method)
    #                 updated = True
    #     # When using multiproces
    #     if updated:
    #         modules.registry.RegistryManager.signal_registry_change(
    #             self.env.cr.dbname)

    # @api.multi
    # def write_task_tracking(self, o, vals):
    #     """
    #     If not task created, create a task and
    #     link it to record.
    #     """
    #     self.ensure_one()

    #     # Unlink task if model is cancelled
    #     if o.state == 'cancel' and o.task_id:
    #         o.task_id.unlink()

    #     # Update dates in the related task
    #     if o._name == 'stock.move' and 'date_expected' in vals and \
    #             o.task_id:
    #         o.task_id.write({'date_end': o.date_expected})

    # @api.multi
    # def _make_create(self):
    #     @api.model
    #     def my_create(self, vals, **kwargs):
    #         print "*********************************************"
    #         print "MY CREATE"
    #         print "*********************************************"
    #         track_model = self.env['tracking.wip']
    #         res = my_create.origin(self, vals, **kwargs)
    #         track_record = track_model.get_track_for_model(self._name, res)
    #         if track_record:
    #             track_record.create_task_tracking(res)
    #         return res
    #     return my_create

    # @api.multi
    # def _make_write(self):
    #     @api.multi
    #     def my_write(self, vals, **kwargs):
    #         print "*********************************************"
    #         print "MY WRITE"
    #         print "*********************************************"
    #         res = my_write.origin(self, vals, **kwargs)
    #         # track_model = self.env['tracking.wip']
            # track_record = track_model.get_track_for_model(self._name, self)
    #         # if track_record:
    #         #     track_record.write_task_tracking(self, vals)
    #         return res

    #     return my_write

    # @api.multi
    # def _make_unlink(self):
    #     @api.multi
    #     def my_unlink(self, **kwargs):
    #         print "*********************************************"
    #         print "MY UNLINK"
    #         print "*********************************************"
    #         res = my_unlink.origin(self, **kwargs)
    #         return res
    #     return my_unlink
