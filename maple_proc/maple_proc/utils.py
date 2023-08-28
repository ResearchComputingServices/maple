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
#-----------------------------------------------------------------


#The packages below are needed for sentiment analysis
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
from scipy.special import softmax

MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
#------------------------------------------------------------------


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



#==========================================================================
#Returns the maximum score for a sentiment value and assign a label to it
#=========================================================================
def max_score(scores):
    if (scores[0]>scores[1]) and (scores[0]>scores[2]):
        label="NEGATIVE"
        score = scores[0]
    else:
        if (scores[1] > scores[0]) and (scores[1] > scores[2]):
            label = "NEUTRAL"
            score = scores[1]
        else:
            if (scores[2] > scores[0]) and (scores[2] > scores[1]):
                label = "POSITIVE"
                score = scores[2]
    return label, score



#==========================================================================
#This function split a text in paragraphs
#Assuming each paragraph is separated by a new line.
#==========================================================================
def split_in_paragraphs(text):
   lines = text.split('\n')
   return lines


#==========================================================================
#This function gets the sentiment value of an article
#==========================================================================
def bert_get_sentiment_of_article(article_text):
    #Get the paragraphs
    lines = split_in_paragraphs(article_text)

    #Obtain sentiment value of each paragraph
    sentiment_lines = {}
    i=0
    for line in lines:
        if len(line)>0:
            label, score = bert_get_sentiment_of_text(line)
            sentiment_lines[i] = {"label" : label, "score" : score}
            i=i+1
    return sentiment_lines


#==========================================================================
#This function gets the sentiment value of a text
#==========================================================================
def bert_get_sentiment_of_text(text):
    encoded_text = tokenizer(text, return_tensors='pt')
    output = model(**encoded_text)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    scores_dict = {
        'roberta_neg': scores[0],
        'roberta_neu': scores[1],
        'roberta_pos': scores[2]
    }
    label, score = max_score(scores)

    return label, score


#======================================================================
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nltk.download('all')

#======================================================================
def nltk_preprocess_text(text):

    # Tokenize the text
    tokens = word_tokenize(text.lower())

    # Remove stop words
    filtered_tokens = [token for token in tokens if token not in stopwords.words('english')]

    # Lemmatize the tokens
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]

    # Join the tokens back into a string
    processed_text = ' '.join(lemmatized_tokens)
    return processed_text


#=========================================================================
def nltk_max_score(scores):
    if (scores['neg']>scores['neu']) and (scores['neg']>scores['pos']):
        label="NEGATIVE"
        score = scores['neg']
    else:
        if (scores['neu'] > scores['neg']) and (scores['neu'] > scores['pos']):
            label = "NEUTRAL"
            score = scores['neu']
        else:
            if (scores['pos'] > scores['neg']) and (scores['pos'] > scores['neu']):
                label = "POSITIVE"
                score = scores['pos']
            else:
                label = "UNDEFINED"
                score = 0

        if scores['compound'] >= 0.05:
            overall = "POSITIVE"
        else:
            if scores["compound"]<=-0.05:
                overall = "NEGATIVE"
            else:
                overall = "NEUTRAL"
    return label, score, overall



#=====================================================================================
def nltk_sentiment_text(text):
    analyzer = SentimentIntensityAnalyzer()
    pre_pro_text = nltk_preprocess_text(text)
    scores = analyzer.polarity_scores(pre_pro_text)
    label, score, overall = nltk_max_score(scores)

    return overall, scores["compound"]





