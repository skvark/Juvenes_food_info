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

class TTYfood(object):
    """Creates nice JSON files about food and other general info of TTY Juvenes restaurants"""
    
    def __init__(self, lang = 'fi'):
    
        # start runtime logging
        self._start_time = time.time()
        
        # language ('fi' if not given)
        # 'en' if you want stuff in English, opening hours will not translate
        self._language = lang
        
        # filepaths/names
        self._en = 'food.json'
        self._fi = 'ruoka.json'
        
        # inits dict with update time and error-flag
        # JSON time format: datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        self._info = {'update_timestamp':time.time(), 'error':'False' }
        
        # inits time variables
        self._year, self._week, self._weekdays = datetime.date.today().isocalendar()
        
        # This list/dict contains info about every restaurant...
        # I did spent some hours figuring out those random little funny numbers from Juvenes site, wasn't funny :(
        # Kitcheninfoid's are labeled in the html source code as openinfoid, 
        # and the api service description does not tell anything about them.
        # However, GetKitchenInfo-method magically appears to accept those openinfoid's when inserted
        # in KitchenId's place and the API returns some crazy html/css crap with opening hours in the middle :D
        
        # More stuff (cafes) will be added later...
        self._restaurants = [
            {'restaurant': 'Newton', 'kitchen': 6, 'menutype': 60, 'kitcheninfoid': 2352 },
            {'restaurant': 'Zip', 'kitchen': 12, 'menutype': 60, 'kitcheninfoid': 2360 },
            {'restaurant': 'Edison', 'kitchen': 2, 'menutype': 60, 'kitcheninfoid': 2364 },
            {'restaurant': 'Pastabaari', 'kitchen': 26, 'menutype': 11, 'kitcheninfoid': 2368 },
            {'restaurant': 'Fast Voltti', 'kitchen': 25, 'menutype': 4, 'kitcheninfoid': 2366 },
            {'restaurant': 'Fusion Kitchen', 'kitchen': 6, 'menutype': 3, 'kitcheninfoid': 2354 }
        ]
        
        # More stuff (cafes) will be added later...
        self._restaurants_tay = [
            {'restaurant': 'Café Alakuppila', 'kitchen': 30, 'menutype': 58, 'kitcheninfoid': 2342 },
            {'restaurant': 'Intro', 'kitchen': 13, 'menutype': 2, 'kitcheninfoid': 2338 },
            {'restaurant': 'Salaattibaari', 'kitchen': 13, 'menutype': 5, 'kitcheninfoid': 2336 },
            {'restaurant': 'Fusion Kitchen', 'kitchen': 13, 'menutype': 3, 'kitcheninfoid': 2334 }
        ]
        self._restaurants_tay_kauppi = [
            {'restaurant': 'Medica Bio', 'kitchen': 5, 'menutype': 60, 'kitcheninfoid': 2346 },
            {'restaurant': 'Medica Arvo', 'kitchen': 27, 'menutype': 60, 'kitcheninfoid': 2348 }
        ]
        
        self._restaurants_tamk = [
            {'restaurant': 'Dot (Ziberia)', 'kitchen': 15, 'menutype': 60, 'kitcheninfoid': 2324 }
        ]
        
        self._restaurants_takk = [
            {'restaurant': 'Nasta', 'kitchen': 22, 'menutype': 60, 'kitcheninfoid': 2328 },
            {'restaurant': 'Fusion Kitchen & Panini Meal', 'kitchen': 22, 'menutype': 3, 'kitcheninfoid': 2328 },
            {'restaurant': 'Salad & Soup', 'kitchen': 22, 'menutype': 23, 'kitcheninfoid': 2328 },
           #{'restaurant': 'Café Mesta', 'kitchen': , 'menutype': , 'kitcheninfoid': }
        ]
        
        # Logger
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', 
                            level=logging.INFO)
        self._logger = logging.getLogger()
        
        # Urllib2 client
        self._opener = urllib2.build_opener()
        self._opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        self._default_timeout = 20
        
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
        
    def fetch_food(self):
        """Loops trough two weeks, day by day, restaurant by restaurant via this API 
        http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx
        and returns info as a dictionary"""
        
        for w in range(0,2): # loop for weeks
        
            # initializing dicts
            food = {}
            curweek = self._week+w
            self._info[curweek] = {}
            self._logger.info(' Starting week '+str(curweek)+'...')
            
            for i in range(0,6): # weekdays
                food[i] = {}
                
                for restaurant in self._restaurants:
                
                    restr = {}
                    fetch_parameters = { # setting the GET params
                        'kitchen': restaurant['kitchen'],
                        'menutype': restaurant['menutype'],
                        'weekday': i+1,
                        'week': curweek,
                        'kitcheninfoid': restaurant['kitcheninfoid'],
                        'lang': self._language
                    }
                    try:
                    
                        fetched_data = self._opener.open('http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx/GetMenuByWeekday?KitchenId=%(kitchen)s&MenuTypeId=%(menutype)s&Week=%(week)d&Weekday=%(weekday)d&lang=\'%(lang)s\'&format=json' % fetch_parameters)
                        decoded_data = fetched_data.read().decode('utf-8')
                        
                        # stripping some stuff out from the "json"
                        decoded_data = json.loads(decoded_data.strip()[1:-2])['d']
                        if decoded_data.endswith(');'):
                            decoded_data.strip()[:-2]
                        loaded_json = json.loads(decoded_data)
                        
                        if i == 0: # this gets the opening hours at every "monday" for the week (they are the same whole week)
                            fetched_data_info = self._opener.open('http://www.juvenes.fi/DesktopModules/Talents.LunchMenu/LunchMenuServices.asmx/GetKitchenInfo?KitchenInfoId=%(kitcheninfoid)s&lang=\'%(lang)s\'&format=json' % fetch_parameters)
                            decoded_data_info = fetched_data_info.read().decode('utf-8')
                                                
                    except: # if there's some problem when fetching the data, this raises the error flag
                        food['error'] = True
                        self.logger.info(' Error in fetching.')
                        return
                    try:
                        pvm = loaded_json['MealOptions'][0]['MenuDate'] # get the date
                        
                        for j in range(0,4): # loops the food names until exception raises
                        
                            type = loaded_json['MealOptions'][j]['Name']
                            restr[type] = loaded_json['MealOptions'][j]['MenuItems'][0]['Name']
                            
                            try:
                                for h in range(1,3): # loops all the potatoes, rice and other related stuff :D (until exception)
                                    restr[type] += ', '+loaded_json['MealOptions'][j]['MenuItems'][h]['Name']
                            except:
                                pass # we don't care
                    except:
                        pass # we don't care
                        
                    food[i][restaurant['restaurant']] = restr # saving restaurant specific food to dict
                    food[i]['date'] = pvm # saving date to dict
                    
                    if i == 0: # if "monday", parse and save the opening hours
                    
                        json_info = json.loads(decoded_data_info.strip()[1:-2])
                        s = self._parse_opening_hours(str(json_info['d']))
                        food[restaurant['restaurant']+'_open'] = s
                        
                self._logger.info(' Fetched day '+pvm+' foods successfully.')
            self._info[self._week+w] = food # save the restaurant dict to the week-key at the end of the week
        self._end_time = time.time()
        self._logger.info(' Language was '+self._language+'.')
        self._logger.info(' Fetch time: '+instance._get_execution_time()+'.')
        return self._info # class return food dictionary
        
    def _get_execution_time(self):
        """Returns execution time"""
    
        return "%.2f" % (self._end_time-self._start_time, )
        
# function for writing the dict into an JSON file.        
def write_json(language, food_dict):
    """Writes JSON to file"""
        
    # sorts keys and adds indent for more pretty output
    data = json.dumps(food_dict, sort_keys=True, indent=4)
        
    if lang == 'fi':
        f = open('ruoka.json', 'w+') # overwrite old
    else:
        f = open('food.json', 'w+') # overwrite old
            
    f.write(data + "\n")        # save to file
    f.close()
    print "Wrote JSON to file."

# usage example
# accepts "fi" and "en" as parameters
if __name__ == "__main__":
    if len(sys.argv) > 1:
        lang = sys.argv[1]
        if lang != 'en' and  lang != 'fi':
            exit('Parameter error. Parameter was: '+lang+' Accepted values: none, fi, en')
    else:    
        lang = 'fi'
        
    instance = TTYfood(lang) # inits object
    food = instance.fetch_food() # fetches the stuff
    write_json(lang, food) # writes json