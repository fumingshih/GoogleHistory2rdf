'''
Created on Apr 21, 2010

@author: fuming
'''
import urllib
import urllib2 
import re
import logging 
from datetime import datetime
from cookielib import CookieJar
from time import mktime
import feedparser  
import sys
from getopt import getopt
import os

# The folder to store all the downloaded history


folder = './'
trytwice = False

class GoogleHistoryDownloader(object):

    
    def __init__(self, username, password):
 
        self.login_params = {
            "continue": 'https://www.google.com/history/?output=rss',
            "PersistentCookie": "yes",
            "Email": username,
            "Passwd": password,
        }
        
        self.headers = [("Referrer", "https://www.google.com/accounts/ServiceLoginBoxAuth"),
                        ("Content-type", "application/x-www-form-urlencoded"),
                        ('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.0.14) Gecko/2009082706 Firefox/3.0.14'),
                        ("Accept", "text/plain")]
        self.url_ServiceLoginBoxAuth = 'https://www.google.com/accounts/ServiceLoginBoxAuth'
        self.url_CookieCheck = 'https://www.google.com/accounts/CheckCookie?chtml=LoginDoneHtml'
        self.header_dictionary = {}
        self._connect()
        
    def _connect(self):
        global trytwice
        
        self.cj = CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders = self.headers
        galx = re.compile('<input type="hidden" name="GALX" value="(?P<galx>[a-zA-Z0-9_]+)">')
        resp = self.opener.open(self.url_ServiceLoginBoxAuth).read()
        m = galx.search(resp)
        if not m: # may be need to serialize the previous GALX
            #try again! sometimes the cookie could be out-of-date
            if not trytwice: 
                trytwice = True
                self._connect()
                
            else:
                raise Exception("Cannot parse GALX out of login page")
        
        self.login_params['GALX'] = m.group('galx')
        params = urllib.urlencode(self.login_params)
        self.opener.open(self.url_ServiceLoginBoxAuth, params)
        self.opener.open(self.url_CookieCheck)
    
    def download_all(self, startdate=None):

        unixtime = self.make_unixtime(startdate)
        self.download_all_unixtime(unixtime)

    def download_all_unixtime(self,unixtime_start):


        latest_datetime = self.download_history(unixtime_start)     
        previous_latest = latest_datetime

        
        while(True):

            unixtime = self.make_unixtime(latest_datetime)
            latest_datetime = self.download_history(unixtime)        
#            print  ("latest_time_after_last_read:%s")%(latest_datetime)
            
            if(previous_latest!=latest_datetime):
                previous_latest = latest_datetime
            else:
                break;
            
    def make_unixtime(self, datetime):
        
        p = datetime
        unixtime = mktime(p.timetuple())+1e-6*p.microsecond
        return str(int(unixtime))
    
    def download_history(self, unixtime):
        '''
        https://www.google.com/history/lookup?month=1&day=3&yr=2007&output=rss
        https://www.google.com/history/lookup?hl=en&min=1175572800000000&output=rss&num=100
        The plan is to retrieve every 500 entry of browsing history and save into a file with naming of UNIX time
        e.g. 1175572800.xml will be the 500 items starting from 2007, Apr, 3
        '''
 
        google_time = unixtime + '000000'

        self.url_history = 'https://www.google.com/history/lookup?'

        params = urllib.urlencode({ 
            'output': "rss",
            'min': google_time,
            'num':500
 
        })                                    
     
        try:
            self.raw_data = self.opener.open(self.url_history + params).read()
        except Exception, err:
            print err
 
        if self.raw_data in ['You must be signed in to export data from Google Trends']:
            logging.error('You must be signed in to export data from Google Trends')
            raise Exception('You must be signed in to export data from Google Trends')
        
        print("parsing")
        #print(self.raw_data)
        d = feedparser.parse(self.raw_data)
#        last_item = len(d['entries'])
#        print last_item
        latest = d['entries'][0].updated_parsed # time tuple
        
        latest_datetime = datetime(latest[0],latest[1],latest[2],latest[3],latest[4],latest[5])
        
        unixtime = self.make_unixtime(latest_datetime)
        print("writing file %s.xml"%int(unixtime))
        self.write_file(True,int(unixtime))
        
        return latest_datetime
        
    
    
 
    def write_file(self, rss, filename):
        global folder
        if(rss):

            file = open(folder+'%s.xml'%(filename),'w')
            file.write(self.raw_data)
            file.close()
            print "done"
        else:
            
            print "write n3 file"
        # save to the file 
    def write_n3(self):
        print "writing n3"
        
    def download_all_from(self,startdate):
        '''
        The startdate from the input is in format YYYYMMDD. Here we will try to get the earliest date that 
        Google has the user's history. Seems that everyone has different starting date, depends on when they turned on 
        the Google search history. The user needs to find out himself/herself about the first date  
        that Google keeps the record
        
        '''
 
        if startdate:
            s_year = int(startdate[:4])
            s_month = int(startdate[4:6])
            s_day = int(startdate[6:8])

        
        start = datetime(s_year,s_month,s_day)
 
        self.download_all(start)
    
    
    def download_auto(self):
        '''
        It looks for the largest(newest) date specified in the filename and start from there
        '''
        global folder
        newest = ''
        for f in os.listdir(folder):
            
            if(f[0]!='_'): # means it's not translated to rdf yet e.g. 1131102912.xml
                if f[0:9] > newest:
                    newest = f[:10]
            else:
                if f[1:10] > newest:
                    newest = f[1:11]
        
        print "newest:%s"%newest
        self.download_all_unixtime(newest)
        

def main(argv = None):

# 
#   v.2 starts from here 
    global folder
    if argv is None : argv = sys.argv
    try:
        opts, argvs = getopt(sys.argv[1:], 'hu:p:f:', ['start=', 'end=',])
        if opts :
            startdate = ""
            enddate = ""
            id = ""
            passwd = ""
            global folder
            for o, a in opts :
                if o == '-h' :
                    print '''options:
        -h help
        -u <Google id> (must given)
        -p <Google password>  (must given)
        --start <earliest date> (in the format of YYYYMMDD) to start download google history. 
        By default it will try to start on the earliest date of your google history (e.g 2005, Apr).
        If omitted, it will start with the latest date of the previously downloaded history in the folder
        -f <output folder> to store the downloaded search history, by default it's the current folder that runs this program 
        example: GoogleHistoryDownloader -u yourid -p yourpasswd --start 20061001'''
                        
                elif o=='--start' : startdate = a
                elif o=='-f' : folder = a
                elif o=='-u' : id = a
                elif o=='-p' :
                    passwd = a
                    r = GoogleHistoryDownloader(id,passwd)
                
            if startdate: 
                r.download_all_from(startdate)
            else:
                r.download_auto()       
        else:
            print '''Type -h for help'''
    except Exception, err:
        print err


if __name__ == '__main__':
    main()
    


    


    


 
