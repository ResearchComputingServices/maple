import logging
from maple_structures import Article
from maple_interface import MapleAPI
# from maple_structures import Topic
# import rcs
import bert
import pprint

logger = logging.getLogger('topic_test')
# rcs.utils.configure_logging(level='debug')

# ===============================================================================================
# Get the articles from the database
# ===============================================================================================


def get_articles(hours):
    maple = MapleAPI(authority="http://134.117.214.192:80")
    art_summaries = []
    art_uuids = []
    for articles in maple.article_iterator(hours=hours):
        for article in articles:
            if hasattr(article, 'chat_summary'):
                art_summaries.append(getattr(article, 'chat_summary'))
                art_uuids.append(getattr(article, 'uuid'))
    logger.debug('got %d articles from backend', len(art_summaries))
    logger.info('Predicting documents (%d)', len(art_summaries))
    return art_uuids, art_summaries


# ===============================================================================================
# Display topic information for a trained model
# ===============================================================================================
def display_topic_information(trained_model):
    try:
        topic_info = trained_model.get_topic_info()
        topic_info_dict = topic_info.to_dict()

        # topic_info.to_csv("results/topic_info.csv")
        # pprint.pprint(topic_info)
        fig = trained_model.visualize_topics()
        fig.show()
    except Exception as e:
        print(e)


# ===============================================================================================
# Display article information for a trained model
# ===============================================================================================
def display_article_information(trained_model, art_summaries):
    try:
        articles_info = trained_model.get_document_info(art_summaries)
        # articles_info.to_csv("results/articles_info.csv")
        # pprint.pprint(articles_info)
        fig = trained_model.visualize_documents(art_summaries)
        fig.show()
    except Exception as e:
        print(e)


if __name__ == '__main__':

    # 1. Extract articles
    hours = 24*10
    art_uuids, art_summaries = get_articles(hours)

    # 2. Create model
    # Note: Here is we will send as paameter the number of topics to find.
    # model = bertopic_model.create_topic_model(
    #    min_topi
    # c_size=3, number_of_topics=9)
    model = bert.create_topic_model(
        min_topic_size=10, number_of_topics=None)

    # 3. Train the model with the articles' summary
    trained_model, topics, probs = bert.perform_topic_modeling(
        model, art_summaries, True)

    # 4. Display topic information
    display_topic_information(trained_model)
    # print("Press a key to continue")
    # key = input()

    # Reduce outlierstra
    # Reduce outliers
    # new_topics = trained_model.reduce_outliers(art_summaries, topics)

    # 4. Display topic information
    # display_topic_information(trained_model)
    # print("Press a key to continue")
    # key = input()

    # 5. Display article information
    display_article_information(trained_model, art_summaries)
