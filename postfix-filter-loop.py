# Author: Miroslav Houdek miroslav.houdek at gmail dot com
# License is, do whatever you wanna do with it (at least I think that that is what LGPL v3 says)
# Modified by: Koray YILMAZ kyilmaz at gmail dot com

import smtpd
import asyncore
import smtplib
import traceback
import parse_msg
import params

# import parse_msg and params from
# https://github.com/kyilmaz80/emailrelay-dlp postfix-python-filter branch


class CustomSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
        
        mailfrom.replace('\'', '')
        mailfrom.replace('\"', '')
        
        for recipient in rcpttos:
            recipient.replace('\'', '')
            recipient.replace('\"', '')
        
        print('Receiving message from:', peer)
        print('Message addressed from:', mailfrom)
        print('Message addressed to  :', rcpttos)
        print('MSG >>')
        print(data)
        print('>> EOT')
        

        try:
            # DO WHAT YOU WANNA DO WITH THE EMAIL HERE
            # In future I'd like to include some more functions for users convenience, 
            # such as functions to change fields within the body (From, Reply-to etc), 
            # and/or to send error codes/mails back to Postfix.
            # Error handling is not really fantastic either.
            DLP_DETECTED = False
            # TODO: add timestamp to msg_file
            # TODO: rewrite parse_msg to parse from string
            msg_file = '/tmp/message'
            with open(msg_file, 'w') as fp:
                fp.write(data)
            ret = parse_msg.main(msg_file)
            if ret != 0:
                DLP_DETECTED = True
            # pass
        except:
            pass
            print('Something went south')
            print(traceback.format_exc())

        try:
            if DLP_DETECTED == False:
                server = smtplib.SMTP(REMOTE_POSTFIX_IP, REMOTE_POSTFIX_PORT)
                server.sendmail(mailfrom, rcpttos, data)
                server.quit()
                # print('send successful')
            else:
                print("DLP content found on message!")
        except smtplib.SMTPException:
            print('Exception SMTPException')
            pass
        except smtplib.SMTPServerDisconnected:
            print('Exception SMTPServerDisconnected')
            pass
        except smtplib.SMTPResponseException:
            print('Exception SMTPResponseException')
            pass        
        except smtplib.SMTPSenderRefused:
            print('Exception SMTPSenderRefused')
            pass        
        except smtplib.SMTPRecipientsRefused:
            print('Exception SMTPRecipientsRefused')
            pass        
        except smtplib.SMTPDataError:
            print('Exception SMTPDataError')
            pass        
        except smtplib.SMTPConnectError:
            print('Exception SMTPConnectError')
            pass        
        except smtplib.SMTPHeloError:
            print('Exception SMTPHeloError')
            pass        
        except smtplib.SMTPAuthenticationError:
            print('Exception SMTPAuthenticationError')
            pass
        except:
            print('Undefined exception')
            print(traceback.format_exc())

        return

if __name__ == "__main__":
    
    FILTER_SERVER_IP = params.LHOST
    REMOTE_POSTFIX_IP = params.RHOST
    REMOTE_POSTFIX_PORT = params.RPORT
    FILTER_SERVER_PORT = params.LPORT
    server = CustomSMTPServer((FILTER_SERVER_IP, FILTER_SERVER_PORT), None)
    asyncore.loop()
