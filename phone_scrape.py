#!/usr/bin/python

##TODO: keep track of progress downloading mail

#TODO:fix the "downloads attachments" bug ;)
### helper for converting string to a number
def num (s):
    try:
        return int(s)
    except ValueError:
        return float(s)
    

def uniqify(seq, idfun=None):  
  return list(set(map(idfun, seq)))


### formatting the timestamp on the messages
import datetime
import rfc822 # deprecated in python3

###  benchmarking: how long does it take for the script to run?
import time
script_start_time = time.time()

 
#### connecting to mysql
import MySQLdb
#import oursql
conn = MySQLdb.connect(host='localhost', user='root', passwd='', db='dijscrape')
#conn = oursql.connect(host='localhost', user='root', db='dijscrape', port=3306)
curs = conn.cursor()

#### settings ####
user_email_address = 'foobar@gmail.com'
user_email_pw = 'foobar'

user_email_address = 'felix1265@gmail.com'
user_email_pw = 'helloworld12345'
#####################################
### extracting the phone numbers ###
################# thanks to this thread: http://stackoverflow.com/questions/123559/a-comprehensive-regex-for-phone-number-validation
import re
nanp_pattern = '(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'
number_re = re.compile(nanp_pattern)
email_re = re.compile('("?([a-zA-Z 0-9\._\-]+)"?\s+)?<?([a-zA-Z0-9\._\-]+@[a-zA-Z0-9\._\-]+)>?')

#################
import imaplib #for processing the IMAP mbox
################ 

################ 
from email.parser import HeaderParser # for processing the email into a dictionary
parser = HeaderParser() # we'll instantiate it now 
################

### connecting to google ###
print 'Connecting to the Google IMAP server'
server= imaplib.IMAP4_SSL('imap.googlemail.com')
server.login(user_email_address, user_email_pw)
#resp, gmail_all_mail_message_count_list = server.select('[Gmail]/All Mail', readonly=True)
resp, gmail_all_mail_message_count_list = server.select()
gmail_all_mail_message_count = num(gmail_all_mail_message_count_list[0])
print "Messages to process:", gmail_all_mail_message_count

## retrieving all messages ##
response, list_of_messages = server.search(None, 'ALL')

import sys

## going through each message one by one ##
for message_num in list_of_messages[0].split():
  print 'processing message num: ' + str(message_num)
  try:
    response, message_data = server.fetch(message_num, '(BODY.PEEK[HEADER])') 
  except:
    continue
  raw_message = message_data[0][1] # message_data, the data structure returned by imaplib, encodes some data re: the request type
  header = parser.parsestr(raw_message)
  if header['Content-Type'] is not None and 'multipart' in header['Content-Type']:
    continue # right now we're just skipping any multipart messages. this needs to be rewritten to parse the text parts of said messgs.
  try:
    response, message_data = server.fetch(message_num, '(BODY.PEEK[TEXT])') 
  except:
    continue
  text_payload = message_data[0][1] 
  found_digits = number_re.findall(text_payload)
  if found_digits!=[]:
    print "Message %d has numbers. We are %f%% complete with processing your mail." % (num(message_num), 100*(num(message_num)/gmail_all_mail_message_count))
    print found_digits
    ### need to cast the Date header into a MySQL object. 
    ts = header['Date']
    print 'header date: ' + str(ts)
    if rfc822.parsedate_tz(ts) is not None: #making sure the date header is not empty
      ts_tuple = rfc822.parsedate_tz(ts)
    #perhaps in the future we can intead set the ts_tuple to (0,0,0,0,0,0,0) and interpret it in the UI as 'no date header'. assuming that is actually the problem.
    #otherwise, we're setting it to the date of the most recently received email... and this could get awkward. #TODO: fix this once the UI is ready.
    ts_python_datetime = datetime.datetime(*(ts_tuple[0:6]))
    ts_mysql_datetime = ts_python_datetime.isoformat(' ')

    print 'about to insert into the database'
    ### sometimes it fails due to unicode issues
    try:
        print 'about to parse name and email from header'
        print 'header: ' + str(header['From'])
        name, email = email_re.match(header['From']).groups()[1:3]
        print 'parsing name and email from FROM header: ' + str(name) + ', ' + str(email)
        curs.execute('''INSERT INTO messages
          (sender,recipient,sender_name,sender_email,subject,msg_date,payload)
          VALUES
          (?,?,?,?,?,?,?)
          ''',
          (header['From'],header['To'],name,email,header['Subject'],ts_mysql_datetime,text_payload[0:65534]))
        message_id_local_mysql = curs.lastrowid
        print 'saved as msg id ' + str(message_id_local_mysql)
        
        pure_digits = uniqify(map(''.join, found_digits)) # the phone number regexp will create lists like ['','650','555','1212']. this collapses the list into a string. 

        print 'We found pure digits: ' + str(pure_digits)
        for phone_number in pure_digits:
          if len(str(phone_number))>7:  # for now, we want numbers with area codes only.
            print phone_number
            curs.execute('''INSERT INTO phone_numbers
            (message_id, phone_number)
            VALUES
            (?,?)
            ''',
            (message_id_local_mysql,phone_number))
    except:
        print "Unexpected error:", sys.exc_info()[0]
        pass

script_end_time = time.time()
elapsed_seconds= script_end_time - script_start_time
elapsed_minutes = elapsed_seconds/60

print "The script took", elapsed_seconds, "seconds to run, which is the same as", elapsed_minutes, "minutes"
print gmail_all_mail_message_count, "messages were processed"

curs.close()
conn.commit()
conn.close()
