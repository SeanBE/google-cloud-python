# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest


class TestClient(unittest.TestCase):
    PROJECT = 'PROJECT'
    TOPIC_NAME = 'topic_name'
    TOPIC_PATH = 'projects/%s/topics/%s' % (PROJECT, TOPIC_NAME)
    SUB_NAME = 'subscription_name'
    SUB_PATH = 'projects/%s/subscriptions/%s' % (PROJECT, SUB_NAME)

    def _getTargetClass(self):
        from google.cloud.pubsub.client import Client
        return Client

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_publisher_api_wo_gax(self):
        from google.cloud.pubsub.connection import _PublisherAPI
        from google.cloud.pubsub import client as MUT
        from google.cloud._testing import _Monkey
        creds = _Credentials()

        with _Monkey(MUT, _USE_GAX=False):
            client = self._makeOne(project=self.PROJECT, credentials=creds)

        conn = client.connection = object()
        api = client.publisher_api

        self.assertIsInstance(api, _PublisherAPI)
        self.assertIs(api._connection, conn)
        # API instance is cached
        again = client.publisher_api
        self.assertIs(again, api)

    def test_no_gax_ctor(self):
        from google.cloud._testing import _Monkey
        from google.cloud.pubsub.connection import _PublisherAPI
        from google.cloud.pubsub import client as MUT

        creds = _Credentials()
        with _Monkey(MUT, _USE_GAX=True):
            client = self._makeOne(project=self.PROJECT, credentials=creds,
                                   use_gax=False)

        self.assertFalse(client._use_gax)
        api = client.publisher_api
        self.assertIsInstance(api, _PublisherAPI)

    def test_publisher_api_w_gax(self):
        from google.cloud.pubsub import client as MUT
        from google.cloud._testing import _Monkey

        wrapped = object()
        _called_with = []

        def _generated_api(*args, **kw):
            _called_with.append((args, kw))
            return wrapped

        class _GaxPublisherAPI(object):

            def __init__(self, _wrapped, client):
                self._wrapped = _wrapped
                self._client = client

        creds = _Credentials()

        with _Monkey(MUT, _USE_GAX=True,
                     make_gax_publisher_api=_generated_api,
                     GAXPublisherAPI=_GaxPublisherAPI):
            client = self._makeOne(project=self.PROJECT, credentials=creds)
            api = client.publisher_api

        self.assertIsInstance(api, _GaxPublisherAPI)
        self.assertIs(api._wrapped, wrapped)
        self.assertIs(api._client, client)
        # API instance is cached
        again = client.publisher_api
        self.assertIs(again, api)
        args = (client.connection,)
        self.assertEqual(_called_with, [(args, {})])

    def test_subscriber_api_wo_gax(self):
        from google.cloud.pubsub.connection import _SubscriberAPI
        from google.cloud.pubsub import client as MUT
        from google.cloud._testing import _Monkey
        creds = _Credentials()

        with _Monkey(MUT, _USE_GAX=False):
            client = self._makeOne(project=self.PROJECT, credentials=creds)

        conn = client.connection = object()
        api = client.subscriber_api

        self.assertIsInstance(api, _SubscriberAPI)
        self.assertIs(api._connection, conn)
        # API instance is cached
        again = client.subscriber_api
        self.assertIs(again, api)

    def test_subscriber_api_w_gax(self):
        from google.cloud.pubsub import client as MUT
        from google.cloud._testing import _Monkey

        wrapped = object()
        _called_with = []

        def _generated_api(*args, **kw):
            _called_with.append((args, kw))
            return wrapped

        class _GaxSubscriberAPI(object):

            def __init__(self, _wrapped):
                self._wrapped = _wrapped

        creds = _Credentials()

        with _Monkey(MUT, _USE_GAX=True,
                     make_gax_subscriber_api=_generated_api,
                     GAXSubscriberAPI=_GaxSubscriberAPI):
            client = self._makeOne(project=self.PROJECT, credentials=creds)
            api = client.subscriber_api

        self.assertIsInstance(api, _GaxSubscriberAPI)
        self.assertIs(api._wrapped, wrapped)
        # API instance is cached
        again = client.subscriber_api
        self.assertIs(again, api)
        args = (client.connection,)
        self.assertEqual(_called_with, [(args, {})])

    def test_iam_policy_api(self):
        from google.cloud.pubsub.connection import _IAMPolicyAPI
        creds = _Credentials()
        client = self._makeOne(project=self.PROJECT, credentials=creds)
        conn = client.connection = object()
        api = client.iam_policy_api
        self.assertIsInstance(api, _IAMPolicyAPI)
        self.assertIs(api._connection, conn)
        # API instance is cached
        again = client.iam_policy_api
        self.assertIs(again, api)

    def test_list_topics_no_paging(self):
        from google.cloud.pubsub.topic import Topic

        creds = _Credentials()
        client = self._makeOne(project=self.PROJECT, credentials=creds)
        client.connection = object()
        api = _FauxPublisherAPI(items=[Topic(self.TOPIC_NAME, client)])
        client._publisher_api = api

        iterator = client.list_topics()
        topics = list(iterator)
        next_page_token = iterator.next_page_token

        self.assertEqual(len(topics), 1)
        self.assertIsInstance(topics[0], Topic)
        self.assertEqual(topics[0].name, self.TOPIC_NAME)
        self.assertIsNone(next_page_token)

        self.assertEqual(api._listed_topics, (self.PROJECT, None, None))

    def test_list_topics_with_paging(self):
        from google.cloud.pubsub.topic import Topic

        TOKEN1 = 'TOKEN1'
        TOKEN2 = 'TOKEN2'
        SIZE = 1
        creds = _Credentials()
        client = self._makeOne(project=self.PROJECT, credentials=creds)
        client.connection = object()
        api = _FauxPublisherAPI([Topic(self.TOPIC_NAME, client)], TOKEN2)
        client._publisher_api = api

        iterator = client.list_topics(SIZE, TOKEN1)
        topics = list(iterator)
        next_page_token = iterator.next_page_token

        self.assertEqual(len(topics), 1)
        self.assertIsInstance(topics[0], Topic)
        self.assertEqual(topics[0].name, self.TOPIC_NAME)
        self.assertEqual(next_page_token, TOKEN2)

        self.assertEqual(api._listed_topics, (self.PROJECT, 1, TOKEN1))

    def test_list_topics_missing_key(self):
        creds = _Credentials()
        client = self._makeOne(project=self.PROJECT, credentials=creds)
        client.connection = object()
        api = _FauxPublisherAPI()
        client._publisher_api = api

        iterator = client.list_topics()
        topics = list(iterator)
        next_page_token = iterator.next_page_token

        self.assertEqual(len(topics), 0)
        self.assertIsNone(next_page_token)

        self.assertEqual(api._listed_topics, (self.PROJECT, None, None))

    def test_list_subscriptions_no_paging(self):
        from google.cloud.pubsub.subscription import Subscription
        SUB_INFO = {'name': self.SUB_PATH, 'topic': self.TOPIC_PATH}
        creds = _Credentials()
        client = self._makeOne(project=self.PROJECT, credentials=creds)
        client.connection = object()
        api = client._subscriber_api = _FauxSubscriberAPI()
        api._list_subscriptions_response = [SUB_INFO], None

        subscriptions, next_page_token = client.list_subscriptions()

        self.assertEqual(len(subscriptions), 1)
        self.assertIsInstance(subscriptions[0], Subscription)
        self.assertEqual(subscriptions[0].name, self.SUB_NAME)
        self.assertEqual(subscriptions[0].topic.name, self.TOPIC_NAME)
        self.assertIsNone(next_page_token)

        self.assertEqual(api._listed_subscriptions,
                         (self.PROJECT, None, None))

    def test_list_subscriptions_with_paging(self):
        from google.cloud.pubsub.subscription import Subscription
        SUB_INFO = {'name': self.SUB_PATH, 'topic': self.TOPIC_PATH}
        creds = _Credentials()
        client = self._makeOne(project=self.PROJECT, credentials=creds)
        ACK_DEADLINE = 42
        PUSH_ENDPOINT = 'https://push.example.com/endpoint'
        SUB_INFO = {'name': self.SUB_PATH,
                    'topic': self.TOPIC_PATH,
                    'ackDeadlineSeconds': ACK_DEADLINE,
                    'pushConfig': {'pushEndpoint': PUSH_ENDPOINT}}
        TOKEN1 = 'TOKEN1'
        TOKEN2 = 'TOKEN2'
        SIZE = 1
        client.connection = object()
        api = client._subscriber_api = _FauxSubscriberAPI()
        api._list_subscriptions_response = [SUB_INFO], TOKEN2

        subscriptions, next_page_token = client.list_subscriptions(
            SIZE, TOKEN1)

        self.assertEqual(len(subscriptions), 1)
        self.assertIsInstance(subscriptions[0], Subscription)
        self.assertEqual(subscriptions[0].name, self.SUB_NAME)
        self.assertEqual(subscriptions[0].topic.name, self.TOPIC_NAME)
        self.assertEqual(subscriptions[0].ack_deadline, ACK_DEADLINE)
        self.assertEqual(subscriptions[0].push_endpoint, PUSH_ENDPOINT)
        self.assertEqual(next_page_token, TOKEN2)

        self.assertEqual(api._listed_subscriptions,
                         (self.PROJECT, SIZE, TOKEN1))

    def test_list_subscriptions_w_missing_key(self):
        PROJECT = 'PROJECT'
        creds = _Credentials()

        client = self._makeOne(project=PROJECT, credentials=creds)
        client.connection = object()
        api = client._subscriber_api = _FauxSubscriberAPI()
        api._list_subscriptions_response = (), None

        subscriptions, next_page_token = client.list_subscriptions()

        self.assertEqual(len(subscriptions), 0)
        self.assertIsNone(next_page_token)

        self.assertEqual(api._listed_subscriptions,
                         (self.PROJECT, None, None))

    def test_topic(self):
        PROJECT = 'PROJECT'
        TOPIC_NAME = 'TOPIC_NAME'
        creds = _Credentials()

        client_obj = self._makeOne(project=PROJECT, credentials=creds)
        new_topic = client_obj.topic(TOPIC_NAME)
        self.assertEqual(new_topic.name, TOPIC_NAME)
        self.assertIs(new_topic._client, client_obj)
        self.assertEqual(new_topic.project, PROJECT)
        self.assertEqual(new_topic.full_name,
                         'projects/%s/topics/%s' % (PROJECT, TOPIC_NAME))
        self.assertFalse(new_topic.timestamp_messages)


class _Credentials(object):

    _scopes = None

    @staticmethod
    def create_scoped_required():
        return True

    def create_scoped(self, scope):
        self._scopes = scope
        return self


class _Iterator(object):

    def __init__(self, items, token):
        self._items = items or ()
        self.next_page_token = token

    def __iter__(self):
        return iter(self._items)


class _FauxPublisherAPI(object):

    def __init__(self, items=None, token=None):
        self._items = items
        self._token = token

    def list_topics(self, project, page_size, page_token):
        self._listed_topics = (project, page_size, page_token)
        return _Iterator(self._items, self._token)


class _FauxSubscriberAPI(object):

    def list_subscriptions(self, project, page_size, page_token):
        self._listed_subscriptions = (project, page_size, page_token)
        return self._list_subscriptions_response