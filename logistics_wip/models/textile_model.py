# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class TextileModel(models.Model):

    _inherit = "textile.model"

    project_id = fields.Many2one("project.project", "Project", readonly=True,
                                 copy=False)

    @api.multi
    def action_approve(self):
        res = super(TextileModel, self).action_approve()
        if self.model_type == 'model':
            project = self.env["project.project"].\
                create({'name': u'[' + self.reference + u'] ' + self.name,
                        'label_tasks': 'Eventos',
                        'partner_id': self.customer.id,
                        'code': self.reference,
                        'tag_ids': [(6, 0, [self.analytic_tag.id])]})
            self.project_id = project.id
        return res
