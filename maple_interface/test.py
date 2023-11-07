import json
from maple_structures import model
from maple_interface import maple
import pprint

# Access the api
maple_api = maple.MapleAPI(authority="http://localhost:3000")

# Create a topic for testing (no model for now)
post = False
if post:
    topic = model.Topic(name='Topic2', keyword='Sample, Topic, API',
                        label="Testing API Topic",
                        dot_summary=[
                            'topic 1 is awesome', 'Completely related to something.'],
                        prevalence=0.50)
    print('Topic:')
    print(json.dumps(topic.to_dict(), indent=2))
    res = maple_api.topic_post(topic)


get = False
put = False
if get:
    topics = maple_api.topic_get()
    t = {}
    for topic in topics:
        print(topic.to_dict())
        t = topic

    if put == True:
        t.label = "Updated label"
        res = maple_api.topic_put(t)
        print(res.to_dict())


# We need to add topic to a model and test
post = False
if post:
    model = model.Model(type='bert', version="v1", level=1,
                        name="Model2", status="created", path="Model path")
    print('Model:')
    print(json.dumps(model.to_dict(), indent=2))
    res = maple_api.model_post(model)
    print(res.to_dict())

get = False
put = False
if get:
    models = maple_api.model_get()
    m = {}
    for model in models:
        print(model.to_dict())
        m = model

    if put == True:
        print("..................................\n")
        m.status = "complete"
        print(m.to_dict())
        res = maple_api.model_put(m)
        print(res.to_dict())


# ======================================================================================
# Testing topic and model
# Create topic
post = False
if post:
    topic1 = model.Topic(name='TopicNov06_1', keyword='Sample, Topic, API',
                         label="Testing API Topic",
                         dot_summary=[
                             'Testing topic and model - 1', 'Testing post and get - 1'],
                         prevalence=0.50)

    topic2 = model.Topic(name='TopicNov06_2', keyword='Sample, Topic, API',
                         label="Testing API Topic",
                         dot_summary=[
                             'Testing topic and model - 2', 'Testing post and get - 2'],
                         prevalence=0.50)

    model = model.Model(name="ModelNov06", type='bert',
                        level=1, status='created', path='')
    topic1.model = model
    topic2.model = model
    model.add_topic(topic1)
    model.add_topic(topic2)

    print(model.to_dict(include_topic=True))
    json.dump(
        model.to_dict(include_topic=True), open('scripts/dummy.json', 'w'), indent=2)

    res = maple_api.model_post(model, include_topic=True)
    print(res.to_dict())


get = False
put = False
if get:
    models = maple_api.model_get()
    m = {}
    for model in models:
        pprint.pprint(model.to_dict(include_topic=True))
        m = model

    if put == True:
        print("..................................\n")
        m.name = "Topic Nov 06 - 1"
        res = maple_api.model_put(m)
        pprint.pprint(res.to_dict())


# ==============================================================================================================
post = True
if post:
    topic1 = model.Topic(name='Topic Nov06_1', keyword='Sample, Topic, API',
                         label="Testing API Topic",
                         dot_summary=[
                             'Testing topic and model - 1', 'Testing post and get - 1'],
                         prevalence=0.50)

    topic2 = model.Topic(name='Topic Nov06_2', keyword='Sample, Topic, API',
                         label="Testing API Topic",
                         dot_summary=[
                             'Testing topic and model - 2', 'Testing post and get - 2'],
                         prevalence=0.50)

    model1 = model.Model(name="Model Nov06", type='bert',
                         level=1, status='created', path='')
    topic1.model = model1
    topic2.model = model1
    model1.add_topic(topic1)
    model1.add_topic(topic2)

    model_it1 = model.ModelIteration(
        name='Model It 1 Nov 06', type='bert', article_trained=3000, article_classified=1000, model_level1=model1)
    # print('Model:')
    # print(json.dumps(model_it1.to_dict(), indent=2))
    res = maple_api.model_iteration_post(
        model_it1, include_model=True, include_topic=True)

    pprint.pprint(res.to_dict())


get = False
put = False
if get:
    m_its = maple_api.model_iteration_get()
    for it in m_its:
        d = it.to_dict()
        pprint.pprint(d)

    if put == True:
        print("..................................\n")
        it.article_classified = 200
        pprint.pprint(it.to_dict())
        res = maple_api.model_iteration_put(it)
        pprint.pprint(res.to_dict())


delete = False
uuid = "88380d98-01f6-4272-b8c0-d4119d964588"
if delete:
    res = maple_api.model_delete(uuid)
    pprint.pprint(res.to_dict())


delete = True
uuid = "8953b0c8-f7ae-4d2a-86b8-881b3c0c81fe"
if delete:
    res = maple_api.model_iteration_delete(uuid)
    pprint.pprint(res.to_dict())
