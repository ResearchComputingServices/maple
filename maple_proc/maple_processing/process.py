"""functions to extract information from articles."""
import logging
import re
import heapq
import asyncio
import aiohttp
import nltk
from openai import AsyncOpenAI, api_key
from maple_structures import Article


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
        

async def chatgpt_summary_v2(prompt, content: str, api_key: str):
    client = AsyncOpenAI(api_key=api_key)
    
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role":"user",
                "content": f"{prompt} '{content}'",
            },
        ],
        timeout = 40,
    )
    return completion.choices[0].message.content

async def chatgpt_summary(content: str, api_key: str):
    client = AsyncOpenAI(api_key=api_key)
    
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role":"user",
                "content": f"summarize in less than 300 words the following content: '{content}'",
            },
        ],
        timeout = 40,
    )
    return completion.choices[0].message.content

default_prompts = {
    'summary': "summarize in less than 300 words the following content: ",
}

async def chatgpt_topic_name(keywords: list[str], api_key: str):
    client = AsyncOpenAI(api_key=api_key)
       
    content = ', '.join(keywords)
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role":"user",
                "content": f"In two words represent this: '{content}.'",
            },
        ],
        timeout = 40,
    )
    return completion.choices[0].message.content


async def chatgpt_bullet_summary(content: list[str], api_key: str):
    client = AsyncOpenAI(api_key=api_key)

    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role":"user",
                "content": f"generate a bullet point summary with a maximum of five bullets and fifthy words per point for the following content: '{content}'",
                # "content": f"generate a list separeted by '\n\n' of bullet point summaries with a maximum of five items and fifthy words per item for the following content: '{content}'",
            },
        ],
        timeout = 40,
    )
    out = completion.choices[0].message.content
    logger.debug("chatgpt bullet summary returned: %s", out)
    return out.split('\n')


async def personalized_summary(
    host: str, 
    port: str, 
    model_type: str,
    content: str, 
    api_key: str | None,
    prompt: str = None,
    timeout: int = 300,
    max_tokens: int = None,
    ):
    headers = {}
    if api_key is not None:
        headers["x-api-key"] = api_key
    if prompt is None:
        prompt = default_prompts["summary"]
        
    body = {
        "model_type": model_type,
        "articles": [content],
        "prompt": prompt,
        }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
        
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.post(
            f"{host}:{port}/llm/article_summary",
            headers=headers,
            timeout=timeout,
            json=body,
            ssl=False,
            ) as response:
            data =  await response.json()
            if len(data) == 0:
                return None
            return data[0]

async def personalized_topic_name(
    host: str, 
    port: str, 
    model_type: str,
    keywords: list[str],
    api_key: str | None,
    prompt: str = None,
    timeout: int = 300,
    max_tokens: int = None,
    ):
    headers = {}
    if api_key is not None:
        headers["x-api-key"] = api_key
        
    # content = ', '.join(keywords)
    body = {
        "model_type": model_type,
        "keywords": keywords,
        "prompt": prompt if prompt is not None else "In two words represent this: ",
        }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
        
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.post(
            f"{host}:{port}/llm/topic_name",
            headers=headers,
            timeout=timeout,
            json=body,
            ssl=False,
            ) as response:
            data =  await response.json()
            if len(data) == 0:
                return None
            return data

async def personalized_bullet_point(host: str, 
    port: str, 
    model_type: str,
    articles: list[str],
    api_key: str | None,
    prompt: str = None,
    timeout: int = 300,
    max_tokens: int = None,):
    headers = {}
    if api_key is not None:
        headers["x-api-key"] = api_key
    body = {
        "model_type": model_type,
        "articles": articles,
        "prompt": prompt,
        }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
        
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.post(
            f"{host}:{port}/llm/bullet_point",
            headers=headers,
            timeout=timeout,
            json=body,
            ssl=False,
            ) as response:
            data =  await response.json()
            if len(data) == 0:
                return None
            return data

