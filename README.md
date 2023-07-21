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

[Sample Data](./jsonSamples/NewsAPI_JSON.md)

<table>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<th>Name</th>
<th>Price</th>
<th>Request</th>
<th>Example output</th>
<th>Sources</th>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td> <a href="https://newscatcherapi.com/"> NewsCatcher API </a></td>
<td> Free 30 days trial, then min $399/mo</td>
<td> <a href="https://docs.newscatcherapi.com/api-docs/endpoints-1/search-news"> Documentaion </a></td>
<td>[Sample Data](jsonSample/NewsCatcherAPI_JSON)</td>
<td>1000+
[Source List](sources/NewsCatcherAPI.md)</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>NewsAPI</td>
<td>Free,
$449/mnth,
$1749/mnth
</td>
<td>
<a href="https://newsapi.org/docs"> Documentation </a></td>
<td>[Sample Data](./jsonSamples/NewsAPI_JSON.md)</td>
<td>Sources</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>GNews</td>
<td>Free, 
$49/mnth, 
$99/mnth</td>
<td> <a href="https://gnews.io/docs/v4#introduction"> Documentation</a></td>
<td>[Sample Data](./jsonSamples/GNewsAPI_JSON.md)</td>
<td>---</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>NewsomaticAPI</td>
<td>49 cents / article, 
custom</td>
<td><a href="https://www.newsomaticapi.com/sources/"> Documentation</a></td>
<td>No Free API Key</td>
<td>~20
<a href="https://www.newsomaticapi.com/sources/"> Source List </a>
</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>NewsX API</td>
<td>Price</td>
<td></td>
<td>No Free API Key</td>
<td>5,000  Sources</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>News Article Data Extract and Summarization API</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>News Sentiment API</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>MrNewsAPI</td>
<td>---</td>
<td>---</td>
<td>---</td>
<td>---</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>NewsData.io</td>
<td>Free,
$99/mnth,
$199/mnth,
$599/mnth</td>
<td><a href="https://newsdata.io/documentation"> Documentation </a></td>
<td>[Sample Data](jsonSample/NewsDataIO_JSON.md)</td>
<td>100+ 
[Source List](sources/NewsDataIO.md)
</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->
<tr>
<td>MediaStack</td>
<td>Free,
$25/mnth,
$100/mnth,
$250/mnth</td>
<td><a href="https://mediastack.com/documentation"> Documentation </a></td>
<td>[Sample Data](jsonSample/)</td>
<td>10s
[Source List](sources/MediaStack.md)
</td>
</tr>
<!-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ -->

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
