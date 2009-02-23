"""HttpClient

HttpClient acts as an interface to urlfetch. It handles redirection headers and
will maintain cookies between requests

"""
class HttpClient():
    
    cookies = {}
    
    def __init__(self, url, method='get', values=None):
        self.request(url, method, values)
        
    def request(url, method='get', values=None, headers=None):
        
        if method == 'post':
            method = urlfetch.POST
        else:
            method = urlfetch.GET
        
        if values:
            values = urllib.urlencode(values)
        
        # TODO make sure headers grabs from the cookie jar 
        if headers is None: headers = {}
        
        response = urlfetch.fetch(
            url=url,
            payload=values,
            method=method,
            headers=headers,
            follow_redirects=False
        )
        
        if response.status_code == 200:
            return response
        elif response.status_code == 302:
            
            #Add the session cookie from the response and pass it to the cookie jar
            responseCookies = self.__extractCookies(result.headers['set-cookie'])
            cookies = self.cookieJar(responseCookies['JSESSIONID'])
            
            url = result.headers['location']
            
            return self.request(
                       url=url,
                       headers={'cookies': cookies}
                   )
        
    def cookieJar(self, moreCookies=None):
        """Return the collection of cookies we have collected so far.
        Passing a dict as an argument adds to the cookieJar
        """
        if moreCookies:
            self.cookies.extend(moreCookies)
            
        # TODO need some kind of urllib encode and join here
        #return self.cookies
        return "; ".join(["%s=%s" % (k, v) for k, v in self.cookies])
        #return "=".join(['JSESSIONID', resultHeadersKv['JSESSIONID']])
    
    def __extractCookies(self, cookieString):
        """Returns a dict object of cookie name value pairs derived 
        from the parsed cookieString
        """
        parts = cookieString.split("; ")
        
        data = {}
        
        for cookie in parts:
            keyValues = cookie.split("=")
            data[keyValues[0]] = keyValues[1]
            
        return data
        #print resultHeadersKv
        # TODO sort this
    