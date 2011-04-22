#TODO:fix the "downloads attachments" bug ;)
### helper for converting string to a number
def num (s):
    try:
        return int(s)
    except exceptions.ValueError:
        return float(s)



def uniqify(seq, idfun=None):  
	if idfun is None: 
		def idfun(x): return x 
	seen = {} 
	result = [] 
	for item in seq: 
		marker = idfun(item) 
		if marker in seen: continue 
		seen[marker] = 1 
		result.append(item) 
	return result


### formatting the timestamp on the messages
import datetime
import rfc822 # deprecated in python3

###  benchmarking: how long does it take for the script to run?
import time
script_start_time = time.time()


#### settings ####
user_email_address = 'username_email_address'
user_email_pw = 'setme'

#####################################
### extracting the phone numbers ###
################# thanks to this thread: http://stackoverflow.com/questions/123559/a-comprehensive-regex-for-phone-number-validation
import re
nanp_pattern = '(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'
number_re = re.compile(nanp_pattern)

#################
import imaplib #for processing the IMAP mbox
################ 

################ 
from email.parser import HeaderParser # for processing the header into a dictionary
parser = HeaderParser() # we'll instantiate it now 
################

### connecting to google ###
print 'Connecting to the Google IMAP server'
server= imaplib.IMAP4_SSL('imap.googlemail.com')
server.login(user_email_address, user_email_pw)
resp, gmail_all_mail_message_count_list = server.select('[Gmail]/All Mail')
gmail_all_mail_message_count = num(gmail_all_mail_message_count_list[0])
print "Messages to process:", gmail_all_mail_message_count

## retrieving all messages ##
response, list_of_messages = server.search(None, 'ALL')

