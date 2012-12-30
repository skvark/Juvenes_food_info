#!/usr/bin/env python
import datetime
import urllib2
import json
import re
import HTMLParser
import logging
import sys
import time

# Copyright 2012 Olli-Pekka Heinisuo
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# Fetches food data from Juvenes.fi
# Outputs JSON-formatted files
# See documentation for more specific info

# restaurant names, lookup dict
restaurantNames = {0:'TUT', 1:'TAY', 2:'TAYKauppi', 3:'TAMK', 4:'TAKK'}

class JuvenesFood(object):
    """Creates nice dicts about food and other general info of TTY Juvenes restaurants"""
    
    def __init__(self, location, restNames, lang = 'fi'):
    
        # start runtime logging
        self._start_time = time.time()
        
        # language ('fi' if not given)
        # 'en' if you want stuff in English, opening hours will not translate
        self._language = lang
        
        # location
        self._location = location
        
        # error flag
        self._error = False
        
        # decoded json data
        self._loaded_json = ''
        
        # decoded restaurant info (opening hours etc.)
        self._decoded_data_info = ''
        
        # temp dict
        self._food = {}
        
        # inits dict with update time and error-flag
        # JSON time format: datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        self._info = {'update_timestamp':time.time(), 'fatal_error':'False' }
        
        # inits time variables
        self._year, self._week, self._weekdays = datetime.date.today().isocalendar()
        
        # This list/dict contains info about every restaurant...
        # I did spent some hours figuring out those random little funny numbers from Juvenes site, wasn't funny :(
        # Kitcheninfoid's are labeled in the html source code as openinfoid, 
        # and the api service description does not tell anything about them.
        # However, GetKitchenInfo-method magically appears to accept those openinfoid's when inserted
        # in KitchenId's place and the API returns some crazy html/css crap with opening hours in the middle :D
        
        # dict for the restaurants names, indices corresponding to the next list
        self._restaurantNames = restNames

        self._restaurants = [
            # TUT
            [
                {'restaurant': 'Newton', 'kitchen': 6, 'menutype': 60, 'kitcheninfoid': 2352 },
                {'restaurant': 'Zip', 'kitchen': 12, 'menutype': 60, 'kitcheninfoid': 2360 },
                {'restaurant': 'Edison', 'kitchen': 2, 'menutype': 60, 'kitcheninfoid': 2364 },
                {'restaurant': 'Café & Pastabaari Voltti', 'kitchen': 20017, 'menutype': 11, 'kitcheninfoid': 2368 },
                {'restaurant': 'Café & FastVoltti', 'kitchen': 20015, 'menutype': 62, 'kitcheninfoid': 2366 },
                {'restaurant': 'Fusion Kitchen', 'kitchen': 6, 'menutype': 3, 'kitcheninfoid': 2354 },
                {'restaurant': 'Café Rom', 'kitchen': 120024, 'menutype': 58, 'kitcheninfoid': 2362 },
                {'restaurant': 'Café Joule', 'kitchen': 60020, 'menutype': 6, 'kitcheninfoid': 2358 },
                {'restaurant': 'Café Motivaattori', 'kitchen': 60022, 'menutype': 58, 'kitcheninfoid': 2356 }
            ],
            #TAY
            [
                {'restaurant': 'Yliopiston ravintola', 'kitchen': 13, 'menutype': 60, 'kitcheninfoid': 2338 },
                {'restaurant': 'Intro', 'kitchen': 13, 'menutype': 2, 'kitcheninfoid': 2338 },
                {'restaurant': 'Salaattibaari', 'kitchen': 13, 'menutype': 5, 'kitcheninfoid': 2338 },
                {'restaurant': 'Fusion Kitchen', 'kitchen': 13, 'menutype': 3, 'kitcheninfoid': 2338 },
                {'restaurant': 'Café & LunchPinni', 'kitchen': 130016, 'menutype': 60, 'kitcheninfoid': 2340 },
                {'restaurant': 'Alakuppila', 'kitchen': 13, 'menutype': 5, 'kitcheninfoid': 2342 }
            ],
            # TAY Kauppi
            [
                {'restaurant': 'Fusion Kitchen', 'kitchen': 27, 'menutype': 3, 'kitcheninfoid': 2350 },
                {'restaurant': 'Medica Arvo', 'kitchen': 50026, 'menutype': 60, 'kitcheninfoid': 2348 },
                {'restaurant': 'Medica?', 'kitchen': 5, 'menutype': 60, 'kitcheninfoid': 0 }
            ],
            # TAMK
            [
                {'restaurant': 'Dot', 'kitchen': 110027, 'menutype': 60, 'kitcheninfoid': 2324 },
                {'restaurant': 'Ziberia', 'kitchen': 11, 'menutype': 60, 'kitcheninfoid': 2320 },
                {'restaurant': 'Grill & Parila & Combo', 'kitchen': 11, 'menutype': 7, 'kitcheninfoid': 2322 }
            ],
            # TAKK
            [
                {'restaurant': 'Nasta', 'kitchen': 22, 'menutype': 60, 'kitcheninfoid': 2328 },
                {'restaurant': 'Fusion Kitchen & Panini Meal', 'kitchen': 22, 'menutype': 3, 'kitcheninfoid': 2328 },
                {'restaurant': 'Salad & Soup, Café Mesta?', 'kitchen': 220021, 'menutype': 23, 'kitcheninfoid': 2328 }
            ]
        ]
        
        # Logger
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', 
                            level=logging.INFO)
        self._logger = logging.getLogger()
        
        # Urllib2 client
        self._opener = urllib2.build_opener()
        self._opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        self._default_timeout = 20

    def fetch_food(self):
        """Loops trough two weeks, day by day, restaurant by restaurant via this API 
        http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx
        and returns info as a dictionary"""
        
        try: # check for misconfig etc.
        
            self._logger.info(' Starting '+self._restaurantNames[self._location]+'...')
            for w in range(0,2): # loop for weeks
            
                # initializing dicts
                self._food = {}
                # hack for the week 52 and next year
                # though Juvenes API gets fucked up when week 52 and next yers week 1..
                if self._week == 52 and w == 1:
                    curweek = 1
                else:
                    curweek = self._week+w
                    
                self._info[curweek] = {}
                self._logger.info(' Starting week '+str(curweek)+'...')
                
                for i in range(0,6): # weekdays
                    self._food[i] = {}
                    
                    for restaurant in self._restaurants[self._location]:
                        
                        restr = {}
                        fetch_params = { # setting the GET params
                            'kitchen': restaurant['kitchen'],
                            'menutype': restaurant['menutype'],
                            'weekday': i+1,
                            'week': curweek,
                            'kitcheninfoid': restaurant['kitcheninfoid'],
                            'lang': self._language
                        }
                        self._error = False
                        self._decoded_data_info = ''
                        
                        self._get_json_from_juvenes(restaurant, fetch_params, i) # get the json data
                        
                        if self._error == True:
                           continue # jump back to the beginning of the loop   
                        else:
                            restra = self._get_restaurants_foods(restr) # omomommmsmsmsm
                            self._food[i][restaurant['restaurant']] = restra # saving restaurant specific food to dict
                            
                            try:
                                pvm = self._loaded_json['MealOptions'][0]['MenuDate']
                                self._food[i]['date'] = pvm # saving date to dict
                            except:
                                self._food[i]['date'] = ''  # if not found, save empty date
                        
                        if i == 0 and self._decoded_data_info != '': # if "monday", parse and save the opening hours
                        
                            json_info = json.loads(self._decoded_data_info.strip()[1:-2])
                            s = self._parse_opening_hours(str(json_info['d']))
                            self._food[restaurant['restaurant']+'_open'] = s
                            
                self._info[curweek] = self._food # save the restaurant dict to the week-key at the end of the week
        except:
            self._info['fatal_error'] = 'True'
       
        # execution time
        self._end_time = time.time()
        self._logger.info(' Language was '+self._language+'.') # lang info
        self._logger.info(' Fetch time: '+instance._get_execution_time()+'.')
        
        return self._info # class returns food dictionary
    
    # gets the json from Juvenes site
    def _get_json_from_juvenes(self, restaurant, fetch_parameters, i):
        
        try:
            fetched_data = self._opener.open('http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx/GetMenuByWeekday?KitchenId=%(kitchen)s&MenuTypeId=%(menutype)s&Week=%(week)d&Weekday=%(weekday)d&lang=\'%(lang)s\'&format=json' % fetch_parameters)
            decoded_data = fetched_data.read().decode('utf-8')
            
            # stripping some stuff out from the "json"
            decoded_data = json.loads(decoded_data.strip()[1:-2])['d']
            if decoded_data.endswith(');'):
                decoded_data.strip()[:-2]
            self._loaded_json = json.loads(decoded_data)

            if i == 0: # this gets the opening hours at every "monday" for the week (they are the same whole week)
                fetched_data_info = self._opener.open('http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx/GetKitchenInfo?KitchenInfoId=%(kitcheninfoid)s&lang=\'%(lang)s\'&format=json' % fetch_parameters)
                self._decoded_data_info = fetched_data_info.read().decode('utf-8')

        except: # if there's some problem when fetching the data, this raises the error flag
            self._food['error'] = 'Some data could not be fetched.'
            self._logger.info(' Error in '+restaurant['restaurant']+'.')
            self._error = True
    
    # gets the food from current restaurant
    def _get_restaurants_foods(self, restr):
        """Loops trough the foods"""
        
        # loops the food names until exception raises
        for j in range( 0, len(self._loaded_json['MealOptions'])):
                        
            food_type = self._loaded_json['MealOptions'][j]['Name']
            try:
                restr[food_type] = self._loaded_json['MealOptions'][j]['MenuItems'][0]['Name']
            except IndexError:
                continue
                
            # loops all the potatoes, rice and other related stuff :D (until exception)
            for h in range(1, len(self._loaded_json['MealOptions'][j]['MenuItems']) ):
                restr[food_type] += ', '+self._loaded_json['MealOptions'][j]['MenuItems'][h]['Name']

        return restr

    def _parse_opening_hours(self, data_string):
        """Parses some spaghetti html and inline css off and 
        returns nicely formatted opening hours"""
        
        clean = re.sub('<[^<]+?>', '', json.loads(data_string)) # regexp for html tags
        s = clean.replace('\n', ' ')                            # replaces \n with whitespace
        s = s.replace('&nbsp;', ' ')                            # replaces &nbsp; with whitespace 
        s = s.replace('Aukiolo- ja lounasajat ', '')
        s = s.rstrip()                                          # strips whitespace from the end of the string
        h = HTMLParser.HTMLParser()
        s = h.unescape(s)                                       # unescapes html entities and returns unicode
        return s
        
    def _get_execution_time(self):
        """Returns execution time"""
    
        return "%.2f" % (self._end_time - self._start_time, )
        
# Function for writing the dict into an JSON file.        
def write_json(language, location, food_dict, restNames):
    """Writes dict in JSON to file"""
     
    # sorts keys and adds indent for more pretty output
    data = json.dumps(food_dict, sort_keys=True, indent=4)
        
    if lang == 'fi':
        f = open('data/'+language+'/ruoka_'+restNames[location]+'.json', 'w+') # overwrite old
    else:
        f = open('data/'+language+'/food_'+restNames[location]+'.json', 'w+') # overwrite old
            
    f.write(data + "\n")        # save to file
    f.close()
    print "Wrote "+restNames[location]+" food info to JSON file."

# usage example
# accepts "fi" and "en" as parameters
if __name__ == "__main__":

    if len(sys.argv) > 1:
        lang = sys.argv[1]
        if lang != 'en' and  lang != 'fi':
            exit('Parameter error. Parameter was: '+lang+' Accepted values: none, fi, en')
    else:    
        lang = 'fi'
        
    # loops trough different campuses, inits len(restaurantNames) instances
    for location in range( 0, len(restaurantNames) ):
    
        instance = JuvenesFood(location, restaurantNames, lang) # inits object
        food = instance.fetch_food() # fetches the stuff
        write_json(lang, location, food, restaurantNames) # writes json