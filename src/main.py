import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import os
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup, SoupStrainer
import re
import urllib

from TflUser import TflUser
from HttpClient import HttpClient

"""Basic premise:
* associate login details with google account
* use credentials to authenticate a session against tfl
* scape (urgh) the journey planner page into some form of dict object
* base the scrape range on dates passed into the app
* chuck out atom (or maybe rss at first) or some other useful xml based
  dataset
* think about http authentication and feeds
  - maybe generate a unique access key
  - spike appengine and http auth
  
Now for a cup of tea and some proof of concept code...
"""

class Tfl():
    """Representation of the Tfl Oyster site
    
    Allows you to login and access the Journey History page.
    """
    
    urls = {
        'login':          "https://oyster.tfl.gov.uk/oyster/security_check",
        'journeyhistory': "https://oyster.tfl.gov.uk/oyster/ppvStatement.do",
    }
    
    user
    client
    
    def __init(self, tflUser):
        self.user = tflUser
    
    def login(self):
        
        values = {
            'j_username': self.user.username,
            'j_password': self.user.password,
        }
        
        self.client = HttpClient(
                     url=self.urls['login'],
                     method='post',
                     values=values
                 )
        
        return self.client
        
    def getJourneyHistoryPage(self, dateFrom, dateTo):
        
        try:
            response = self.client.request(url=self.urls['journeyhistory'])
        except AttributeError:
            print "Tfl.getJourneyHistoryPage needs you to run the login method first"
            
        return response

class MainPage(webapp.RequestHandler):
  def get(self):
    
    template_values = {
    }
    
    #url = "https://oyster.tfl.gov.uk/oyster/entry.do"
    url = "https://oyster.tfl.gov.uk/oyster/security_check"
    
    auth = TflUser(
               username=self.request.get('username'),
               password=self.request.get('password')
           )
    
    form_fields = {
        'j_username': auth.username,
        'j_password': auth.password,
    }
    
    
    form_data = urllib.urlencode(form_fields)
    
    result = urlfetch.fetch(
                   url=url,
                   payload=form_data,
                   method=urlfetch.POST,
                   headers={'Content-Type': 'application/x-www-form-urlencoded'},
                   follow_redirects=False
             )
    
    #if result.status_code == 200:
        #soup = BeautifulSoup(result.content)
        #signInForm = soup.find("form", { "class" : re.compile("home-sign-in") })
        #template_values['content'] = signInForm.prettify()
    if result.status_code == 302:
        url = result.headers['location']
        
        resultHeadersParts = result.headers['set-cookie'].split("; ")
        
        resultHeadersKv = {}
        
        for c in resultHeadersParts:
            
            kv = c.split("=")
            resultHeadersKv[kv[0]] = kv[1]
            
        #print resultHeadersKv
        
        test =  "=".join(['JSESSIONID', resultHeadersKv['JSESSIONID']])
        #print test
        #newHeaders = {'JSESSIONID': resultHeaders['JSESSIONID']}
        
        headers = {'cookie': test}
        #headers = urllib.urlencode(newHeaders)
        there = urlfetch.fetch(url=url, headers=headers, follow_redirects=False)
        #print there.headers
        
        #url2 =
        #url = "https://oyster.tfl.gov.uk/oyster/ppvStatement.do"
        #headers = {'cookie': result.headers['set-cookie']}
        
        url = "https://oyster.tfl.gov.uk/oyster/ppvStatement.do"
        here = urlfetch.fetch(url=url, headers=headers, follow_redirects=False)
        
        #print here.content
        strainer = SoupStrainer("table", { "class" :"journeyhistory" })
        
        soup = BeautifulSoup(here.content, parseOnlyThese=strainer)
        th = soup.find("tr")
        
        th.extract()
        
        jh = soup.findAll("tr")
        
        
        dataset = []
        print 'boo'
            #jh.k
        for row in jh:
            
            indexes = ['date', 'time', 'location', 'action', 'fare', 'pricecap', 'balance']
            
            indexes.reverse()
            keyValues = {}
            
            cells = row.findAll("td")
            
            for cell in cells:
                
                keyValues[indexes.pop()] = cell.string.strip()
                #if row.td.nextSibling.string:
                 #   keyValues[column] = row.td.nextSibling.string
                    #print row.td.nextSibling.string
            
            dataset.append(keyValues)
            
            #print row.td.nextSibling
        print dataset
        #signInForm = soup.find("form", { "class" : re.compile("home-sign-in") })
        #print jh
        
        template_values['jh'] = jh
    
    
    #template_values['content'] = there.content
    
    
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
  #def post(self):
    #self.redirect('/?key=' + key)
    
application = webapp.WSGIApplication(
                                     [('/', MainPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()