class LLMProcess:
    def __init__(self, config:dict):
        self.set_config(config)
    
    def set_config(self, config: dict):
        self._config = config
    
    @property
    def summary_prompt(self):
        prompt = 'You are a reporter. Your task is to create a summary of an article with a limit of 50 words. Do not include any description of the task.'
        if self._config:
            model_name = self.get_model_name()
            if model_name == 'chatgpt':
                if 'chatgpt' in self._config['prompts']:
                    prompt = self._config['prompts']['chatgpt']['summary']
            else:
                if model_name in self._config['prompts']:
                    prompt = self._config['prompts'][model_name]['summary']
                
        return prompt
        
    @property
    def topic_name_prompt(self):
        prompt = 'You are provided with a list of keywords. Your task is to find the best possible word to represent them. Provide at least one word, and a maximum of 3 words.\n# Keywords:\n'
        if self._config:
            model_name = self.get_model_name()
            if model_name == 'chatgpt':
                if 'chatgpt' in self._config['prompts']:
                    prompt = self._config['prompts']['chatgpt']['topic_name']
            else:
                if model_name in self._config['prompts']:
                    prompt = self._config['prompts'][model_name]['topic_name']
        return prompt
    
    @property
    def bullet_summary_prompt(self):
        prompt = "Given the articles, create a list with maximum of 5 bullet points, and each bullet point should not exceed 50 words.\n#Articles:\n"
        if self._config:
            model_name = self.get_model_name()
            if model_name == 'chatgpt':
                if 'chatgpt' in self._config['prompts']:
                    prompt = self._config['prompts']['chatgpt']['bullet_points']
            else:
                if model_name in self._config['prompts']:
                    prompt = self._config['prompts'][model_name]['bullet_points']
        return prompt
    
    def get_model_type(self):
        model_type = 'ChatGPT'
        if self._config:
            if 'model' in self._config:
                if 'name' in self._config['model']:
                    model_type = self._config['model']['name']
        return model_type
    
    def get_model_name(self):
        model_type = self.get_model_type()
        model_name='chatgpt'
        if model_type == 'ChatGPT':
            model_name = model_type
        elif model_type == 'Personalized':
            model_name = self._config['model']['selectedModel']
        return model_name

    def get_api_key(self, api_key: str = None):
        if self._config:
            if self.get_model_type() == 'ChatGPT':
                if 'api_key' in self._config['model']['config']:
                    api_key = self._config['model']['config']['api_key']
            elif self.get_model_type() == 'Personalized':
                if 'api_key' in self._config['model']:
                    api_key = self._config['model']['api_key']
        return api_key
    
    async def get_summary(self, content: str, chatgpt_api_key: str):
        model_type = self.get_model_type()
        if not self._config:
            return await chatgpt_summary_v2(self.summary_prompt, content, api_key=chatgpt_api_key)
        else:
            api_key_ = self.get_api_key(chatgpt_api_key)
            if model_type == 'ChatGPT':
                return await chatgpt_summary_v2(self.summary_prompt, content, api_key=api_key_)
            elif model_type == 'Personalized':
                return await personalized_summary(
                    host=self._config['model']['host'],
                    port=self._config['model']['port'],
                    model_type=self.get_model_name(),
                    content=content,
                    api_key=self.get_api_key(),
                    prompt=self.summary_prompt,
                )
        
    async def get_topic_name(self, keywords: list[str], chatgpt_api_key: str):
        model_type = self.get_model_type()
        if not self._config:
            return await chatgpt_topic_name(keywords, chatgpt_api_key)
        else:
            api_key_ = self.get_api_key(chatgpt_api_key)
            if model_type == 'ChatGPT':
                return await chatgpt_topic_name(keywords, api_key_)
            elif model_type == 'Personalized':
                return await personalized_topic_name(
                    host=self._config['model']['host'],
                    port=self._config['model']['port'],
                    model_type=self.get_model_name(),
                    keywords=keywords,
                    api_key=api_key_,
                    prompt=self.topic_name_prompt,
                )
    
    async def get_bullet_summary(self, content: list[str], chatgpt_api_key: str):
        model_type = self.get_model_type()
        if not self._config:
            return await chatgpt_bullet_summary(content, chatgpt_api_key)
        else:
            api_key_ = self.get_api_key(chatgpt_api_key)
            if model_type == 'ChatGPT':
                return await chatgpt_bullet_summary(content, api_key_)
            elif model_type == 'Personalized':
                return await personalized_bullet_point(
                    host=self._config['model']['host'],
                    port=self._config['model']['port'],
                    model_type=self.get_model_name(),
                    articles=content,
                    api_key=api_key_,
                    prompt=self.bullet_summary_prompt,
                )
        