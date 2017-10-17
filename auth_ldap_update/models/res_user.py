# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class Users(models.Model):
    _inherit = "res.users"

    ldap_sync = fields.Boolean(default=False)

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``ldap_sync`` on the records in ``self``. """
        for record in self:
            record.ldap_sync = not record.ldap_sync

    @api.multi
    def write(self, values):
        if self.ldap_sync:
            if 'login' in values:
                ldap = self.env['res.company.ldap']
                for conf in ldap.get_ldap_dicts():
                    if ldap.update_ldap_user_cn(conf, self.login, values['login']):
                        break
            if 'password' in values:
                self._check_concurrency()
                self.check_access_rights('write')
                ldap = self.env['res.company.ldap']
                for conf in ldap.get_ldap_dicts():
                    if ldap.update_ldap_user_password(conf, self.login, values['password']):
                        values.pop("password")
                        break

        res = super(Users, self).write(values)
        if 'ldap_sync' in values and values['ldap_sync']:
            ldap = self.env['res.company.ldap']
            for conf in ldap.get_ldap_dicts():
                if ldap.create_ldap_user(conf, self):
                    break
        return res
