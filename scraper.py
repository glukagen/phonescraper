import threading
from multiprocessing import Process
import datetime
import rfc822
import time
import MySQLdb
import re
import imaplib
import sys
from oldsettings import *
from email.parser import HeaderParser
from utils import num, uniqify
import os


nanp_pattern = '(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'
number_re = re.compile(nanp_pattern)
email_re = re.compile('("?([a-zA-Z 0-9\._\-]+)"?\s+)?<?([a-zA-Z0-9\._\-]+@[a-zA-Z0-9\._\-]+)>?')


class Executer(threading.Thread):
    def __init__(self, message_number):
        threading.Thread.__init__(self)
        self.message_number = int(message_number)    
        
    def run(self):
        command = "python ./scraper.py %d" % self.message_number
        print command
        os.system(command)
        
        
class Analizer(threading.Thread):
    def __init__(self, imap, email, password, numbers):
        #Process.__init__(self)

        threading.Thread.__init__(self)
        self.numbers = numbers    
        print self.numbers
        self.imap = IMAPConnecter(email, password).getConnection()    
        self.conn = MySQLdb.connect(host=DBHOST, user=DBUSER, passwd=DBPASSWD, db=DBNAME)
        self.cursor = self.conn.cursor()
        
    def searchPhone(self, message_number):
        print 'processing message num: ' + str(message_number)
        try:
            response, message_data = self.imap.fetch(message_number, '(BODY.PEEK[HEADER])') 
        except:
            print "Exception in HEADER"
            #self.close()
            return False
        
        raw_message = message_data[0][1] # message_data, the data structure returned by imaplib, encodes some data re: the request type
        header = HeaderParser().parsestr(raw_message)
        if header['Content-Type'] is not None and 'multipart' in header['Content-Type']:
            print "INcorrect content type"
            #self.close()  
            return False # right now we're just skipping any multipart messages. this needs to be rewritten to parse the text parts of said messgs.
        try:
            response, message_data = self.imap.fetch(message_number, '(BODY.PEEK[TEXT])') 
        except:
            print "Exception in TEXT"
            print response
            print message_data
            #self.close()  
            return False
        
        text_payload = message_data[0][1] 
        found_digits = number_re.findall(text_payload)
        #print "FOUND DIGITS"
        #print found_digits
        if found_digits != []:
            print "Message %d has numbers." % num(message_number)
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
            #try:
            print 'about to parse name and email from header'
            print 'header: ' + str(header['From'])
            try:
                name, email = email_re.match(header['From']).groups()[1:3]
            except:
                print "Unexpected error:", sys.exc_info()[0]
                #self.close()  
                return False
            print 'parsing name and email from FROM header: ' + str(name) + ', ' + str(email)          
          
            
            query = '''INSERT INTO messages (sender, recipient, sender_name, sender_email, 
                subject, msg_date, payload) VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s") ''' % \
              (MySQLdb.escape_string(header['From']), 
               MySQLdb.escape_string(header['To']), 
               MySQLdb.escape_string(str(name)), 
               MySQLdb.escape_string(email), 
               MySQLdb.escape_string(header['Subject']), 
               MySQLdb.escape_string(ts_mysql_datetime), 
               MySQLdb.escape_string(text_payload[0:65534]))
            
            self.cursor.execute(query)
          
            message_id_local_mysql = self.cursor.lastrowid
            print 'saved as msg id ' + str(message_id_local_mysql)
            
            pure_digits = uniqify(map(''.join, found_digits)) # the phone number regexp will create lists like ['','650','555','1212']. this collapses the list into a string. 
            
            print 'We found pure digits: ' + str(pure_digits)
            for phone_number in pure_digits:
              if len(str(phone_number)) > 7:  # for now, we want numbers with area codes only.
                  print phone_number
                  query = 'INSERT INTO phone_numbers (message_id, phone_number) VALUES ("%s", "%s") ' % \
                  (message_id_local_mysql, MySQLdb.escape_string(phone_number))
                  self.cursor.execute(query)

        
    
    def run(self):
        for i in self.numbers:
            self.searchPhone(i)
        
        self.close()        
        return True
    
    def close(self):
        #self.imap.logout()
        #if self.conn:
        self.cursor.close()
        self.conn.commit()
        self.conn.close() 
        

class IMAPConnecter:
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.mailCount = 0   
        
    def getMailCount(self):
        return self.mailCount
    
    def getConnection(self):
        imap = imaplib.IMAP4_SSL('imap.googlemail.com')
        imap.login(self.email, self.password)
        self.response, mailCount = imap.select()
        self.mailCount = num(mailCount[0])
        #print imap
        return imap

class Scraper:
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.analizers = []
        
    def startThread(self, thread):
        while threading.activeCount() >= MAX_THREAD:
            pass        
        thread.start()    
                   
    def run(self):
        print 'Connecting to the Google IMAP server'
        conn = IMAPConnecter(self.email, self.password)
        imap = conn.getConnection()

        print "Messages to process:", conn.getMailCount()

        response, list_of_messages = imap.search(None, 'ALL')
        mlist = list_of_messages[0].split()
        for i in range(0, conn.getMailCount(), MESSAGE_COUNT_PER_THREAD):
            analizer = Analizer(imap, self.email, self.password, mlist[i: i + MESSAGE_COUNT_PER_THREAD])
            self.analizers.append(analizer)
            self.startThread(analizer)
        #first = mlist[:int(len(mlist)/3)]
        #second = mlist[int(len(mlist)/2):]
        
        #analizer = Analizer(imap, self.email, self.password, first)
        #self.analizers.append(analizer)
        
        #analizer = Analizer(imap, self.email, self.password, second)
        #self.analizers.append(analizer)
        
        #for analizer in self.analizers:
        #    analizer.start()
        """
        for message_num in list_of_messages[0].split():
            analizer = Analizer(imap, self.email, self.password, message_num)
            self.analizers.append(analizer)
            self.startThread(analizer)
            
            executer = Executer(message_num)
            self.executers.append(executer)
            self.startThread(executer)
        """
            
        for analizer in self.analizers:
            analizer.join()
            #command = "python ./scraper.py %d &" % int(message_num)
            #print command
            #os.system(command)
            #analizer = Analizer(imap, self.email, self.password, message_num)
            #self.analizers.append(analizer)
            #analizer.start()
            #self.startThread(analizer)
            #p = Process(target=fetch, args=(self.email, self.password, message_num,))
            #processes.append(p)
            #p.start()
        
        #for p in processes:
        #    p.join()
        #for analizer in self.analizers:
        #    analizer.join()


def main():
    if len(sys.argv) > 1: 
        Analizer(EMAIL, EMAIL_PASSWD, sys.argv[1]).run()
    else:
        Scraper(EMAIL, EMAIL_PASSWD).run()

if __name__ == '__main__':
    start_time = time.time()
    main()
    print "Done in %.3f seconds" % (time.time() - start_time)