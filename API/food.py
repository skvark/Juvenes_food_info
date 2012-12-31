#!/usr/bin/env python
import cherrypy

# This rather simple CherryPy application provides means to get the Juvenes food data 
# in JSON dumps by the language and campus parameters.
#
# See documentation for more information about deploying and other stuff.
#
# (c) 2012-2013 Olli-Pekka Heinisuo 

class API(object):
    """ Request handler class. """

    def __init__(self):
        """ Settings """
        
        # path to JSON files, edit!
        self._json_path = ''
        
        # accepted campuses
        self._campuses = ['TUT', 'TAY', 'TAYKauppi', 'TAMK', 'TAKK']

    def index(self): # index page

        return "Hurr durr put here whatever you want, though a link back to relativity.fi would be nice. This is the api index."

    index.exposed = True

    @cherrypy.expose
    def foodAPI(self, lang, campus):
        """ Serves the JSON data by the parameters. """
        
        cherrypy.response.headers['Content-Type'] = "application/json" # set headers
        
        if campus in self._campuses:
        
            # The files will be read from the path which is given in class initializer
            
            if lang == 'fi':
                return open(self._json_path+lang+'/ruoka_'+campus+'.json')
            elif lang == 'en':
                return open(self._json_path+lang+'/food_'+campus+'.json')
            else:
                raise cherrypy.HTTPError(404)
                
        else:
            raise cherrypy.HTTPError(404)

    foodAPI.exposed = True
    
    def params(self):
        
        s = ' | '.join(self._campuses)
        return "Languages: fi, en<br />Locations: "+s+""
    
    params.exposed = True
    
    def default(self):
        return "This is default page."
    
    default.exposed = True

import os.path
conf = os.path.join(os.path.dirname(__file__), 'foodapi.conf') # conf file

if __name__ == '__main__':
    
    cherrypy.quickstart(API(), '/API', config=conf) # Edit the folder if needed
