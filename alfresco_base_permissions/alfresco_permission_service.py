# -*- coding: utf-8 -*-

from odoo import models


class AlfrescoPermissionService(models.AbstractModel):
    _name = 'alfresco.permission.service'

    def get_folder_permissions(self, ip, port, store_id, auth):
        pass

    def set_folder_permissions(self, ip, port, store_id, permissions, auth):
        pass
