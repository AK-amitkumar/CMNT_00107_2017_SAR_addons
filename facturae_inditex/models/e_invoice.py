# -*- coding: utf-8 -*-
import logging
import datetime
import smtplib
import email
import time
try:
    import pysftp
except ImportError:
    raise ImportError(
        'This module needs pysftp to push einvoice through SFTP.Please install pysftp on your system.'
        '(sudo pip install pysftp)'
    )

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from poplib import POP3_SSL
from lxml import etree


from odoo import models, _, api
from odoo.addons.l10n_es_base_facturae.models.e_invoice import FILE_NAME_STRATEGY, REPORT_TEMPLATE, SIGN_STRATEGY,\
    PUSH_STRATEGY
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MAIL_TIMEOUT=60

FILE_NAME_STRATEGY.append(('inditex', 'Iditex B2B'))
REPORT_TEMPLATE.append(('facturae_inditex.report_facturae_inditex', 'Factura-e Inditex'))
SIGN_STRATEGY.append(('camerfirma', 'Camerfirma'))
PUSH_STRATEGY.append(('inditex', 'Iditex B2B'))


class EInvoice(models.Model):
    _inherit = "e.invoice"

    def _set_file_name(self):
        if self.file_name_strategy == 'inditex':
            self.e_invoice_file_name = self.invoice_id.partner_id.seller_party_id + '-PRODUCT_INVOICE-' + \
                                       self.invoice_id.company_id.partner_id.vat + \
                                       self.invoice_id.number.replace("/","") + '-I-' + \
                                       datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.xml'
        else:
            super(EInvoice, self)._set_file_name()

    def _sign_invoice(self):
        if self.sign_strategy == 'camerfirma':
            self._synchronous_mail_sign()
        else:
            super(EInvoice, self)._sign_invoice()

    # CMNT mailt to Victor Rojo commented.
    # def _push_invoice(self):
    #     if self.push_strategy == 'inditex':
    #         self._synchronous_sftp_push()
    #     else:
    #         super(EInvoice, self)._push_invoice()

    # def _process_signed_xml(self, signed):
    #     for filename, data in signed.iteritems():
    #         einvoice = self.search([('e_invoice_file_name', '=', filename), ('state', '=', 'unsigned')], limit=1)
    #         einvoice.e_invoice_data = data
    #         einvoice.state = 'signed'

    def _process_push_response(self, received):
        for filename, data in received.iteritems():
            source_file_name = filename.replace("-V-", "-I-")
            einvoice = self.search([('e_invoice_file_name', '=', source_file_name),
                                    ('state', 'in', ('sent', 'error'))], limit=1)
            einvoice.response_data = data
            xml = etree.fromstring(data, etree.XMLParser(remove_blank_text=True, strip_cdata=False))
            root_tag = xml.tag
            if root_tag == "Invoice":
                einvoice.state = 'done'
            else:
                einvoice.state = 'error'

    def _send_to_sign_ca(self):
        # cmnt review
        smtp_host = "smtp.gmail.com"
        smtp_port = "587"
        smtp_user = "srn.pop.test@gmail.com"
        smtp_password = "10gtsvsl11"
        sign_mail_to = "victor.rojo@saroni.info"

        # smtp_host = "smtp.gmail.com"
        # smtp_port = "587"
        # smtp_user = "facturae@gruposaroni.com"
        # smtp_password = "10gtsvsl11"
        # sign_mail_to = "facturity@cc3m.com"

        smtp = None

        for einvoice in self:
            try:
                smtp = smtplib.SMTP(smtp_host, smtp_port)
                msg = MIMEMultipart()
                msg['Subject'] = "FACTURAE DE PLE: " + (einvoice.invoice_id.ple_number or '')
                msg['From'] = smtp_user
                msg['To'] = sign_mail_to
                part = MIMEBase('application', "xml")
                part.set_payload(einvoice.e_invoice_data.encode('utf-8'))
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="' + einvoice.e_invoice_file_name + '"')
                msg.attach(part)

                # starttls() will perform ehlo() if needed first
                # and will discard the previous list of services
                # after successfully performing STARTTLS command,
                # (as per RFC 3207) so for example any AUTH
                # capability that appears only on encrypted channels
                # will be correctly detected for next step
                smtp.starttls()

                # Attempt authentication - will raise if AUTH service not supported
                # The user/password must be converted to bytestrings in order to be usable for
                # certain hashing schemes, like HMAC.
                # See also bug #597143 and python issue #5285
                smtp.login(smtp_user.encode('utf-8'), smtp_password.encode('utf-8'))
                smtp.sendmail(smtp_user, sign_mail_to, msg.as_string())
            except Exception as e:
                msg = _("Mail delivery failed via SMTP server '%s'\n%s: %s") % (
                    smtp_host, e.__class__.__name__, unicode(e))
                _logger.warning(msg)
                raise UserError(_("Mail Delivery Failed") + msg)
            finally:
                if smtp is not None:
                    smtp.quit()

    def _receive_from_ca(self):
        # pop_host = "pop.gmail.com"
        # pop_port = 995
        # pop_user = "srn.pop.test@gmail.com"
        # pop_password = "10gtsvsl11"


        pop_host = "pop.gmail.com"
        pop_port = 995
        pop_user = "facturae@gruposaroni.com"
        pop_password = "10gtsvsl11"

        signed = {}
        timeout = time.time() + 60*5
        pop = None
        while not signed.has_key(self.e_invoice_file_name):
            try:
                pop = POP3_SSL(pop_host, pop_port)
                pop.user(pop_user)
                pop.pass_(pop_password)
                pop.sock.settimeout(MAIL_TIMEOUT)
                messages = [pop.retr(i) for i in range(1, len(pop.list()[1]) + 1)]
                messages = ["\n".join(mssg[1]) for mssg in messages]
                messages = [email.message_from_string(mssg) for mssg in messages]
                for message in messages:
                    for part in message.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue

                        if part.get('Content-Disposition') is None:
                            print("no content dispo")
                            continue

                        filename = part.get_filename()
                        file_data = part.get_payload(decode=1)
                        signed[filename] = file_data
            except Exception as e:
                msg = _("General failure when trying to fetch mail from %s server\n%s: %s") % (
                    pop_host, e.__class__.__name__, unicode(e))
                _logger.warning(msg)
                raise UserError(_("Mail Fetch Failed") + msg)
            finally:
                if pop is not None:
                    pop.quit()
            if time.time() > timeout:
                break
            time.sleep(5)
        if not signed.has_key(self.e_invoice_file_name):
            raise UserError(_("Timeout receiving signed xml for ") + self.e_invoice_file_name)
        self._process_signed_xml(signed)

    def _send_to_sftp(self):
        # cmnt review
        sftp_host = '172.16.10.53'
        sftp_port = 22
        sftp_user = 'root'
        sftp_password = 'neoncss'

        # sftp_host = 'b2btest.inditex.com'
        # sftp_port = 22
        # sftp_user = 'FEB2BPREPR730916'
        # sftp_password = 'BgHqJ16K'

        sftp = None
        remote_file = None
        file_name = self.e_invoice_file_name
        file_path = 'SUPPLIERtoINDITEX/' + file_name
        try:
            sftp = pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_user, password=sftp_password)
            remote_file = sftp.open(remote_file=file_path, mode='w')
            remote_file.write(self.e_invoice_data.encode('utf-8'))
            self.state = 'sent'
        except Exception as e:
            msg = _("General failure when trying to push file to %s server\n%s: %s") % (
                sftp_host, e.__class__.__name__, unicode(e))
            _logger.warning(msg)
            raise UserError(_("Mail Fetch Failed") + msg)
        finally:
            if remote_file is not None:
                remote_file.close
            if sftp is not None:
                sftp.close()

    def _receive_from_sftp(self):
        sftp_host = '172.16.10.53'
        sftp_port = 22
        sftp_user = 'root'
        sftp_password = 'neoncss'

        sftp = None
        remote_file = None
        timeout = time.time() + 60 * 5
        file_name = self.e_invoice_file_name.replace("-I-", "-V-")
        file_path = 'INDITEXtoSUPPLIER/' + file_name
        received = {}

        while not received.has_key(file_name):
            try:
                sftp = pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_user, password=sftp_password)
                if sftp.exists(file_path):
                    remote_file = sftp.open(remote_file=file_path, mode='r')
                    data = remote_file.read()
                    received[file_name] = data
            except Exception as e:
                msg = _("General failure when trying to push file to %s server\n%s: %s") % (
                    sftp_host, e.__class__.__name__, unicode(e))
                _logger.warning(msg)
                raise UserError(_("Mail Fetch Failed") + msg)
            finally:
                if remote_file is not None:
                    remote_file.close
                if sftp is not None:
                    sftp.close()
            if time.time() > timeout:
                break
            time.sleep(5)
        if not received.has_key(file_name):
            raise UserError(_("Timeout receiving response xml for ") + self.e_invoice_file_name)
        self._process_push_response(received)

    def _synchronous_mail_sign(self):
        self._send_to_sign_ca()
        self._receive_from_ca()

    def _synchronous_sftp_push(self):
        self._send_to_sftp()
        self._receive_from_sftp()
