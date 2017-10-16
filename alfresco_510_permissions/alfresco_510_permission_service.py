# -*- coding: utf-8 -*-

from odoo import models
from odoo.addons.alfresco_base_permissions import alfresco_permission_service_factory
import requests
import json


class Alfresco510PermissionService(models.AbstractModel):
    _name = 'alfresco.510.permission.service'
    _inherit = 'alfresco.permission.service'

    def get_folder_permissions(self, ip, port, store_id, auth):
        url = 'http://' + ip + ':' + port + '/alfresco/service/slingshot/doclib/permissions/workspace/SpacesStore/' + store_id
        r = requests.get(url, auth=auth)
        r.raise_for_status()
        permissions = json.loads(r.text)
        return permissions

    def set_folder_permissions(self, ip, port, store_id, permissions, auth):
        url = 'http://' + ip + ':' + port + '/alfresco/service/slingshot/doclib/permissions/workspace/SpacesStore/' +\
              store_id

        perm = {
            'permissions': permissions.permissions,
            'isInherited': False
        }
        r = requests.post(url, json=perm, auth=auth)
        r.raise_for_status()

alfresco_permission_service_factory.ALFRESCO_PERMISSION_SERVICES.append((Alfresco510PermissionService._name,
                                                                         'Alfresco 5.1.0 Permission Service'))
