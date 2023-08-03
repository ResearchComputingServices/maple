"""test module"""
import logging
import json
import os
import nltk
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from maple_proc import load_articles
from maple_proc.process import filter_by_sentences, word_frequency, sentiment_analysis



nltk.download('tagsets')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

DATA_DIRECTORY = os.path.join(os.getcwd(), "data", "to_process")
data = load_articles(DATA_DIRECTORY)

sentiment_analysis(data)

logger.debug(json.dumps(data[0].to_dict(), indent=2))
filtered_data = filter_by_sentences(data, ["Health"])

logger.debug("data has %s and filtered_data has %s.", len(data), len(filtered_data))

freq_words = word_frequency(filtered_data, min_word_size=3)
logger.debug(json.dumps(freq_words, indent=2))

wc = WordCloud(background_color='white')
wc.generate_from_frequencies(freq_words)
plt.figure()
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()
