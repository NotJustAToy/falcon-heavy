from falcon_heavy.contrib.responses import OpenAPIJSONResponse, OpenAPIResponse

from tests.falcon.petstore.openapi import openapi


def sequence(start=0):
    while True:
        start += 1
        yield start


class PetStore:

    def __init__(self):
        self._data = []
        self._index = {}
        self._sequence = sequence()

    def new_pet(self, name):
        pet = {
            'id': next(self._sequence),
            'name': name,
        }
        self._data.append(pet)
        self._index[pet['id']] = pet
        return pet

    def get_pet(self, pet_id):
        return self._index[pet_id]

    def delete_pet(self, pet_id):
        self._data.remove(self._index[pet_id])
        del self._index[pet_id]

    def __iter__(self):
        return iter(self._data)


def pet(id_, name, tag=None):
    result = {
        'id': id_,
        'name': name
    }
    if tag is not None:
        result['tag'] = tag
    return result


store = PetStore()


class Pets:

    @openapi
    def on_get(self, request):
        return OpenAPIJSONResponse([pet for pet in store])

    @openapi
    def on_post(self, request):
        return OpenAPIJSONResponse(store.new_pet(request.content['name']))


class Pet:

    @openapi
    def on_get(self, request):
        return OpenAPIJSONResponse(store.get_pet(request.path_params['id']))

    @openapi
    def on_delete(self, request):
        try:
            store.delete_pet(request.path_params['id'])
        except KeyError:
            return OpenAPIJSONResponse({
                'code': 314,
                'message': "Pet already deleted"
            }, status_code=500)

        return OpenAPIResponse(status_code=204)


class TestMultipart:

    @openapi
    def on_post(self, request):
        return OpenAPIResponse(request.content['photo'].filename)


class TestUrlencoded:

    @openapi
    def on_post(self, request):
        return OpenAPIJSONResponse([request.content['id'], request.content['file_name']])


class TestStyles:

    @openapi
    def on_get(self, request):
        from collections import Mapping  # noqa
        x = request.query_params['x']
        return OpenAPIJSONResponse(dict(x) if isinstance(x, Mapping) else x)


class TestBase64:

    @openapi
    def on_post(self, request):
        return OpenAPIJSONResponse({
            'file': 'Hello human',
            'input_decoded_file': request.content['file'].read().decode('utf-8')
        }, headers={
            'X-Rate-Limit-Limit': 10,
            'X-Rate-Limit-Remaining': 10,
            'X-Rate-Limit-Reset': 10
        })
