# -*- coding: utf-8 -*-

from odoo import models

ALFRESCO_PERMISSION_SERVICES = []


class AlfrescoPermissionServiceFactory(models.AbstractModel):
    _name = 'alfresco.permission.service.factory'

    def get_service(self):
        company = self.env.user.company_id
        if company is not None:
            service = company.alfresco_permission_service
            service = self.env[service]
            return service
        raise Exception('Alfresco Permission Service Fail!')
