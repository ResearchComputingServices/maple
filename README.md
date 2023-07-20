# Maple project 

The goal of this project is to retrieve news data and public opinion on relevant topics in Canada. Important information about these topics can provide relevant information for decision makers and public policy administrators.

Our team have been investigating and implementing different tools to achieve these goals. Below are the tools investigated so far. 

## Youtube - Tool developed by RCS

We can retrieve videos’ metadata and the comments for those videos for any channel in YouTube. We are also able to retrieve the video’s transcripts but those are automatically generated. 

The tool is not only limited to News, and can be used to any channel. The following list contains the Canadian News channels investigated so far:
- CBCNews
- Global News
- CTV News
- CityNews
- CBCNews: The national
- NationalPost
- The Globe and Mail
- Montreal Gazette
- Toronto Sun
- CP 24
- Edmonton Journal
- The Province
- LeDevoir
- The London Free Press
- Toronto Star
- Vancouver Sun
- Ottawa Citizen
- Radio Canada Info 
- LeSoleil
- LaTribune
- Winnipeg Sun
- Calgary Sun

### Sample
The following files are samples of retrieved data from Youtube:

- [sample of transcript for a video](sample/Affordable_housing_projects_go_green_WGpe9FSB6eU.txt)
- [sample of videos metadata for a list of channels](sample/2023_07_14_all_videos_by_channels.xlsx)
- [sample of comments for videos](sample/2023_07_14_file__comments_commenters.xlsx)

## APIs - Investigation of third party tools to query news

<table>
<tr>
<th>Name</th>
<th>Price</th>
<th>Request</th>
<th>Example output</th>
</tr>
<tr>
<td> <a href="https://newscatcherapi.com/"> NewsCatcher API </a></td>
<td> Free 30 days trial, then min $399/mo</td>
<td>

