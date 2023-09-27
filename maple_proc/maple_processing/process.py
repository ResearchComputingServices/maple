"""functions to extract information from articles."""
import logging
import nltk
import re
import heapq
from maple_structures import Article
import openai

logger = logging.getLogger('maple_proc')

def filter_by_sentences(
    articles: list[Article],
    sentences: list[str],
    *,
    in_content: bool = True,
    in_title: bool = False,
    match_case: bool = False
):
    """filter the list of Articles if sentence is found in the articles

    Args:
        articles (list[Article]): a list of Articles to filter
        sentences (list[str]): a list of strings to check in the text
        in_content (bool, optional): check in contents of article. Defaults to True.
        in_title (bool, optional): check in title of article. Defaults to False.

    Returns:
        _type_: _description_
    """
    out = []
    for article in articles:
        add = False
        for sentence in sentences:
            text = ""
            if not match_case:
                sentence = sentence.lower()
            if in_content:
                text += article.content if match_case else article.content.lower()

                # if sentence in content:
                #     add = True
                #     break
            if in_title:
                text += " " + article.title if match_case else article.title.lower()
                # if sentence in title:
                #     add = True
                #     break
            sentences_and = sentence.split(" and ")
            nsentences = len(sentences_and)
            for sent in sentences_and:
                if sent in text:
                    nsentences -= 1
            if nsentences == 0:
                add = True
        if add:
            out.append(article)
    return out


def word_frequency(
    articles: list[Article],
    *,
    n_words: int = None,
    tags_to_keep: list = None,
    min_word_size: int = None
):
    word_count = {}
    for article in articles:
        data = nltk.sent_tokenize(article.content)
        for i, _ in enumerate(data):
            data[i] = data[i].lower()
            data[i] = re.sub(r"\W", " ", data[i])
            data[i] = re.sub(r"\s+", " ", data[i])

            words = nltk.word_tokenize(data[i])
            tags = nltk.pos_tag(words)
            if tags_to_keep is None:
                tags_to_keep = ["NN", "VBG", "VBN"]

            for word, tag in tags:
                if min_word_size is not None:
                    if len(word) < min_word_size:
                        continue
                if tag in tags_to_keep:
                    if word not in word_count:
                        word_count[word] = 1
                    else:
                        word_count[word] += 1

    if n_words is None:
        n_words = len(word_count.keys())

    freq_words = heapq.nlargest(n_words, word_count, key=word_count.get)

    out = {}
    total_count = 1
    # for freq_word in freq_words:
    #     total_count += word_count[freq_word]
    for freq_word in freq_words:
        out[freq_word] = word_count[freq_word] / total_count

    return out


def sentiment_analysis(articles: list[Article]) -> None:
    '''Compute sentiment to articles.'''
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sentiment = SentimentIntensityAnalyzer()
    for article in articles:
        article.sentiment = sentiment.polarity_scores(article.content)
        
        
def chat_summary(content: str, api_key: str):
    openai.api_key = api_key
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role":"user",
                "content": f"summarize in less than 300 words the following content: '{content}'",
            },   
        ],
    )
    return completion.choices[0]['message']['content']
    
    