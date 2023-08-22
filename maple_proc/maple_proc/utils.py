"""utils have helper functions"""
import glob
import os
import json
from json.decoder import JSONDecodeError
import logging
from maple import Article


#The packages and line below are needed for the location function
import spacy
from geopy.geocoders import Nominatim
nlp = spacy.load("en_core_web_sm")
#--------------




logger = logging.getLogger("atlin_proc:utils")


def load_articles(path: str) -> list:
    """load articles exported from the spiders."""
    out = []
    existing_urls = []
    data = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except JSONDecodeError as exc:
                logger.error("Could not load data from file %s. %s", path, exc)
    elif os.path.isdir(path):
        files = glob.glob(os.path.join(path, "*.json"))
        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data += json.load(file)
            except JSONDecodeError as exc:
                logger.error("Could not load data from file %s. %s", path, exc)
                raise exc
    else:
        raise ValueError(f"Invalid path: {path}")
    for article_json in data:
        if article_json["url"] not in existing_urls:
            existing_urls.append(article_json["url"])
            out.append(Article.from_json(article_json))

    return out


#===========================================================================================
#This function retrieves the geopolotical and facilities locations from a text
#using the spacy library
#===========================================================================================
def _get_GEP_locations(text):
    gep={}
    doc = nlp(text)
    for ent in doc.ents:
        if (ent.label_ == "GPE") or (ent.label_ == "FAC"):  # GPE refers to geopolitical entity (location)
            l = ent.text
            if l.lower() not in gep.keys():
                gep[l.lower()]=1
            else:
                gep[l.lower()] = gep[l.lower()] + 1
            #print(ent.text, ent.start_char, ent.end_char, ent.label_)
    return gep


#==========================================================================================
#This function retrieves the most popular location (or the location with more frequency)
#==========================================================================================
def _get_most_popular_location(geps):
    max = 0
    for key, value in geps.items():
        location = value
        if location["frequency"] > max:
            max = location["frequency"]
            loc = key
    return loc



#==========================================================================================
#This function gets the coordinates (latitude and longitude) for a given location
#==========================================================================================
def get_coordinates(loc, count):
    location = {
                 "text": "",
                 "address": "",
                 "geolocation": (),
                 "address_type" : "",
                 "frequency" : 0
                }
    try:
        geolocator = Nominatim(user_agent="sample_app")

        location_obj = geolocator.geocode(loc)
        location["text"] = loc
        location["address"] = location_obj.address
        geo = {}
        geo["latitude"] = location_obj.latitude
        geo["longitude"] = location_obj.longitude
        location["geolocation"] = geo
        location["address_type"] = location_obj.raw["addresstype"]
        location["frequency"] = count
    except Exception as exc:
        print (exc)
    return location



#==========================================================================================
#This functions retrieves the location and its coordinates mentioned in a text
#==========================================================================================
def get_location(text):

    ret_locations = {}

    #Step 1. Get GEP/FAC locations using spacy
    geps = _get_GEP_locations(text)

    #Step 2. Get the geocoordinates
    locations = {}
    for loc, count in geps.items():
        locations[loc] = get_coordinates(loc, count)

    #Step 2. Get the location that was most popular
    main = {}
    key_popular = _get_most_popular_location(locations)
    main[key_popular]=locations[key_popular]

    #Step 3. Organize data structure
    ret_locations["main"]= main
    locations.pop(key_popular)
    ret_locations["others"] = locations

    return ret_locations



