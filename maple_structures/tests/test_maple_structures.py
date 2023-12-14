import unittest
import logging
from maple_structures import Processed, Topic, Model, ModelIteration, Article
from uuid import uuid4 as uuid
import copy
import json

logger = logging.getLogger('test_maple_tructures')
logging.basicConfig(level=logging.DEBUG)


class TestTopic(unittest.TestCase):

    def setUp(self) -> None:
        self.name = 'Topic1'
        self.dot_summary = [
            'topic 1 is awesome',
            'Completely related to something.']
        self.topic = Topic(name=self.name, dot_summary=self.dot_summary)

    def test_topic_creation(self):
        logger.debug('test topic creation')
        self.assertTrue(isinstance(self.topic, Topic))
        self.assertEqual(self.name, self.topic.name)
        self.assertEqual(self.dot_summary, self.topic.dot_summary)

    def test_topic_to_dict(self):
        logger.debug('test topic.to_dict()')
        logger.debug(self.topic.to_dict())
        true_dict = dict(name=self.name, dot_summary=self.dot_summary)
        self.assertEqual(self.topic.to_dict(), true_dict)
        true_dict['uuid'] = str(uuid())
        self.topic.uuid = true_dict['uuid']
        self.assertEqual(self.topic.to_dict(), true_dict)

    def test_topic_from_dict(self):
        true_dict = dict(
            name=self.name,
            dot_summary=self.dot_summary,
            uuid=str(uuid()),
        )
        topic = Topic.from_dict(true_dict)
        for attribute in ['name', 'dot_summary', 'uuid']:
            self.assertEqual(getattr(topic, attribute), true_dict[attribute])


class TestModel(unittest.TestCase):

    def setUp(self) -> None:
        N_TOPICS = 5
        self.topic_names = [f'topic{i}' for i in range(N_TOPICS)]
        self.topic_dot_summary = [
            [f'dot summary number 1', f'dot summary number 2'] for i in range(N_TOPICS)]
        self.topics = [Topic(name=topic_name, dot_summary=dot_summary)
                       for topic_name, dot_summary in zip(self.topic_names, self.topic_dot_summary)]
        self.model_type = 'bert'
        self.model1 = Model(type=self.model_type)
        for topic in self.topics:
            self.model1.add_topic(topic)
        self.model2 = copy.copy(self.model1)

    def test_model_equality(self):
        logger.debug('Testing model.to_dict()')
        logger.debug(self.model1.to_dict())
        self.assertEqual(self.model1.to_dict(), self.model2.to_dict())
        logger.debug('model.to_dict(include_topic=True)')
        logger.debug('%s', self.model1.to_dict(include_topic=True))
        self.assertEqual(self.model1.to_dict(include_topic=True),
                         self.model2.to_dict(include_topic=True))
        self.assertEqual(self.model1.type, self.model_type)

    def test_model_topic(self):
        self.assertTrue(self.topics[0] in self.model1.topic)


class TestModelIteration(unittest.TestCase):

    def setUp(self) -> None:
        self.model_iteration_name = 'iteration1'
        self.model_iteration_type = 'bert'
        self.model_iteration_article_trained = 2000
        self.model_iteration_article_classified = 20000

        self.model_iteration = ModelIteration(
            name=self.model_iteration_name,
            type=self.model_iteration_type,
            article_trained=self.model_iteration_article_trained,
            article_classified=self.model_iteration_article_classified)
        for level in range(1, 4):
            model_var = f'model_level{level}'
            model = Model(type=self.model_iteration.type, level=level)
            for topic_i in range(5):
                model.add_topic(
                    Topic(
                        name=f'topic_{level}_{topic_i}',
                        dot_summary=[f'dot summary {i}' for i in range(3)]))
            self.model_iteration.add_model_level(model_var, model)

    def test_fields(self) -> None:
        self.assertEqual(self.model_iteration_name, self.model_iteration.name)
        self.assertEqual(self.model_iteration_type, self.model_iteration.type)
        self.assertEqual(self.model_iteration_article_trained,
                         self.model_iteration.article_trained)
        self.assertEqual(self.model_iteration_article_classified,
                         self.model_iteration.article_classified)

    def test_to_dict(self):
        model_iteration_dict = self.model_iteration.to_dict()
        for key in ['model_iteration_name',
                    'model_iteration_type',
                    'model_iteration_article_trained',
                    'model_iteration_article_classified']:
            dictname = key.replace('model_iteration_', '')
            self.assertTrue(dictname in model_iteration_dict,
                            f'missing key {dictname}')
            self.assertEqual(model_iteration_dict[dictname], getattr(
                self.model_iteration, dictname))

    def test_to_dict_with_models(self):
        model_iteration_dict = self.model_iteration.to_dict(
            include_model=True, include_topic=True)
        for key in [f'model_level{i}' for i in range(1, 4)]:
            self.assertTrue(key in model_iteration_dict, f'missing key: {key}')

    def test_from_dict(self):
        model_iteration_dict = self.model_iteration.to_dict()
        model_iteration = ModelIteration.from_dict(model_iteration_dict)
        self.assertEqual(model_iteration.to_dict(), model_iteration_dict)
        logger.debug("Model_iteration from_dict() then to_dict()")
        logger.debug(json.dumps(model_iteration.to_dict(
            include_model=True), indent=2))


class TestProcessed(unittest.TestCase):
    def setUp(self) -> None:

        print('Setup Test Processed')

        t_article = Article()
        t_article.uuid = str(uuid())

        t_modeliteration = ModelIteration()
        t_modeliteration.uuid = str(uuid())

        topics = []
        for level in range(1, 4):
            topic = Topic()
            topic.uuid = str(uuid())
            topics.append(topic)

        self.processed = Processed(
            article=t_article,
            modelIteration=t_modeliteration,
            topic_level1=topics[0],
            topic_level1_prob=0.54,
            topic_level2=topics[1],
            topic_level2_prob=0.45,
            topic_level3=topics[2],
            topic_level3_prob=0.33,
            position=[1, 0.05]
        )

    def test_processed_creation(self):
        logger.debug('test processed creation')
        self.assertTrue(isinstance(self.processed, Processed))

    def test_processed_to_dict(self):
        out = self.processed.to_dict()
        self.assertTrue('uuid' in self.processed.to_dict()
                        ['modelIteration'].keys())

    def test_from_dict(self):
        true_dict = {'article': {'uuid': 'dc17f1e7-30d6-48af-b8b2-ef952d9a4658'}, 'modelIteration': {'uuid': '3980db2b-4469-4c93-adbf-102e415e074e'}, 'topic_level1': {'uuid': '5d37bdd4-02db-41ea-bed0-64e37397ab82'},
                     'topic_level2': {'uuid': '2274726c-a84f-4dfa-84b0-8497c635826c'}, 'topic_level3': {'uuid': 'eb512160-e06e-4049-b8ff-b425e5de9c31'}, 'topic_level1_prob': 0.54, 'topic_level2_prob': 0.45, 'topic_level3_prob': 0.33}
        processed = Processed.from_dict(true_dict)

        self.assertEqual(true_dict, processed.to_dict())
        

if __name__ == '__main__':
    unittest.main()
