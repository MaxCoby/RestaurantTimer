import requests
from requests import get
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import re
import matplotlib.pyplot as plt
import numpy as np
from PIL import ImageGrab
import unidecode
import os.path

""" Project Secondus!
    Locates location based on IP address and uses Yelp API to find nearby recommended restaurants.
    Implements selenium to look up each restaurant's name on Google as Google API does not 
    contain data about popularity at each hour. Scrapes pixel height from the html in order to create
    graphs with matplotlib, screenshots each graph after appearing, and saves the screenshot in folder.
    MapQuest API used to show the restaurants on the map and the associated graph of popular times can 
    be seen when hovering over the mark. 
"""
__author__ = "Max Chou"

# determining current day of the week for the graph of popular times
weekday = datetime.datetime.today().weekday()
if weekday == 0:
    day = "Mondays"
elif weekday == 1:
    day = "Tuesdays"
elif weekday == 2:
    day = "Wednesdays"
elif weekday == 3:
    day = "Thursdays"
elif weekday == 4:
    day = "Fridays"
elif weekday == 5:
    day = "Saturdays"
elif weekday == 6:
    day = "Sundays"

# determining current hour for the graph of popular times
now = datetime.datetime.now()
current_hour = int(now.hour)
if current_hour == 5:
    current_hour = "5 AM"
elif current_hour == 6:
    current_hour = "6 AM"
elif current_hour == 7:
    current_hour = "7 AM"
elif current_hour == 8:
    current_hour = "8 AM"
elif current_hour == 9:
    current_hour = "9 AM"
elif current_hour == 10:
    current_hour = "10 AM"
elif current_hour == 11:
    current_hour = "11 AM"
elif current_hour == 12:
    current_hour = "12 PM"
elif current_hour == 13:
    current_hour = "1 PM"
elif current_hour == 14:
    current_hour = "2 PM"
elif current_hour == 15:
    current_hour = "3 PM"
elif current_hour == 16:
    current_hour = "4 PM"
elif current_hour == 17:
    current_hour = "5 PM"
elif current_hour == 18:
    current_hour = "6 PM"
elif current_hour == 19:
    current_hour = "7 PM"
elif current_hour == 20:
    current_hour = "8 PM"
elif current_hour == 21:
    current_hour = "9 PM"
elif current_hour == 22:
    current_hour = "10 PM"
elif current_hour == 23:
    current_hour = "11 PM"

turn_green = False # open with current activity
turn_blue = False # open without current activity
turn_red = False # closed
turn_gray = False # not enough data


mapquestKey = "Upsn88yhJT0Ez0OqsbNdJ9BjpH8cR0g8"
ipstackKey = "8259377043d9ed7fa5bb36bbd93cc7ab"
yelpKey = "0vxh3O8kZdWX2R6cSwuG8lr6EzyzTIFWS32kKIt7HMlWYQuZCrtIaktyBorp4nWwJ6uhMvSCPvaEcNHwLMlWBzM81p_Dtelo_--IKOXJSwoZwnv2uyXoahuwh-3ZW3Yx"
ip = get('https://api.ipify.org').text

# finds latitude and longitude based on public IP address
ipstackURL = "http://api.ipstack.com/" + ip
ipstack_param_data = {"access_key": ipstackKey}
ipstack_response = requests.get(ipstackURL, params=ipstack_param_data)
ipstack_response_data = json.loads(ipstack_response.text)
latitude = str(ipstack_response_data["latitude"])
longitude = str(ipstack_response_data["longitude"])

# using Yelp API to find recommended restaurants within ~3 mile radius of current location
yelp_header_data = {"Authorization" : "Bearer " + yelpKey}
yelp_param_data = {"term" : "Restaurants", "latitude" : latitude, "longitude" : longitude, "radius": 5000}
yelp_endpoint = "https://api.yelp.com/v3/businesses/search"
yelp_response = requests.get(yelp_endpoint, headers=yelp_header_data, params=yelp_param_data)
yelp_response_data = json.loads(yelp_response.text)

def height_and_hours(name):
    """ This function returns the list of hours where there is activity
        and their respective list of pixel heights of the bar at those hours.
        Uses selenium to look up restaurant names and scrapes html to find
        the hours and heights of the bars in Google's "Popular times" graphs
    """
    import time

    list_of_hours = []
    list_of_heights = []

    # using selenium to look up restaurants from Yelp on Google
    driver = webdriver.Safari()
    driver.get("https://www.google.com")
    inputElement = driver.find_element(By.NAME, "q")
    inputElement.send_keys(name + " restaurant")
    inputElement.submit()
    WebDriverWait(driver, 10).until(EC.title_contains(name + " restaurant"))
    time.sleep(2)
    html = driver.page_source

    # scraping through the html to find the hours and pixel heights of google's "Popular times" graph
    # Google API does not want popular times data being public, so selenium and scraping was the alternative
    # able to determine relative popularity based on the height of the bars in the html
    bsObj = BeautifulSoup(html, "html.parser")
    
    time_slots = bsObj.find_all('div', class_='wYzX9b')    
    for slot in time_slots:
        data_hour = slot['data-hour']
        list_of_hours.append(int(data_hour))

    heights = bsObj.find_all("div", class_="cwiwob")
    for height in heights:
        inline_style = height["style"]
        cleaned_height = inline_style.replace("height:", "").replace("px;", "")
        list_of_heights.append(float(cleaned_height))

    driver.close()

    return list_of_hours, list_of_heights

