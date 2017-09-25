# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, modules, _
from odoo.exceptions import ValidationError


class TrackingWip(models.Model):
    """ Inherits partner and adds Tasks information in the partner form """
    _name = 'tracking.wip'

    name = fields.Char('Name', required=True)
    model_id = fields.Many2one('ir.model', 'Model to track', required=True)
    condition_eval = fields.Text('Condition', required=True)
    project_eval = fields.Text('Project')
    name_eval = fields.Text('Task Name')
    start_date_eval = fields.Text('Start Date')
    end_date_eval = fields.Text('End Date')
    state = fields.Selection([('deactivated', 'Deactivated'),
                              ('active', 'Active')], 'State',
                             default='deactivated')

    def _check_asset_categ(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        for account in self.browse(cr, uid, ids, context=context):
            if account.asset_category_id and \
                    account.asset_category_id.account_asset_id != account:
                return False
        return True

    @api.multi
    @api.constrains('model_id')
    def check_related_model_task_id(self):
        for track in self:
            model_name = self.model_id.model
            if not hasattr(self.env[model_name], 'task_id'):
                raise ValidationError(_(
                    "The selected model can not be tracked because is not "
                    "related rith task model"))

    def _register_hook(self):
        """
        Apply patches in the actived rule models.
        """
        super(TrackingWip, self)._register_hook()
        if not self:
            self = self.search([('state', '=', 'active')])
        return self._patch_methods()

    @api.model
    def create(self, vals):
        """ Update the hooks when a new track is created."""
        new_record = super(TrackingWip, self).create(vals)
        # Used with multiprocess
        if new_record._register_hook():
            modules.registry.RegistryManager.signal_registry_change(
                self.env.cr.dbname)
        return new_record

    @api.multi
    def write(self, vals):
        """ Update the hooks when a new track is writed."""
        res = super(TrackingWip, self).write(vals)
        # Used with multiprocess
        if self._register_hook():
            modules.registry.RegistryManager.signal_registry_change(
                self.env.cr.dbname)
        return res

    @api.multi
    def unlink(self):
        """ Restore Monkey-patching to original methods"""
        self.deactivate()
        return super(TrackingWip, self).unlink()

    @api.multi
    def _patch_methods(self):
        for track in self:
            # Avoid deactived tracking models
            if track.state == 'deactived':
                continue
            track_model = self.env[track.model_id.model]
            track_model._patch_method('create', track._make_create())
            track_model._patch_method('write', track._make_write())
            track_model._patch_method('unlink', track._make_unlink())
        return True

    @api.multi
    def _revert_methods(self):
        """ Restore original ORM methods of models defined in tracks. """
        updated = False
        for track in self:
            model_model = self.env[track.model_id.model]
            for method in ['create', 'write', 'unlink']:
                if hasattr(getattr(model_model, method), 'origin'):
                    model_model._revert_method(method)
                    updated = True
        # When using multiproces
        if updated:
            modules.registry.RegistryManager.signal_registry_change(
                self.env.cr.dbname)

    @api.model
    def get_track_for_model(self, model_name):
        domain = [('model_id.model', '=', model_name),
                  ('state', '=', 'active')]
        track_record = self.search(domain)
        return track_record

    @api.multi
    def do_task_tracking(self, record):
        """
        If a eval condition is true and not task created, create a task
        """
        self.ensure_one()
        if eval(self.condition_eval) and not record.task_id:
            vals = {
                'name': eval(self.name_eval),
                'project_id': eval(self.project_eval),
                'date_start': eval(self.start_date_eval),
                'date_end': eval(self.end_date_eval),
                'model_reference': record._name + ',' + str(record.id)
            }
            self.env['project.task'].create(vals)

    @api.multi
    def _make_create(self):
        @api.model
        def my_create(self, vals, **kwargs):
            print "*********************************************"
            print "MY CREATE"
            print "*********************************************"
            track_model = self.env['tracking.wip']
            res = my_create.origin(self, vals, **kwargs)
            track_record = track_model.get_track_for_model(self._name)
            if track_record:
                track_record.do_task_tracking(res)
            return res

        return my_create

    @api.multi
    def _make_write(self):
        @api.multi
        def my_write(self, vals, **kwargs):
            print "*********************************************"
            print "MY WRITE"
            print "*********************************************"
            res = my_write.origin(self, vals, **kwargs)

            return res

        return my_write

    @api.multi
    def _make_unlink(self):
        @api.multi
        def my_unlink(self, **kwargs):
            print "*********************************************"
            print "MY UNLINK"
            print "*********************************************"
            res = my_unlink.origin(self, **kwargs)

            return res

        return my_unlink

    @api.multi
    def deactivate(self):
        self._revert_methods()
        self.write({'state': 'deactivated'})
        return True

    @api.multi
    def activate(self):
        self.write({'state': 'active'})
        return True
