import json
from maple_interface import MapleAPI
from pprint import pprint as p

maple = MapleAPI(authority='http://0.0.0.0:3000')

dump_articles = []
chat_summary_count = 0
for articles in maple.article_iterator():
    for article in articles:
        try:
            dump_articles.append(article.to_dict())
            if hasattr(article, 'chat_summary'):
                chat_summary_count +=1
            else: 
                p(f"Article without chat_summary: {article.uuid} {article.url}\n{json.dumps(article.to_dict(), indent=2)}")
        except Exception as exc:
            print(exc)            

FILENAME = 'data/dump.json'
try:
    with open(FILENAME, 'w', encoding='utf-8') as f:
        json.dump(dump_articles, f)
    print(f'got {len(dump_articles)}, {chat_summary_count} had chatgpt summaries.')
except Exception as exc:
    print('failed ...', exc)
