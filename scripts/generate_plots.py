import os
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import colormaps
import numpy as np
import pandas as pd
import json
from maple_structures import Article, ModelIteration, Model, Topic, Processed
# matplotlib.use('GTK')

MODEL_ITERATION = '48111ee8-b2ee-49f5-bf75-e536febd1e9f'
MODEL_ITERATION_PATH = f"data/modelIteration/{MODEL_ITERATION}"
PATH = 'data/figures'
FIGSIZE = (8, 8)

os.makedirs(PATH, exist_ok=True)

model_iteration = ModelIteration.from_dict(json.load(
    open(os.path.join(MODEL_ITERATION_PATH, 'model_iteration.json'), 'r')))

articles = []
for article in json.load(open(os.path.join(MODEL_ITERATION_PATH, 'article.json'), 'r')):
    articles.append(Article.from_dict(article))

processed = []
proc_art_map = {}
for processed_item in json.load(open(os.path.join(MODEL_ITERATION_PATH, 'processed.json'), 'r')):
    proc_obj = Processed.from_dict(processed_item)
    processed.append(proc_obj)
    # for article in articles:
    #     if article.uuid == proc_obj.article.uuid:
    #         proc_art_map[proc_obj] = article
    


    
def figpath(path: str):
    return os.path.join(PATH, path)

per_level = dict()
for level in range(1,4):
    # for model in [ for level in range(1,4)]:
    model = getattr(model_iteration, f'model_level{level}')
    proc_topic_map = {}
    for proc in processed:
        for topic in model.topic:
            if getattr(proc, f'topic_level{level}').uuid == topic.uuid:
                proc_topic_map[proc] = topic
    per_level[level] = dict()
    per_level[level]['proc_topic_map'] = proc_topic_map

allx, ally = [], []
for proc in processed:
    allx.append(proc.position[0])
    ally.append(proc.position[1])

for level in range(1,4):
    proc_topic_map = per_level[level]['proc_topic_map']
    fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)
    ax.set_axis_off()
    ax.set_xlim([np.min(allx)-0.5*np.std(allx), np.max(allx)+0.5*np.std(allx)])
    ax.set_ylim([np.min(ally)-0.5*np.std(ally), np.max(ally)+0.5*np.std(ally)])
    x, y, c = [], [], []
    
    for proc in processed:
        if proc_topic_map[proc].index != -1:
            x.append(proc.position[0])
            y.append(proc.position[1])
            c.append(proc_topic_map[proc].index)
    
    cmap=colormaps['inferno']
    colors = cmap((np.array(c)+1)/np.max(np.array(c)+1))
    ax.scatter(x,y, c = colors, norm = matplotlib.colors.Normalize(0, np.max(c)))
    # ax.set_title(f'{len(set(c))}')
    fig.savefig(figpath(f'level{level}_.png'))
    
    
    for topic_index in set(c):
        topic_color = colors.copy()
        topic_color[:,3] = 0.1
        topic_color[np.array(c) == topic_index, 3] = 1
        
        ax.cla()
        ax.scatter(x,y,c=topic_color)
        ax.set_xlim([np.min(allx)-0.5*np.std(allx), np.max(allx)+0.5*np.std(allx)])
        ax.set_ylim([np.min(ally)-0.5*np.std(ally), np.max(ally)+0.5*np.std(ally)])
        ax.set_axis_off()
        fig.savefig(figpath(f'leve_{level}_topic_{topic_index}.png'))
    plt.close('all')

# barplot per level
for level in range(1,4):
    fig, ax = plt.subplots(1,1,figsize = (4,3))
    topics = getattr(model_iteration, f'model_level{level}').topic
    topics = [topic for topic in topics if topic.index >=0]
    data = []
    for topic in topics:
        data.append(dict(
            prevalence = [topic.prevalence],
            index= [topic.index],
            label= [topic.label]
        ))
    df = pd.concat([pd.DataFrame.from_dict(dt) for dt in data]).sort_values('prevalence', ascending=False)
    ax.bar(df.label, df.prevalence)
    plt.xticks(rotation=30)
    ax.set_ylabel('Training prevalence')
    fig.suptitle('Topic prevalence')
    fig.tight_layout()
    plt.savefig(figpath(f'level_{level}_barplot.png'))
    plt.close('all')


topic_map = dict()

for level in range(1,4):
    topic_map[level]=dict()
    topics = getattr(model_iteration, f'model_level{level}').topic
    for topic in topics:
        topic_map[topic.uuid] = topic
        topic_map[level][topic.index]=topic
    
data = []
for level in range(1,4):
    for proc in processed:
        topic = topic_map[getattr(proc,f'topic_level{level}').uuid]
        data.append(dict(
            date = [proc.article.createDate],
            level = [level],
            topic_name = [topic.label],
            topic_index = [topic.index],
        ))
df = pd.concat([pd.DataFrame.from_dict(dt) for dt in data]).reset_index()
df['createDate'] = pd.to_datetime(df['date'])

for level in range(1,4):
    groups = df[df.level==level].set_index('createDate').sort_index().groupby('topic_index').rolling('1D').count()
    # df[df.level==1].set_index('createDate').sort_index().groupby('topic_index').rolling('1D').count().loc[-1].resample('1D').max().level
    topic_indexes = df[df.level==level].topic_index.unique()
    for topic_i in topic_indexes:
        fig, ax = plt.subplots(1,1,figsize=(4,3))
        # ax.plot(groups.loc[topic_i].resample('7D').mean().level)
        maxval = groups.loc[topic_i].resample('1D').max().dropna()
        ax.bar(maxval.index, maxval.level)
        ax.plot(maxval.index, maxval.rolling('4D').median().level, c='red')
        plt.xticks(rotation=30)
        fig.suptitle(','.join(topic_map[level][topic_i].keyword))
        fig.tight_layout()
        plt.savefig(figpath(f'level_{level}_topictime_{topic_i}.png'))
        plt.close('all')

pass
