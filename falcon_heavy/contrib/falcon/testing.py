# Copyright 2019 Not Just A Toy Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from falcon import API, testing

from falcon_heavy.contrib.responses import OpenAPIResponse

from .decorators import FalconAbstractOpenAPIDecorator

__all__ = (
    'FalconDummyOpenAPIDecorator',
    'make_resource_class',
    'create_client',
)


class FalconDummyOpenAPIDecorator(FalconAbstractOpenAPIDecorator):

    def _handle_not_found(self, request, instance, exception):
        return OpenAPIResponse(status_code=404)

    def _handle_invalid_request(self, request, operation, instance, exception):
        print(exception)
        return OpenAPIResponse(status_code=400)

    def _handle_invalid_response(self, response, operation, instance, exception):
        print(exception)

    def _handle_authorization_failed(self, request, operation, instance, reasons):
        return OpenAPIResponse(status_code=401)


def make_resource_class(decorator):
    class Resource:

        def __init__(self):
            self.captured_request = None

        @decorator
        def on_get(self, request):
            self.captured_request = request

        @decorator
        def on_post(self, request):
            self.captured_request = request

    return Resource


def create_client(uri_template, resource, handlers=None):
    app = API()
    app.add_route(uri_template, resource)

    if handlers:
        app.req_options.media_handlers.update(handlers)

    client = testing.TestClient(app)
    client.resource = resource

    return client
