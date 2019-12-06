import json
import unittest
import base64

import falcon
from falcon import testing

from falcon_heavy.http.testing import encode_urlencoded_form

from tests.falcon.petstore.server import app


class PetstoreTest(testing.TestCase):

    def setUp(self):
        super(PetstoreTest, self).setUp()
        self.app = app

    def test_petstore(self):
        resp = self.simulate_get('/pets', params={'tags': ['ff', 'dd', 34, 'ff']})
        self.assertEqual(resp.status, falcon.HTTP_200)

        body = {}
        headers = {"Content-Type": falcon.MEDIA_JSON}
        resp = self.simulate_post('/pets', body=json.dumps(body), headers=headers)
        self.assertEqual(resp.status, falcon.HTTP_400)

        body = {
            'name': 'Max'
        }
        headers = {"Content-Type": falcon.MEDIA_JSON}
        resp = self.simulate_post('/pets', body=json.dumps(body), headers=headers)
        self.assertEqual(resp.status, falcon.HTTP_200)
        self.assertEqual(resp.json['name'], 'Max')

        resp = self.simulate_get('/pets')
        self.assertEqual(resp.status, falcon.HTTP_200)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['name'], 'Max')

        resp = self.simulate_get('/pets/1')
        self.assertEqual(resp.status, falcon.HTTP_200)
        self.assertEqual(resp.json['name'], 'Max')

        resp = self.simulate_delete('/pets/1')
        self.assertEqual(resp.status, falcon.HTTP_204)

        resp = self.simulate_get('/pets')
        self.assertEqual(resp.status, falcon.HTTP_200)
        self.assertEqual(len(resp.json), 0)

        resp = self.simulate_delete('/pets/1')
        self.assertEqual(resp.status, falcon.HTTP_500)
        self.assertEqual(resp.json['code'], 314)

    def test_www_form_urlencoded(self):
        body, headers = encode_urlencoded_form({'id': '45', 'file_name': 'adobe_русский.pdf 45'})
        resp = self.simulate_post('/test-urlencoded', body=body, headers=headers)
        self.assertEqual(resp.status, falcon.HTTP_200)
        self.assertEqual([45, u'adobe_русский.pdf 45'], resp.json)

    def test_styles(self):
        resp = self.simulate_get('/test-styles-array', query_string='x=1,2,3')
        self.assertEqual(resp.json, [1, 2, 3])

        resp = self.simulate_get('/test-styles-object', query_string='x=role,admin,firstName,Alex')
        self.assertEqual(resp.json, {'role': 'admin', 'firstName': 'Alex'})

    def test_base64(self):
        body = {
            'id': 1,
            'file_name': 'base64 encoded',
            'file': base64.b64encode(b'Hello World').decode('ascii')
        }
        headers = {"Content-Type": falcon.MEDIA_JSON}
        resp = self.simulate_post('/test-base64?a=1&a=2', body=json.dumps(body), headers=headers)
        self.assertEqual(resp.status, falcon.HTTP_200)
        self.assertEqual(resp.json['input_decoded_file'], 'Hello World')
        self.assertEqual(base64.b64decode(resp.json['file']).decode('utf-8'), 'Hello human')


if __name__ == '__main__':
    unittest.main()
