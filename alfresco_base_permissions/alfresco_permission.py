# -*- coding: utf-8 -*-
import logging

ALFRESCO_ROLES = dict(CONSUMER='Consumer', CONTRIBUTOR='Contributor', EDITOR='Editor', COLLABORATOR='Collaborator',
                      COORDINATOR='Coordinator')

ALFRESCO_ROLE_FLAGS = dict(CONSUMER=1, CONTRIBUTOR=3, EDITOR=5, COLLABORATOR=7, COORDINATOR=15)
_logger = logging.getLogger(__name__)


class AlfrescoPermissions(object):

    def __init__(self, model_access_list):
        self.isInherited = False
        self.permissions = []
        for model_access in model_access_list:
            group = model_access.group_id
            if group:
                authority = 'GROUP_' + str(group.category_id.id) + '-' + group.name
                flag = (1 if model_access.perm_read else 0) | \
                       (2 if model_access.perm_create else 0) | \
                       (4 if model_access.perm_write else 0) | \
                       (8 if model_access.perm_unlink else 0)
                role = ''
                if (ALFRESCO_ROLE_FLAGS['COORDINATOR'] & flag) == ALFRESCO_ROLE_FLAGS['COORDINATOR']:
                    role = ALFRESCO_ROLES['COORDINATOR']
                elif (ALFRESCO_ROLE_FLAGS['COLLABORATOR'] & flag) == ALFRESCO_ROLE_FLAGS['COLLABORATOR']:
                    role = ALFRESCO_ROLES['COLLABORATOR']
                elif (ALFRESCO_ROLE_FLAGS['EDITOR'] & flag) == ALFRESCO_ROLE_FLAGS['EDITOR']:
                    role = ALFRESCO_ROLES['EDITOR']
                elif (ALFRESCO_ROLE_FLAGS['CONTRIBUTOR'] & flag) == ALFRESCO_ROLE_FLAGS['CONTRIBUTOR']:
                    role = ALFRESCO_ROLES['CONTRIBUTOR']
                elif (ALFRESCO_ROLE_FLAGS['CONSUMER'] & flag) == ALFRESCO_ROLE_FLAGS['CONSUMER']:
                    role = ALFRESCO_ROLES['CONSUMER']
                if role:
                    permission = {
                        'authority': authority,
                        'role': role
                    }
                    self.permissions.append(permission)

    def merge_for_update(self, current_permissions):
        for perm in current_permissions:
            permission = {
                'authority': perm['authority']['name'],
                'role': perm['role'],
            }
            if permission not in self.permissions:
                permission['remove'] = True
                self.permissions.append(permission)

    def has_permissions(self):
        return True if len(self.permissions) > 0 else False
