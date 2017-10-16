# -*- coding: utf-8 -*-
from odoo import models, fields
from .. import alfresco_permission_service_factory


class Company(models.Model):
    _inherit = 'res.company'

    alfresco_permission_service = fields.Selection(alfresco_permission_service_factory.ALFRESCO_PERMISSION_SERVICES,
                                                   string="Alfresco Permission Service")