def plot(name, hours_and_heights):
    """ This function creates a graph for the given restaurant using its
        name and list of hours and list of pixel heights for the bars
        and then screenshots the image and saves it.
        Uses matplotlib to create the graphs and ImageGrab to screenshot
        the graphs when they appear.
    """

    # if there was no data available for the restaurant
    if (hours_and_heights[0].__len__() == 0):
        print ("Not Enough Data Given About Popular Times for the Restaurant: " + name)
        return ""

    delete_hour_index = datetime.datetime.now().hour - 6 + 1 # current hour is duplicated
    hours_for_graphs = [f'{i} AM' if i <= 12 else f'{i - 12} PM' for i in hours_and_heights[0]]
    heights_for_graphs = hours_and_heights[1]
    current_bar_height = False

    if len(heights_for_graphs) > len(hours_for_graphs):
        # has current activity
        current_bar_height = heights_for_graphs[delete_hour_index]
        global turn_green
        turn_green = True
        heights_for_graphs.pop(delete_hour_index)  
    elif heights_for_graphs[datetime.datetime.now().hour - 6] != 0:
        # open
        global turn_blue
        turn_blue = True
    elif heights_for_graphs[datetime.datetime.now().hour - 6] == 0:
        # closed
        global turn_red
        turn_red = True

    # creating the graph
    plt.rcParams['toolbar'] = 'None'
    plt.figure(figsize=(12, 8))
    plt.ylim([0, 100])
    plt.yticks([])
    y_pos = np.arange(len(hours_for_graphs))
    plt.bar(y_pos, heights_for_graphs, align = "center")
    if current_bar_height != False:
        plt.bar(y_pos[hours_for_graphs.index(current_hour)], current_bar_height, color='red', align="center", alpha=0.5)
    plt.xticks(y_pos, hours_for_graphs)
    plt.ylabel("Overall Popularity")
    plt.xlabel("Time by the Hour")
    plt.title("Popular Times for " + name)

    # screenshotting the graph and saving it
    plt.savefig(f'/Users/max/Desktop/GitHub/RestaurantTimer/src/{name}.png')

restaurant_js = ""

# making map markers for restaurants given by Yelp API
for i in range(0, len(yelp_response_data["businesses"])):
    # gets rid of accent marks and apostrophes
    name = unidecode.unidecode(yelp_response_data["businesses"][i]["name"].replace("'", ""))

    # creates the graph and saves the screenshot
    plot(name, height_and_hours(name))

    # keeps track of latitude and longitude of the restaurant
    rlat = str(yelp_response_data["businesses"][i]["coordinates"]["latitude"])
    rlong = str(yelp_response_data["businesses"][i]["coordinates"]["longitude"])

    # checks if there is a screenshot for the graph of the restaurant
    if os.path.isfile(f'/Users/max/Desktop/GitHub/RestaurantTimer/src/{name}.png'):
        if turn_green == True:
            restaurant_js += """L.marker([""" + rlat + ", " + rlong + """], {
        icon: L.mapquest.icons.marker({
        primaryColor: '00FF00'
        }),
        draggable: false
      }).bindPopup('<img src=""" + '"' + name + """.png" width="450" height="300" alt="Not Enough Data for """ + name + '"' + """</img>').addTo(map);

      """

            turn_green = False

        elif turn_blue == True:
            restaurant_js += """L.marker([""" + rlat + ", " + rlong + """], {
        icon: L.mapquest.icons.marker({
        primaryColor: '0000FF'
        }),
        draggable: false
      }).bindPopup('<img src=""" + '"' + name + """.png" width="450" height="300" alt="Not Enough Data for """ + name + '"' + """</img>').addTo(map);

      """

            turn_blue = False

        elif turn_red == True:
            restaurant_js += """L.marker([""" + rlat + ", " + rlong + """], {
        icon: L.mapquest.icons.marker({
        primaryColor: 'FF0000'
        }),
        draggable: false
      }).bindPopup('<img src=""" + '"' + name + """.png" width="450" height="300" alt="Not Enough Data for """ + name + '"' + """</img>').addTo(map);

      """

            turn_red = False
        else:
            restaurant_js += """L.marker(["""+ rlat + ", " + rlong + """], {
        icon: L.mapquest.icons.marker(),
        draggable: false
      }).bindPopup('<img src=""" + '"' + name + """.png" width="450" height="300" alt="Not Enough Data for """ + name + '"' + """</img>').addTo(map);
            
      """
    # if there is no screenshot for the graph of the restaurant (no data on Google),
    # create marker with default color and acknowledge there was insufficient data in the popup
    else:
        restaurant_js += """L.marker([""" + rlat + ", " + rlong + """], {
        icon: L.mapquest.icons.marker(),
        draggable: false
      }).bindPopup('""" + "Not Enough Data to Make Graph of Popular Times for " + name + """').addTo(map);

      """

# the beginning boiler plate for a MapQuest map
start="""<html>
  <head>
    <script src="https://api.mqcdn.com/sdk/mapquest-js/v1.3.2/mapquest.js"></script>
    <link type="text/css" rel="stylesheet" href="https://api.mqcdn.com/sdk/mapquest-js/v1.3.2/mapquest.css"/>

    <script type="text/javascript">
      window.onload = function() {
        L.mapquest.key = '""" + mapquestKey + """';

        var map = L.mapquest.map('map', {
          center: ["""+ latitude + ", " + longitude + """],
          layers: L.mapquest.tileLayer('map'),
          zoom: 12
        });

  """

# the ending boiler plate for a MapQuest map
end="""      };
    </script>
  </head>

  <body style="border: 0; margin: 0;">
    <div id="map" style="width: 100%; height: 1000px;"></div>
  </body>
</html>"""

# write the html for our custom map with restaurants
myfile = open("restaurant.html", "w")
myfile.write(start + restaurant_js + end)
myfile.close()