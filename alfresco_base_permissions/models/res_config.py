# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class BaseConfigSettings(models.TransientModel):
    _inherit = "base.config.settings"

    alfresco_permission_service = fields.Selection(related='company_id.alfresco_permission_service',
                                                   string="Alfresco Permission Service")
