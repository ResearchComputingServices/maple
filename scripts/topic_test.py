import logging
from maple_structures import Article
from maple_interface import MapleAPI
from bertopic import BERTopic
import matplotlib.pyplot as plt
import numpy as np
from umap import UMAP
import rcs

logger = logging.getLogger('topic_test')
rcs.utils.configure_logging(level='debug')

topic_model = BERTopic.load("./output/topic_models")

maple = MapleAPI(authority="http://134.117.214.192:80")

docs = []
for articles in maple.article_iterator(hours=14*24):
    for article in articles:
        if hasattr(article, 'chat_summary'):
            docs.append(getattr(article, 'chat_summary'))

logger.debug('got %d articles from backend', len(docs))
logger.info('Predicting documents (%d)', len(docs))
doc_pred = topic_model.transform(docs)
logger.info('embedding documents...')
doc_embeddings = topic_model.embedding_model.embed_documents(docs)
umap_model = UMAP(n_neighbors=10, n_components=2, min_dist=0.0,
                  metric='cosine').fit(doc_embeddings)
doc_embeddings_fitted = umap_model.embedding_
# logger.info('fittting embeddings')
# doc_embeddings_fitted = topic_model.umap_model.transform(doc_embeddings)


colors = np.random.rand(len(topic_model.get_topic_info()))
scatter_colors = [colors[doc_pred_i] for doc_pred_i in doc_pred[0]]


fig, ax = plt.subplots(1, 1)
ax.scatter(doc_embeddings_fitted[:, 0],
           doc_embeddings_fitted[:, 1], c=scatter_colors)

# ax.scatter(doc_embeddings[:, 0],
#           doc_embeddings[:, 1], c=scatter_colors)

fig.show()

pass
# print(docs)
# docs = get_docs("test_set/")
# print(f'# of topics: {len(docs)}')
