import os

from falcon_heavy.contrib.operations import OpenAPIOperations
from falcon_heavy.contrib.parsers import MultiPartParser, JSONParser, FormParser
from falcon_heavy.contrib.renderers import JSONRenderer, TextRenderer
from falcon_heavy.contrib.falcon.testing import FalconDummyOpenAPIDecorator

operations = OpenAPIOperations.from_file(
    os.path.join(os.path.dirname(__file__), 'schema/petstore.yaml'))
openapi = FalconDummyOpenAPIDecorator(
    operations, parsers=(MultiPartParser(), FormParser(), JSONParser()), renderers=(JSONRenderer(), TextRenderer()))
