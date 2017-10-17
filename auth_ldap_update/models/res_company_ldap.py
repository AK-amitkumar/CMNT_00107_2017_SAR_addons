# -*- coding: utf-8 -*-
from __builtin__ import filter

import ldap
import logging
import time
from odoo import models, tools, fields
from ldap.filter import filter_format
from urlparse import urlparse
from odoo.addons.alfresco_base_permissions.alfresco_permission import AlfrescoPermissions
from odoo.addons.cmis_field_4_all.cmis_field_4_all import EXCLUDED_MODELS

_logger = logging.getLogger(__name__)


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    ldap_group_base = fields.Char(string='LDAP group base', required=True)

    def update_ldap_user_password(self, conf, login, password):
        result = False
        try:
            filter = filter_format(conf['ldap_filter'], (login,))
        except TypeError:
            _logger.warning('Could not format LDAP filter. Your filter should contain one \'%s\'.')
            return False
        try:
            conn = self.connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            conn.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            user_dn = filter + "," + conf['ldap_base']
            login_value = password.encode("utf-8")
            add_login = [(ldap.MOD_REPLACE, "userPassword", [login_value])]
            result = conn.modify_s(user_dn, add_login)
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error('LDAP bind failed.')
            return False
        except ldap.LDAPError, e:
            _logger.error('An LDAP exception occurred: %s', e)
            return False
        return result
    
    def update_ldap_user_cn(self, conf, login, newlogin):
        result = False
        try:
            filter = filter_format(conf['ldap_filter'], (login,))
        except TypeError:
            _logger.warning('Could not format LDAP filter. Your filter should contain one \'%s\'.')
            return False
        try:
            conn = self.connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            conn.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            user_dn = filter + "," + conf['ldap_base']
            result = conn.modrdn_s(user_dn, "cn=" + newlogin)
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error('LDAP bind failed.')
            return False
        except ldap.LDAPError, e:
            _logger.error('An LDAP exception occurred: %s', e)
            return False
        return result

    def process_sync_user_groups(self):
        _logger.info("Starting Alfresco user groups sync")
        start = time.time()
        ldaps = self.env['res.company.ldap'].search([])
        groups = self.env['res.groups'].search([])
        users = self.env['res.users'].search([])
        for ldap in ldaps:
            for user in users:
                if user.ldap_sync :
                    ldap.create_ldap_user(ldap, user)
            for group in groups:
                ldap.sync_ldap_user_group(ldap, group)

        self.sync_alfresco_group_permissions()
        end = time.time()
        _logger.info("End Alfresco user groups sync " + str((end - start)))

    def sync_alfresco_group_permissions(self):
        models = self.env['ir.model'].search([])
        factory = self.env['alfresco.permission.service.factory']
        alfresco_service = factory.get_service()
        for model in models:
            model_name = model.model
            if model_name not in EXCLUDED_MODELS:
                if model_name == 'sale.order':
                    i = 0
                permissions = AlfrescoPermissions(model.access_ids)
                backends = self.env['cmis.backend'].search([])
                for backend in backends:
                    path = '/'.join([backend.initial_directory_write,
                                     model_name.replace('.', '_')])
                    store_id = backend.get_folder_by_path(path, create_if_not_found=True).id
                    url = urlparse(backend.location)
                    folder_permissions = alfresco_service.get_folder_permissions(url.hostname, str(url.port),
                                                                                 str(store_id),
                                                                                 (backend.username, backend.password))
                    permissions.merge_for_update(folder_permissions['direct'])
                    if permissions.has_permissions():
                        alfresco_service.set_folder_permissions(url.hostname, str(url.port), store_id, permissions,
                                                                (backend.username, backend.password))


    def sync_ldap_user_group(self, conf, group):
        result = False
        group_name = str(group.category_id.id) + '-' + group.name
        try:
            filter = filter_format("cn=%s", (group_name,))
        except TypeError:
            _logger.warning('Could not format LDAP filter. Your filter should contain one \'%s\'.')
            return False
        try:
            conn = self.connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            conn.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            result = conn.search_st(self.ldap_group_base, ldap.SCOPE_SUBTREE, filter)
            group_dn = filter + "," + self.ldap_group_base
            members = []
            for user in group.users:
                user_dn = filter_format(conf['ldap_filter'], (user.login,)) + "," + conf['ldap_base']
                members.append(user_dn.encode('utf-8'))
            if len(members) == 0:
                members = ['']
            if len(result) == 0:
                add_record = [
                    ('objectclass', ['groupOfNames', 'top']),
                    ('cn', [group_name.encode('utf-8')]),
                    ('member', members)
                ]
                result = conn.add_s(group_dn, add_record)
            else:
                if result[0][1]['member'] != members:
                    add_login = [(ldap.MOD_REPLACE, "member", members)]
                    result = conn.modify_s(group_dn, add_login)
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error('LDAP bind failed.')
            return False
        except ldap.LDAPError, e:
            _logger.error('An LDAP exception occurred: %s', e)
            return False
        return result

    def create_ldap_user(self, conf, user):
        result = False
        try:
            filter = filter_format(conf['ldap_filter'], (user.login,))
        except TypeError:
            _logger.warning('Could not format LDAP filter. Your filter should contain one \'%s\'.')
            return False
        try:
            conn = self.connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            conn.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            result = conn.search_st(conf['ldap_base'], ldap.SCOPE_SUBTREE, filter)
            if len(result) == 0:
                user_dn = filter + "," + conf['ldap_base']
                group = conn.search_st(conf['ldap_base'], ldap.SCOPE_SUBTREE)
                user_home = 'home/' + user.login
                add_record = [
                    ('objectclass', ['inetOrgPerson', 'posixAccount', 'top']),
                    ('cn', [user.login.encode('utf-8')]),
                    ('sn', [user.name.encode('utf-8')]),
                    ('uid', [user.login.encode('utf-8')]),
                    ('mail', [user.login.encode('utf-8')]),
                    ('gidNumber', group[0][1]['gidNumber']),
                    ('uidNumber', [str(user.id)]),
                    ('homeDirectory', [user_home.encode('utf-8')]),
                    ('userPassword', ['']),
                    ('description', [user.name.encode('utf-8')])
                ]
                result = conn.add_s(user_dn, add_record)
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error('LDAP bind failed.')
            return False
        except ldap.LDAPError, e:
            _logger.error('An LDAP exception occurred: %s', e)
            return False
        return result

