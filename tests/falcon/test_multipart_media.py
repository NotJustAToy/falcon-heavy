import os
import io
import json
import unittest

import falcon

from falcon_heavy.contrib.operations import OpenAPIOperations
from falcon_heavy.contrib.parsers import MultiPartParser
from falcon_heavy.contrib.renderers import TextRenderer, JSONRenderer
from falcon_heavy.contrib.falcon.testing import create_client, make_resource_class, FalconDummyOpenAPIDecorator

from falcon_heavy.http.testing import encode_multipart
from falcon_heavy.http.datastructures import FormStorage, FileStorage


class MultipartTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        operations = OpenAPIOperations.from_file(
            os.path.join(os.path.dirname(__file__), 'petstore/schema/petstore.yaml'))
        resource_class = make_resource_class(FalconDummyOpenAPIDecorator(
            operations, parsers=(MultiPartParser(),), renderers=(TextRenderer(), JSONRenderer())))
        cls.client = create_client('/test-multipart', resource_class())

    def test_multipart(self):
        body, headers = encode_multipart((
            ('id', FormStorage('1')),
            ('meta', FormStorage(json.dumps({'name': 'Max'}), content_type='application/json')),
            ('artist', FormStorage(json.dumps({'name': 'Jared Leto'}), content_type='application/json')),
            ('artist', FormStorage(json.dumps({'name': 'Jared Leto'}), content_type='application/json')),
            ('photo', FileStorage(
                stream=io.StringIO(r'photo\t\n\dummy\r\n'),
                filename='cam.jpg',
                content_type='image/png',
                headers={'X-Rate-Limit-Limit': '1'}
            ))
        ))

        resp = self.client.simulate_post('/test-multipart', body=body, headers=headers)
        self.assertEqual(falcon.HTTP_200, resp.status)
        self.assertEqual(1, self.client.resource.captured_request.content['id'].content)
        self.assertEqual(2, len(self.client.resource.captured_request.content['artist']))
        self.assertEqual(u'cam.jpg', self.client.resource.captured_request.content['photo'].storage.filename)
        self.assertEqual(1, self.client.resource.captured_request.content['photo'].custom_headers['x-rate-limit-limit'])

        data, headers = encode_multipart(())

        resp = self.client.simulate_post('/test-multipart', body=data, headers=headers)
        self.assertEqual(resp.status, falcon.HTTP_400)


if __name__ == '__main__':
    unittest.main()
