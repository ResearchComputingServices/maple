import time
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from umap import UMAP
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired
from pprint import pprint as print

import bert_utils


###########################################################################################################
# This function precalculates the embeddings so that they can be used again.
# There are many topics for doing this
###########################################################################################################


def calculate_embeddings(docs: list):

    embedding_model = SentenceTransformer(bert_utils.EMBEDDING_MODEL)
    embeddings = embedding_model.encode(docs,
                                        show_progress_bar=True)

    return embeddings

###########################################################################################################
# Initialize the clustering algorithm. This controls the number of topics generated
###########################################################################################################


def get_clustering_algorithm(min_cluster_size=bert_utils.CLUSTERING_MIN_SIZE,
                             metric=bert_utils.CLUSTERING_METRIC,
                             cluster_selection_method=bert_utils.CLUSTERING_SELECTION_METHOD,
                             prediction_data=True):

    hdbscan_model = HDBSCAN(min_cluster_size=min_cluster_size,
                            metric=metric,
                            cluster_selection_method=cluster_selection_method,
                            prediction_data=prediction_data)
    return hdbscan_model

###########################################################################################################
# This function will setup a random seed to make the output reproduceable
###########################################################################################################


def get_dim_reduc_model(n_neighbors=bert_utils.UMAP_NUM_NEIHGBOURS,
                        n_components=bert_utils.UMAP_NUM_COMPS,
                        min_dist=bert_utils.UMAP_MIN_DIST,
                        metric=bert_utils.UMAP_METRIC,
                        random_state=bert_utils.UMAP_RANDOM_SEED):

    umap_model = UMAP(n_neighbors=n_neighbors,
                      n_components=n_components,
                      min_dist=min_dist,
                      metric=metric,
                      random_state=random_state)

    return umap_model

###########################################################################################################
# Topic cleaner
###########################################################################################################


def get_topic_cleaner(stop_words=bert_utils.VEC_MODEL_STOP_WORDS,
                      min_df=bert_utils.VEC_MODEL_MIN_DIFF,
                      ngram_range=bert_utils.VEC_MODEL_NGRAM_RANGE):

    # Clean up the topic representations (remove stopwords)
    vectorizer_model = CountVectorizer(stop_words=stop_words,
                                       min_df=min_df,
                                       ngram_range=ngram_range)

    return vectorizer_model

###########################################################################################################
#  Topic representation model (get a summmary of the topic) ie LABEL
###########################################################################################################


def get_labeler():

    keybert_model = KeyBERTInspired()

    representation_model = {"KeyBERT": keybert_model}

    return representation_model

###########################################################################################################
# This function precalculates the embeddings so that they can be used again.
###########################################################################################################


def create_topic_model(min_topic_size=None, number_of_topics=None):

    # customized the various steps of the topic modeller
    cluster_model = get_clustering_algorithm()

    dim_reduc_model = get_dim_reduc_model()

    vec_model = get_topic_cleaner()

    labeller = get_labeler()

    # Now create the BERTopic model
    # topic_model = BERTopic(embedding_model=EMBEDDING_MODEL,
    #                       hdbscan_model=cluster_model,
    #                       umap_model=dim_reduc_model,
    #                       vectorizer_model=vec_model,
    #                       representation_model=labeller,
    #                       min_topic_size=min_topic_size,
    #                       nr_topics = number_topics)

    # Now create the BERTopic model
    topic_model = BERTopic(embedding_model=bert_utils.EMBEDDING_MODEL,
                           hdbscan_model=cluster_model,
                           umap_model=dim_reduc_model,
                           vectorizer_model=vec_model,
                           representation_model=labeller)

    return topic_model

###########################################################################################################
# This function performs topic modeling on the set of strings passed as an arguments
###########################################################################################################


def perform_topic_modeling(tm: BERTopic,
                           input_corpus=[],
                           verbose=False):
    try:
        start = time.time()
        topics, probs = tm.fit_transform(input_corpus)
        end = time.time()

        if verbose:
            print(f'Processing Time {end-start}[s]')
    except Exception as e:
        print(e)

    return tm, topics, probs