[search documentation](https://docs.newscatcherapi.com/api-docs/endpoints-1/search-news)
</td>
<td>

```json
{
    "status": "ok",
    "total_hits": 10000,
    "page": 1,
    "total_pages": 5000,
    "page_size": 2,
    "articles": [
        {
            "title": "ARK reduziert Anteile: Cathie Wood wirft Tesla-Aktien aus dem Depot",
            "author": null,
            "published_date": "2021-08-04 01:15:00",
            "published_date_precision": "full",
            "link": "https://www.finanzen.net/nachricht/aktien/beteiligung-reduziert-ark-reduziert-anteile-cathie-wood-wirft-tesla-aktien-aus-dem-depot-10402608",
            "clean_url": "finanzen.net",
            "excerpt": "• ARK Invest verkauft Tesla-Anteile im Wert von 43,7 Millionen US-Dollar • Tesla-Aktie bleibt Top-Holding in drei ETFs • Cathie Wood sieht Tesla-Aktie falsch ...",
            "summary": "• ARK Invest verkauft Tesla-Anteile im Wert von 43,7 Millionen US-Dollar• Tesla-Aktie bleibt Top-Holding in drei ETFs• Cathie Wood sieht Tesla-Aktie falsch bewertet Die starke Entwicklung der Tesla-Aktie im Jahr 2020 war einer der Hauptwachstumstreiber in den ETFs der Investmentfirma ARK Invest. Im April hatte das Unternehmen bei einem Aktienpreis von rund 719 US-Dollar dann zuletzt einige Tesla-Aktien aus dem Depot geworfen, jetzt war es erneut soweit. Tesla-Aktien verkauft: 43,7 Millionen US-Dollar eingenommen ARK veräußerte 63.643 Tesla-Aktien und hat bei dem Verkauf 43,7 Millionen US-Dollar eingenommen, das geht aus dem Trading-Update des Unternehmens hervor. Tesla ist die Top-Holding im Flaggschiff ETF ARK Innovation und ist ebenfalls die größte Beteiligung in zwei weiteren ARK-ETFs: Dem Ark Autonomous Technology & Robotics ETF und dem Ark Next Generation Internet ETF. Insgesamt befinden sich nun noch 4.873.916 Tesla-Aktien in den ETFs von ARK Invest, der Gesamtwert des Investments belief sich zuletzt auf rund 3,3 Milliarden US-Dollar. Tesla von falschen Analysten falsch bewertet Dass der Teil-Verkauf von Tesla-Aktien den Langzeit-Bullen Wood an dem Elektroautobauer zweifeln lässt, ist allerdings nicht anzunehmen. Noch vor Veröffentlichung der Quartalsbilanz von Tesla hatte Wood in einem Interview ihr Basis-Kursziel von 3.000 US-Dollar für die Tesla-Aktie bestätigt. Gegenüber \"Real Vision\" nahm die Investorin dabei auch Tesla-Analysten ins Visier, die ihrer Meinung nach mit dafür verantwortlich sind, dass Tesla am Markt falsch bewertet wird: \"Wir glauben, dass der Grund für eine so große Ineffizienz bei Teslas Bewertung der kurzfristige Zeithorizont der Analysten ist und die Tatsache, dass die falschen Analysten folgen\". Sie betonte, dass Tesla mehrheitlich von Auto-Analysten bewertet werde, dabei sei der Konzern von Elon Musk ein \"facettenreiches Technologieunternehmen\". Bei ARK hab man eine andere Herangehensweise, um die Aktie von Tesla korrekt bewerten zu können: \"Tesla ist ein Technologieunternehmen, aber nicht nur ein Technologieunternehmen\", sagte sie und nannte in dem Zusammenhang auch Energiespeicher, Robotik, künstliche Intelligenz und Software-as-a-Service. \"Wir haben also drei Analysten, die das Tesla-Modell zusammenbauen\", erklärte sie. ARK investiert in Innovation Die Investmentgesellschaft der Starinvestorin hat sich vorrangig auf die Marktsegmente Digitalisierung und Technologie konzentriert und das Portfolio ihrer ETFs konsequent darauf ausgerichtet. Der Fokus hat dafür gesorgt, dass ARK in den vergangenen Jahren eine starke Rendite erwirtschaften konnte und im vergangenen Jahr auch Investorenlegende Warren Buffett und seiner Holding Berkshire Hathaway den Rang abgelaufen hatte.",
            "rights": "klamm.de",
            "rank": 7420,
            "topic": "news",
            "country": "unknown",
            "language": "de",
            "authors": [],
            "media": "https://static.klamm.de/news/news-img-k.jpg",
            "is_opinion": false,
            "twitter_account": null,
            "_score": 13.178295,
            "_id": "e3c5e3a88c985a015b6051812198670d"
        },
        {
            "title": "How much does a Tesla weigh? Comparing each model",
            "author": "Scooter Doll",
            "published_date": "2021-08-02 08:23:00",
            "published_date_precision": "full",
            "link": "https://electrek.co/2021/08/02/how-much-does-a-tesla-weigh-comparing-each-model",
            "clean_url": "electrek.co",
            "excerpt": "When learning more about Tesla and its growing fleet of EVs, consumers new to the market have a lot of the same questions. Inquiries such as How much does a Tesla cost? How long does it take to charge a Tesla? How much does it cost to charge a Tesla? Believe it or not, one of the most frequent questions we receive in addition to those above is, How much does a Tesla weigh? \nWhile this question is more easily answered than others, there are a few factors that play a role in the weight of each Tesla model. Here's everything you need to know broken down by model.\n more…\nThe post How much does a Tesla weigh? Comparing each model appeared first on Electrek.",
            "summary": "When learning more about Tesla and its growing fleet of EVs, consumers new to the market have a lot of the same questions. Inquiries such as How much does a Tesla cost? How long does it take to charge a Tesla? How much does it cost to charge a Tesla? Believe it or not, one of the most frequent questions we receive in addition to those above is, How much does a Tesla weigh?\n\nWhile this question is more easily answered than others, there are a few factors that play a role in the weight of each Tesla model. Here's everything you need to know broken down by model.\n\nHow much does each Tesla weigh?\n\nUnfortunately, your Tesla does not get an annual physical where a doctor can check in on your EV's weight, and there aren't too many vehicle-sized scales easily accessible to drivers.\n\nLuckily, Tesla has provided the weights of most of its vehicles, but they're still are varying factors.\n\nAside from different model types, some Teslas can vary in weight based on their trim or powertrain. Electric motors aren't as heavy ICE engine blocks, but they do carry some weight around.\n\nThat being said, more performance means more electric motors, and more motors mean additional weight.\n\nThe size and cargo space of the Tesla itself is also a pretty obvious factor, as a Model X will certainly weigh more than a Model 3 — and pretty much any other Tesla at this point.\n\nBelow is each Tesla's weight according to the American automaker, sorted by chronological debut.\n\nTesla's original Roadster EV\n\nTesla Roadster\n\nTesla's flagship EV remains its lightest model to date. The original Tesla Roadster sits as a limited-run EV and is now a collector's item for some, so its weight has not changed in the decade it's been around.\n\nThe first-generation Roadster weighs in at 2,723 lbs.\n\nModel S\n\nThe second oldest Tesla model on our list and the longest currently in production is the Model S sedan. After seeing a refresh earlier in 2021 that will eventually bring the tri-motor Plaid powertrain to drivers, the Model S can come with some weight.\n\nThe dual-motor Long Range trim, which has now been delayed to 2022, weighs 4,561 lbs.\n\nThe tri-motor Plaid Model S will weigh in at 4,766 lbs. when it (hopefully) delivers this fall.\n\nModel X\n\nThe largest current Tesla is unsurprisingly also the heaviest to date (we're still waiting on you, Cybertruck).\n\nCurrently available in two different trims, both the Long Range and new Plaid Model X weigh more than any of their Tesla siblings.\n\nThe Model X Long Range weighs 5,185 lbs., while the Plaid Model X and its three motors will weigh 5,390 lbs. Both trims are currently scheduled to arrive in the first quarter of 2022 alongside the Long Range Model S.\n\nModel 3\n\nThe cheapest Tesla available is also one of the very lightest, no matter the powertrain you choose. The Tesla Model 3 is currently available in three trims:\n\nThe single motor Model 3 Standard Range Plus is the second-lightest Tesla ever at 3,582 lbs.\n\nThe other two dual-motor Model 3 trims, Long Range and Performance, both weigh in at 4,065 lbs.\n\nModel Y\n\nThe newest Tesla to arrive currently sits in the middle of the pack on weight, which sits on brand with its pricing and performance as well.\n\nThe Tesla Model Y is currently available in either a Long Range or Performance dual-motor trim, and each weighs 4,416 lbs.\n\nWhat is the heaviest Tesla?\n\nIf you've skimmed through to this point, you must just be looking for weights and an answer to the question above without all the jibber-jabber. We respect that, so here you go.\n\nHere are all of Tesla's current models sorted heaviest to lightest:\n\n5,390 lbs – Model X Plaid\n\n5,185 lbs – Model X Long Range\n\n4,766 lbs – Model S Plaid\n\n4,561 lbs – Model S Long Range\n\n4,416 lbs – Model Y Long Range/Performance\n\n4,065 lbs – Model 3 Long Range/Performance\n\n3,582 lbs – Model 3 Standard Range Plus\n\n2,723 lbs Gen. 1 Tesla Roadster\n\nHow much does Tesla Cybertruck weigh?\n\nUnfortunately, we do not have that granular of specs on the upcoming Tesla Cybertruck yet, although we have asked Tesla several times.\n\nBased on the increased size and payload capacity (at least 3,500 lbs) compared to the current largest Tesla in the Model X, we anticipate the weight of the three upcoming powertrains on the Cybertruck to be between 5,000 and 6,500 lbs.\n\nThat being said, towing capacities up to 14,000 lbs., like Tesla is advertising for the tri-motor Cybertruck, could very well require more weight beyond 6,500 lbs.\n\nCheck back in with our Cybertruck guide periodically for the latest specs from Tesla.\n\nHow much does the 2nd generation Tesla Roadster weigh?\n\nMuch like the Cybertruck, Tesla has not yet revealed what the second-generation Roadster will tip the scales at when it debuts in 2022.\n\nBased on its size and touted performance, complete with new motors, we'd expect the new Roadster to land somewhere near the upcoming Model S trims, perhaps between 4,400 and 4,700 lbs.\n\nWe will know for certain when Tesla shares more details of the Gen. 2 Roadster… like whether it can actually hover or not.\n\nFTC: We use income earning auto affiliate links. More.\n\nSubscribe to Electrek on YouTube for exclusive videos and subscribe to the podcast.",
            "rights": "electrek.co",
            "rank": 3297,
            "topic": "news",
            "country": "US",
            "language": "en",
            "authors": [
                "Scooter Doll"
            ],
            "media": "https://i1.wp.com/electrek.co/wp-content/uploads/sites/3/2021/08/Tesla-on-a-scale.jpg?resize=1200%2C628&quality=82&strip=all&ssl=1",
            "is_opinion": false,
            "twitter_account": "@electrekco",
            "_score": 13.09692,
            "_id": "b9a2f7cabf9255d7e9ec19c6dc65018d"
        }
    ],
    "user_input": {
        "q": "Tesla",
        "search_in": [
            "title",
            "summary"
        ],
        "lang": null,
        "not_lang": null,
        "countries": null,
        "not_countries": null,
        "from": "2021-08-02 00:00:00",
        "to": null,
        "ranked_only": "True",
        "from_rank": null,
        "to_rank": null,
        "sort_by": "relevancy",
        "page": 1,
        "size": 2,
        "sources": null,
        "not_sources": null,
        "topic": null,
        "published_date_precision": null
    }
}
```

<td>
</tr>
</table>



## Custom spiders - RCS implementation

Spiders can follow news links from a list of websites. Each website has its own implementation and therefore a new spider is required for each website. At this moment, we implemented the CBC spider to go over news based on localities.

### CBC

- Fetch news metadata and content for the following localities:
    - British Columbia 
    - Calgary 
    - Edmonton 
    - Saskatchewan 
    - Saskatoon 
    - Manitoba 
    - Thunder Bay 
    - Sudbury 
    - Windsor 
    - London 
    - Kitchener-Waterloo 
    - Hamilton 
    - Toronto 
    - Ottawa 
    - Montreal 
    - New Brunswick 
    - Prince Edward Island 
    - Nova Scotia 
    - Newfoundland & Labrador 
    - North 

Here is a sample of a simple entry for the news [Sleep disorders a risk for recent immigrants, say students, professor](https://www.cbc.ca/news/canada/edmonton/sleep-disorders-a-risk-for-recent-immigrants-say-students-professor-1.6910657). A sample file with different outputs can be found in [here](sample/cbcout1.json).


```json
{
    "id": "card-1.6910657",
    "contentId": 3997854,
    "url": "/news/canada/edmonton/sleep-disorders-a-risk-for-recent-immigrants-say-students-professor-1.6910657",
    "itemURL": "https://www.cbc.ca/news/canada/edmonton/sleep-disorders-a-risk-for-recent-immigrants-say-students-professor-1.6910657",
    "departments": {
        "sectionList": [
            "news",
            "canada",
            "edmonton"
        ],
        "sectionLabels": [
            "News",
            "Canada",
            "Edmonton"
        ]
    },
    "category": "edmonton",
    "relatedLinks": [],
    "description": "Some recent immigrants say sleep disorders are widespread in Alberta's international student bodies and in some diaspora communities.\u00a0A sleep researcher at the University of Calgary says newcomers struggle accessing the health-care system.",
    "flag": "",
    "imageURL": "https://i.cbc.ca/1.3406714.1657900886!/fileImage/httpImage/image.jpg_gen/derivatives/16x9_780/nap.jpg",
    "imageAspects": "square_220,16x9_940,16x9_300,16x9_620,original_620,original_300,16x9tight_140,square_140,16x9_780,square_60,16x9_460",
    "publishTime": 1689771600395,
    "updateTime": 1689771600395,
    "sourceId": "1.6910657",
    "source": "Polopoly",
    "sponsorMeta": null,
    "slug": "sleep-disorders-a-risk-for-recent-immigrants-say-students-professor",
    "title": "Sleep disorders a risk for recent immigrants, say students, professor",
    "itemType": "story",
    "show": null,
    "author": {
        "name": "Brendan Coulter",
        "smallImageUrl": "https://i.cbc.ca/1.6903563.1689099544!/fileImage/httpImage/image.jpg_gen/derivatives/square_140/brendan-coulter.jpg"
    },
    "displayComments": false,
    "videoId": null,
    "videoCardOverlayType": "",
    "videoDuration": null,
    "videoAirDate": null,
    "videoTitle": "",
    "external": false,
    "flagId": "f-card-1.6910657",
    "headlineId": "h-card-1.6910657",
    "descriptionId": "d-card-1.6910657",
    "metadataId": "m-card-1.6910657",
    "content": "Saad Iqbal sleeps\u00a0about five hours per night.\u00a0\nIqbal, who moved to Edmonton in 2021 from Pakistan to study at the University of Alberta, is one\u00a0of several recent immigrants who say sleep disorders are widespread in Alberta's international student bodies and in some diaspora communities.\u00a0\n\"It was affecting my attention in the classroom,\" said Iqbal. \"You're very sleepy, you're yawning, so you're not attentive to the conversations that are taking place.\"\nIqbal, vice-president of the U of A's International Students' Association, says time-zone differences, part-time jobs, and adjusting to a new environment all contribute to the difficulty some students face getting rest.\u00a0\n\"The [students] that I have talked to \u2026 go through anxiety and stress,\" he said. \"There's always these different stressors that keep you worried.\"\nHow many hours of shuteye is best? Here's what the latest science says about sleep\nThe University of Alberta supports international students dealing with various personal challenges, and newcomers believe sleeping issues span different communities and institutions.\u00a0\nOne Swiss study\n found immigrants were more likely to face sleep disturbances than non-immigrants because they faced higher levels of emotional distress. \nA\u00a02020 analysis of previously published studies\n\u00a0found migrants and refugees faced a\u00a0greater risk of\u00a0snoring, metabolic diseases, and insomnia.\u00a0\nResearch published in 2019 \nfound that immigrants living in Canada were less likely to report troubled sleep, but authors suggested different cultural interpretations of sleep could be a factor.\u00a0\nSaad Iqbal will begin a PhD program at the University of Alberta in the fall. He said he's grateful for his life and professional opportunities in Canada, but he struggles to get enough sleep. \n \n(Submitted by Saad Iqbal)\nUniversity of Calgary professor and sleep physician Dr. Sachin Pendharkar says newcomers to Canada face challenges in accessing health care in general and may not recognize the importance of healthy sleep habits.\u00a0 \nHe described Alberta's current care model for sleep disorders as \"fragmented,\" with a mix of public and private providers offering different testing through different types of facilities.\u00a0\n\"Patients have a difficult time figuring out where to go for what problem,\" Pendharkar said. \"When you add on to that, there are potentially other barriers related to work or home responsibilities \u2026 they just compound the problem for many [immigrants],\" he said.\u00a0\nPoor sleep is associated with an increased risk of depression, obesity, diabetes, and all-cause mortality, according to Health Canada.\u00a0\nThe Canadian Society for Exercise Physiology recommends between seven and nine hours of sleep per night for adults between 18 and 64.\nStruggling with getting a good night's sleep? You're not alone\nAsylum seekers sleeping on Toronto streets as at-capacity city shelters overwhelmed\nEdmonton resident Eric Awuah says he talks to loved ones in his birth country,\u00a0Ghana, every day over the phone, and those conversations can last from 10 p.m. until midnight.\u00a0Ghana time is six hours ahead of Alberta.\n\"In trying to keep up with family, my mother \u2026 sometimes I have to like forfeit sleep just so I can call when they are up,\" said Awuah, a PhD student at U of A.\nStress levels also drive his sleeping issues, Awuah says.\u00a0\n\"There is a huge cultural responsibility, moral responsibility \u2026 on you as somebody who has immigrated for greener pastures to also be able to support your family back home,\" he said.\u00a0\nAwuah wants more Edmonton residents from Africa to appreciate why getting proper sleep and managing stress levels is important, and to use the free resources that are available.\nCoalition assisting refugees demands action to help asylum seekers sleeping on Toronto streets\nSleep doctors resign from Manitoba's backlog task force, saying proposal was 'completely ignored'\nEdmonton's Africa Centre provides free counselling through a partnership with the Alberta Black Therapists Network.\u00a0\nPsychologist Noreen Sibanda, the network's director, said sleep habits are a good indicator of mental health and other challenges newcomers may be facing.\n\"Having to come to a new place where you don't feel connected \u2026 Finding yourself living in two worlds where your heart is home but you're physically here, and when you do that, sleep is probably impacted,\" she said.\u00a0 \nPendharkar said sleep health needs to be a larger focus for medical schools and in Canadian culture as a whole.\n\"I think there's a real potential for under-recognition and under-diagnosis.\""
},
```
### What is missing and could be implemented
- Retrieve comments for news
- Load more data (dynamically loaded content is not currently implemented)
- Standardize output from multiple websites

### Drawbacks
- The spiders should be constantly maintained
- No queries most of the time, but could be implemented with `downloaded` data

### Advantages
- Free (following 'robots.txt' rules)

### Where we would like to go


Create a standardized output, where spiders for different news websites would populate the fields that are able to be retrieved.

The following is an example of the structure in mind:

```json
{
    "title": "string",
    "authors": [ {"name":"string"}, ],
    "url": "string",
    "content": "string",
    "summary": "string",
    "has_video": "boolena",
    "video_url": ["string"],
    "date_published": "string",
    "date_modified": "string",
    "number_of_comments": "string",
    "has_likes": "boolean",
    "number_of_likes": "string",
    "has_shares":"string",
    "number_of_shares": "int",
    "comments": [
        {
            "author": "string",
            "comment": "string",
            "date_posted": "string",
            "modified": "boolean",
        },
    ],
    "topic": ["string"],
    "language": "string",
    "geographic_location": "string",
    "location_name": ["string"],
    "metadata": {},
}
```
