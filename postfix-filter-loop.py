# Author: Miroslav Houdek miroslav.houdek at gmail dot com
# License is, do whatever you wanna do with it (at least I think that that is what LGPL v3 says)
# Modified by: Koray YILMAZ kyilmaz at gmail dot com

import smtpd
import asyncore
import smtplib
import traceback
import logging
import os,sys,inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir + '/emailrelay-dlp')

import parse_msg
import params
from common import *
# import parse_msg and params from
# https://github.com/kyilmaz80/emailrelay-dlp postfix-python-filter branch


class CustomSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
        """
        processes the message
        :param peer: remote sender
        :param mailfrom: mail from header
        :param rcpttos: mail recipients
        :param data: message object as string
        :return:
        """

        mailfrom.replace('\'', '')
        mailfrom.replace('\"', '')

        for recipient in rcpttos:
            recipient.replace('\'', '')
            recipient.replace('\"', '')

        logging.info('Receiving message from: %s', peer)
        logging.info('Message addressed from: %S', mailfrom)
        logging.info('Message addressed to  %s:', rcpttos)
        logging.info('MSG >>')
        logging.info(data)
        logging.info('>> EOT')

        try:
            # DO WHAT YOU WANNA DO WITH THE EMAIL HERE
            # In future I'd like to include some more functions for users convenience, 
            # such as functions to change fields within the body (From, Reply-to etc), 
            # and/or to send error codes/mails back to Postfix.
            # Error handling is not really fantastic either.
            DLP_DETECTED = False
            # TODO: add timestamp to msg_file
            # TODO: rewrite parse_msg to parse from string. DONE: in parse_msg.py 1.0.5 version
            email_message = parse_msg.EmailMessage(message_string=data)
            ret = email_message.search_leaks()
            if ret != 0:
                DLP_DETECTED = True
            # pass
        except:
            pass
            logging.error('Something went south')
            logging.error(traceback.format_exc())

        try:
            if DLP_DETECTED == False:
                server = smtplib.SMTP(REMOTE_POSTFIX_IP, REMOTE_POSTFIX_PORT)
                server.sendmail(mailfrom, rcpttos, data)
                server.quit()
                # print('send successful')
            else:
                logging.warning("DLP content found on message!")
                logging.info("Archiving the message in " + params.FILTER_QUEUE_PATH)
                fname = email_message.message_id
                email_message.export_message(params.FILTER_QUEUE_PATH + '/' + clean_str(fname) + '.eml')
        except smtplib.SMTPException:
            logging.error('Exception SMTPException')
            pass
        except smtplib.SMTPServerDisconnected:
            logging.error('Exception SMTPServerDisconnected')
            pass
        except smtplib.SMTPResponseException:
            logging.error('Exception SMTPResponseException')
            pass
        except smtplib.SMTPSenderRefused:
            logging.error('Exception SMTPSenderRefused')
            pass
        except smtplib.SMTPRecipientsRefused:
            logging.error('Exception SMTPRecipientsRefused')
            pass
        except smtplib.SMTPDataError:
            logging.error('Exception SMTPDataError')
            pass
        except smtplib.SMTPConnectError:
            logging.error('Exception SMTPConnectError')
            pass
        except smtplib.SMTPHeloError:
            logging.error('Exception SMTPHeloError')
            pass
        except smtplib.SMTPAuthenticationError:
            logging.error('Exception SMTPAuthenticationError')
            pass
        except:
            logging.error('Undefined exception')
            print(traceback.format_exc())

        return

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - \
                                                %(threadName)s - %(message)s',
                        filename='/tmp/postfix-filter.log',
                        filemode='a', level=logging.DEBUG)
    FILTER_SERVER_IP = params.LHOST
    REMOTE_POSTFIX_IP = params.RHOST
    REMOTE_POSTFIX_PORT = params.RPORT
    FILTER_SERVER_PORT = params.LPORT

    logging.info('------------------------------------------')
    logging.info('Server is waiting for data on %s IP port: %s',FILTER_SERVER_IP, FILTER_SERVER_PORT)
    server = CustomSMTPServer((FILTER_SERVER_IP, FILTER_SERVER_PORT), None)
    asyncore.loop()
