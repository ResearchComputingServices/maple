"""initial app"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sys.path.append(os.getcwd())
from maple import Article
from maple_proc.maple_proc.utils import load_articles
from maple_proc.maple_proc.process import filter_by_sentences, word_frequency, sentiment_analysis

st.set_page_config(layout="wide")
def load_data_with_message():
    """load data and display a temporary message"""
    with st.toast("Loading data..."):
        data_ = load_data()
    return data_

@st.cache_data
def load_data():
    """load the data from the articles"""
    data_directory = os.path.join(os.getcwd(), "data", "to_process")
    data_ = load_articles(data_directory)
    sentiment_analysis(data_)
    return data_

def filter_data(data: list[Article], sentences: list[str]):
    '''filter data by sentences'''
    return filter_by_sentences(data, sentences)


wc = WordCloud(background_color="white")
# def on_change_sentence()
data = load_data_with_message()

st.title("Real-time Policy Tracker")
sentences = st.text_input("Filter", help="Comma separated sentences")
sentences = sentences.split(",")
sentences = [sentence.strip() for sentence in sentences]


with st.toast("Filtering data by sentence"):
    filtered_data = filter_data(data, sentences=sentences)

# st.button("Rerun", on_click=load_data)

print(
    f"Data has {len(data)} articles, and filtered"+\
    f"data have {len(filtered_data)} articles."
)
st.success(f"{len(filtered_data)} of {len(data)} selected.")
with st.toast("Finding word frequency..."):
    freq_words = word_frequency(filtered_data, min_word_size=3, n_words=100)
    print(f"loaded {len(freq_words.keys())} words")
st.toast(f"loaded {len(freq_words.keys())} words" )
    
wc = WordCloud(background_color="white")
with st.toast("Generating word cloud..."):
    wc.generate_from_frequencies(freq_words)


with st.toast("Plotting..."):
    print("plotting...")
    fig, ax = plt.subplots(1, 1)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")

col1, col2 = st.columns(2)

col1.pyplot(fig=fig, clear_figure=True)

sentiment_keys = ['neg', 'neu', 'pos', 'compound']
sentiment_data = {}
for key in sentiment_keys:
    sentiment_data[key] = []
sentiment_labels = {
    'neg':'Negative',
    'neu':'Neutral',
    'pos':'Positive',
    'compound':'Compound'
    }

for article in filtered_data:
    if getattr(article, 'sentiment', None) is not None:
        sentiment = getattr(article, 'sentiment')
        for key in sentiment_keys:
            if key in sentiment.keys():
                sentiment_data[key].append(sentiment[key])

# fig2, ax2 = plt.subplots(1,1, figsize=(fig.get_figwidth(), fig.get_figheight()))

fig2, ax2 = plt.subplots(1,1, figsize=(8, 3.57))

# for key in sentiment_keys:
sns.kdeplot(
    data = pd.DataFrame(sentiment_data).rename(mapper=sentiment_labels),
    legend=True,
    ax=ax2,
)
# fig2.set_figheight(fig.get_figheight())
plt.xlabel("Sentiment Score")
plt.ylabel("Density")
plt.title("Density plot of Sentiment Analysis")
col2.pyplot(fig=fig2, clear_figure=True)
print("Done...")
