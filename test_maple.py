from maple import Article, Comments, Author
import logging
import json
logging.basicConfig(level=logging.DEBUG)

author = Author.from_json(dict(name="Roger Selzler", last_name="Selzler", url="http://tse.htmls.com", a=1))
author.email="roger@bol.com.br"
print("This is an example of an Author")
print(json.dumps(author.to_dict(), indent=2))
#TODO comment should have content
comment = Comments.from_json(dict(author=author.to_dict()))
print("This is an example of a comment.")
print(json.dumps(comment.to_dict(), indent=2))

article = Article()
article.title = "This is a title"
article.summary = "Summary should be a string and this is an example of a summary"
article.content = "This is where all the content extracted from news should go"
article.url = "http://globalnews.com/validurl"
article.date_published = "2023-07-03"

article.add_author(author)
article.random_keyword = "Example of metadata added"
# article.add_author(author)
print("This is the structure of an article")
print(json.dumps(article.to_dict(), indent=2))


b=Article.from_json(article.to_dict())


# news_catcher_article = {
#     "title": "ARK reduziert Anteile: Cathie Wood wirft Tesla-Aktien aus dem Depot",
#     "author": "test_name",
#     "published_date": "2021-08-04 01:15:00",
#     "published_date_precision": "full",
#     "link": "https://www.finanzen.net/nachricht/aktien/beteiligung-reduziert-ark-reduziert-anteile-cathie-wood-wirft-tesla-aktien-aus-dem-depot-10402608",
#     "clean_url": "finanzen.net",
#     "excerpt": "• ARK Invest verkauft Tesla-Anteile im Wert von 43,7 Millionen US-Dollar • Tesla-Aktie bleibt Top-Holding in drei ETFs • Cathie Wood sieht Tesla-Aktie falsch ...",
#     "summary": "• ARK Invest verkauft Tesla-Anteile im Wert von 43,7 Millionen US-Dollar• Tesla-Aktie bleibt Top-Holding in drei ETFs• Cathie Wood sieht Tesla-Aktie falsch bewertet Die starke Entwicklung der Tesla-Aktie im Jahr 2020 war einer der Hauptwachstumstreiber in den ETFs der Investmentfirma ARK Invest. Im April hatte das Unternehmen bei einem Aktienpreis von rund 719 US-Dollar dann zuletzt einige Tesla-Aktien aus dem Depot geworfen, jetzt war es erneut soweit. Tesla-Aktien verkauft: 43,7 Millionen US-Dollar eingenommen ARK veräußerte 63.643 Tesla-Aktien und hat bei dem Verkauf 43,7 Millionen US-Dollar eingenommen, das geht aus dem Trading-Update des Unternehmens hervor. Tesla ist die Top-Holding im Flaggschiff ETF ARK Innovation und ist ebenfalls die größte Beteiligung in zwei weiteren ARK-ETFs: Dem Ark Autonomous Technology & Robotics ETF und dem Ark Next Generation Internet ETF. Insgesamt befinden sich nun noch 4.873.916 Tesla-Aktien in den ETFs von ARK Invest, der Gesamtwert des Investments belief sich zuletzt auf rund 3,3 Milliarden US-Dollar. Tesla von falschen Analysten falsch bewertet Dass der Teil-Verkauf von Tesla-Aktien den Langzeit-Bullen Wood an dem Elektroautobauer zweifeln lässt, ist allerdings nicht anzunehmen. Noch vor Veröffentlichung der Quartalsbilanz von Tesla hatte Wood in einem Interview ihr Basis-Kursziel von 3.000 US-Dollar für die Tesla-Aktie bestätigt. Gegenüber \"Real Vision\" nahm die Investorin dabei auch Tesla-Analysten ins Visier, die ihrer Meinung nach mit dafür verantwortlich sind, dass Tesla am Markt falsch bewertet wird: \"Wir glauben, dass der Grund für eine so große Ineffizienz bei Teslas Bewertung der kurzfristige Zeithorizont der Analysten ist und die Tatsache, dass die falschen Analysten folgen\". Sie betonte, dass Tesla mehrheitlich von Auto-Analysten bewertet werde, dabei sei der Konzern von Elon Musk ein \"facettenreiches Technologieunternehmen\". Bei ARK hab man eine andere Herangehensweise, um die Aktie von Tesla korrekt bewerten zu können: \"Tesla ist ein Technologieunternehmen, aber nicht nur ein Technologieunternehmen\", sagte sie und nannte in dem Zusammenhang auch Energiespeicher, Robotik, künstliche Intelligenz und Software-as-a-Service. \"Wir haben also drei Analysten, die das Tesla-Modell zusammenbauen\", erklärte sie. ARK investiert in Innovation Die Investmentgesellschaft der Starinvestorin hat sich vorrangig auf die Marktsegmente Digitalisierung und Technologie konzentriert und das Portfolio ihrer ETFs konsequent darauf ausgerichtet. Der Fokus hat dafür gesorgt, dass ARK in den vergangenen Jahren eine starke Rendite erwirtschaften konnte und im vergangenen Jahr auch Investorenlegende Warren Buffett und seiner Holding Berkshire Hathaway den Rang abgelaufen hatte.",
#     "rights": "klamm.de",
#     "rank": 7420,
#     "topic": "news",
#     "country": "unknown",
#     "lan": "de",
#     "authors": [],
#     "media": "https://static.klamm.de/news/news-img-k.jpg",
#     "is_opinion": False,
#     "twitter_account": None,
#     "_score": 13.178295,
#     "_id": "e3c5e3a88c985a015b6051812198670d"
#     }

# preprocessing some fields.
nc_author = Author.from_json(dict(name=news_catcher_article['author']))
news_catcher_article['author'] = [nc_author.to_dict()]
nc_article = Article.from_json(news_catcher_article, mapping=dict(namefromapi="name"))
a = Article()
a.author=[author]
pass