import unittest
import datetime
from contextlib import contextmanager

import rfc3339

from falcon_heavy.core.context import (
    make_specification_conversion_context,
    make_request_conversion_context
)
from falcon_heavy.core.openapi import (
    SchemaObjectType,
    ComponentsObjectType
)
from falcon_heavy.core.factories import TypeFactory
from falcon_heavy.core.types import Error, SchemaError, Path


class FactoriesTest(unittest.TestCase):

    @staticmethod
    def _load(object_type, specification):
        return object_type().convert(
            specification,
            Path(''),
            **make_specification_conversion_context(
                '', specification)
        )

    @staticmethod
    def _generate_type(spec):
        return TypeFactory().generate(spec)

    @staticmethod
    def _convert(type_, payload, strict=True):
        return type_.convert(
            payload,
            Path(''),
            strict=strict,
            **make_request_conversion_context()
        )

    @contextmanager
    def assertSchemaErrorRaises(self, expected_errors=None):
        with self.assertRaises(SchemaError) as ctx:
            yield

        if expected_errors is not None:
            self.assertEqual(len(expected_errors), len(ctx.exception.errors))

            for path, message in expected_errors.items():
                self.assertTrue(
                    Error(Path(path), message) in ctx.exception.errors,
                    msg="An error at %s with message \"%s\" was expected, but these errors were received:\n%s" % (
                        path, message, ctx.exception.errors)
                )

    def test_generate_one_of(self):
        spec = {
            'x-schemas': {
                'Cat': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'name': {
                            'type': 'string'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'nickname': {
                            'type': 'string'
                        }
                    }
                }
            },
            'type': 'object',
            'properties': {
                'pet': {
                    'oneOf': [
                        {
                            '$ref': '#/x-schemas/Cat'
                        },
                        {
                            '$ref': '#/x-schemas/Dog'
                        }
                    ]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        cat_payload = {
            'pet': {
                'name': 'Misty'
            }
        }

        cat = self._convert(type_, cat_payload)
        self.assertEqual(cat['pet']['name'], 'Misty')

        dog_payload = {
            'pet': {
                'nickname': 'Max'
            }
        }

        dog = self._convert(type_, dog_payload)
        self.assertEqual(dog['pet']['nickname'], 'Max')

    def test_generate_oneof_with_implicit_discriminator(self):
        spec = {
            'schemas': {
                'Cat': {
                    'type': 'object',
                    'required': [
                        'pet_type'
                    ],
                    'properties': {
                        'pet_type': {
                            'type': 'string'
                        },
                        'name': {
                            'type': 'string'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'additionalProperties': False,
                    'required': [
                        'pet_type'
                    ],
                    'properties': {
                        'pet_type': {
                            'type': 'string'
                        },
                        'nickname': {
                            'type': 'string'
                        }
                    }
                },
                'Pet': {
                    'type': 'object',
                    'properties': {
                        'pet': {
                            'oneOf': [
                                {
                                    '$ref': '#/schemas/Cat'
                                },
                                {
                                    '$ref': '#/schemas/Dog'
                                }
                            ],
                            'discriminator': {
                                'propertyName': 'pet_type'
                            }
                        }
                    }
                }
            }
        }

        spec = self._load(ComponentsObjectType, spec)
        type_ = self._generate_type(spec['schemas']['Pet'])

        cat_payload = {
            'pet': {
                'pet_type': 'Cat',
                'name': 'Misty'
            }
        }

        cat = self._convert(type_, cat_payload)
        self.assertEqual(cat['pet']['name'], 'Misty')
        self.assertEqual(cat['pet']['pet_type'], 'Cat')

        ambiguous_cat_payload = {
            'pet': {
                'pet_type': '',
                'name': 'Misty'
            }
        }

        with self.assertSchemaErrorRaises({
            '#/pet': "The discriminator value must be equal to one of the following values: 'Cat', 'Dog'"
        }):
            self._convert(type_, ambiguous_cat_payload)

        dog_with_cat_properties = {
            'pet': {
                'pet_type': 'Dog',
                'name': 'Misty'
            }
        }

        with self.assertSchemaErrorRaises({
            '#/pet': "When `additionalProperties` is False, no unspecified properties are allowed. "
                     "The following unspecified properties were found: 'name'"
        }):
            self._convert(type_, dog_with_cat_properties)

    def test_generate_one_of_with_semi_explicit_discriminator(self):
        spec = {
            'schemas': {
                'Cat': {
                    'type': 'object',
                    'additionalProperties': False,
                    'required': [
                        'pet_type'
                    ],
                    'properties': {
                        'pet_type': {
                            'type': 'string'
                        },
                        'name': {
                            'type': 'string'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'additionalProperties': False,
                    'required': [
                        'pet_type'
                    ],
                    'properties': {
                        'pet_type': {
                            'type': 'string'
                        },
                        'nickname': {
                            'type': 'string'
                        }
                    }
                },
                'Pet': {
                    'type': 'object',
                    'properties': {
                        'pet': {
                            'oneOf': [
                                {
                                    '$ref': '#/schemas/Cat'
                                },
                                {
                                    '$ref': '#/schemas/Dog'
                                }
                            ],
                            'discriminator': {
                                'propertyName': 'pet_type',
                                'mapping': {
                                    '1': '#/schemas/Cat',
                                }
                            }
                        }
                    }
                }
            }
        }

        spec = self._load(ComponentsObjectType, spec)
        type_ = self._generate_type(spec['schemas']['Pet'])

        cat_payload = {
            'pet': {
                'pet_type': '1',
                'name': 'Misty'
            }
        }

        cat = self._convert(type_, cat_payload)
        self.assertEqual(cat['pet']['name'], 'Misty')

        dog_payload = {
            'pet': {
                'pet_type': 'Dog',
                'nickname': 'Max'
            }
        }

        dog = self._convert(type_, dog_payload)
        self.assertEqual(dog['pet']['nickname'], 'Max')

        unknown_payload = {
            'pet': {
                'pet_type': '2',
                'nickname': 'Max'
            }
        }

        with self.assertSchemaErrorRaises({
            '#/pet': "The discriminator value must be equal to one of the following values: '1', 'Cat', 'Dog'"
        }):
            self._convert(type_, unknown_payload)

    def test_generate_discriminator_with_inline_schemas(self):
        # Discriminator with inline schemas
        spec = {
            'x-schemas': {
                'Cat': {
                    'type': 'object',
                    'additionalProperties': False,
                    'required': [
                        'pet_type'
                    ],
                    'properties': {
                        'pet_type': {
                            'type': 'string'
                        },
                        'name': {
                            'type': 'string'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'additionalProperties': False,
                    'required': [
                        'pet_type'
                    ],
                    'properties': {
                        'pet_type': {
                            'type': 'string'
                        },
                        'nickname': {
                            'type': 'string'
                        }
                    }
                }
            },
            'type': 'object',
            'properties': {
                'pet': {
                    'oneOf': [
                        {
                            '$ref': '#/x-schemas/Cat'
                        },
                        {
                            '$ref': '#/x-schemas/Dog'
                        },
                        {
                            'type': 'object',
                            'additionalProperties': False,
                            'required': [
                                'pet_type'
                            ],
                            'properties': {
                                'pet_type': {
                                    'type': 'string'
                                },
                                'last_name': {
                                    'type': 'string'
                                }
                            }
                        }
                    ],
                    'discriminator': {
                        'propertyName': 'pet_type'
                    }
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        inline_payload = {
            'pet': {
                'pet_type': 2,
                'last_name': 'Misty'
            }
        }

        with self.assertSchemaErrorRaises({
            '#/pet': "The discriminator value must be equal to one of the following values: 'Cat', 'Dog'"
        }):
            self._convert(type_, inline_payload)

    def test_generate_anyOf(self):
        spec = {
            'x-schemas': {
                'Cat': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'name': {
                            'type': 'string'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'nickname': {
                            'type': 'string'
                        }
                    }
                }
            },
            'type': 'object',
            'properties': {
                'pet': {
                    'anyOf': [
                        {
                            '$ref': '#/x-schemas/Cat'
                        },
                        {
                            '$ref': '#/x-schemas/Dog'
                        }
                    ]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        cat_payload = {
            'pet': {
                'name': 'Misty'
            }
        }

        cat = self._convert(type_, cat_payload)
        self.assertEqual(cat['pet']['name'], 'Misty')

        dog_payload = {
            'pet': {
                'nickname': 'Max'
            }
        }

        dog = self._convert(type_, dog_payload)
        self.assertEqual(dog['pet']['nickname'], 'Max')

        not_any_payload = {
            'pet': {
                'weight': '10kg'
            }
        }

        with self.assertSchemaErrorRaises({
            '#/pet': "Does not match any schemas from `anyOf`",
            '#/pet/0': "When `additionalProperties` is False, no unspecified properties are allowed. "
                       "The following unspecified properties were found: 'weight'",
            '#/pet/1': "When `additionalProperties` is False, no unspecified properties are allowed. "
                       "The following unspecified properties were found: 'weight'"
        }):
            self._convert(type_, not_any_payload)

        spec = {
            'x-schemas': {
                'Cat': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'properties': {
                        'nickname': {
                            'type': 'string'
                        }
                    }
                }
            },
            'type': 'object',
            'properties': {
                'pet': {
                    'anyOf': [
                        {
                            '$ref': '#/x-schemas/Cat'
                        },
                        {
                            '$ref': '#/x-schemas/Dog'
                        }
                    ]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        cat_dog_payload = {
            'pet': {
                'name': 'Misty',
                'nickname': 'Max'
            }
        }

        cat_dog = self._convert(type_, cat_dog_payload)
        self.assertEqual(cat_dog['pet']['name'], 'Misty')
        self.assertEqual(cat_dog['pet']['nickname'], 'Max')

    def test_generate_allOf(self):
        spec = {
            'x-schemas': {
                'Cat': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string'
                        },
                        's': {
                            'type': 'integer'
                        }
                    }
                },
                'Dog': {
                    'type': 'object',
                    'properties': {
                        'nickname': {
                            'type': 'string'
                        }
                    }
                }
            },
            'type': 'object',
            'properties': {
                'pet': {
                    'allOf': [
                        {
                            '$ref': '#/x-schemas/Cat'
                        },
                        {
                            '$ref': '#/x-schemas/Dog'
                        }
                    ]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        cat_dog_payload = {
            'pet': {
                'name': 'Misty',
                'nickname': 'Max',
                's': '45'
            }
        }

        cat_dog = self._convert(type_, cat_dog_payload, strict=False)
        self.assertEqual(cat_dog['pet']['name'], 'Misty')
        self.assertEqual(cat_dog['pet']['nickname'], 'Max')
        self.assertTrue(isinstance(cat_dog['pet']['s'], int))

    def test_generate_recursive_property(self):
        spec = {
            'properties': {
                'payload': {},
                'nested_nodes': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/'
                    }
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'adsad': 'sdsd',
            'payload': {
                'ddd': 34
            },
            'nested_nodes': [
                {
                    'payload': {},
                    'nested_nodes': [
                        {
                            'payload': {
                                'fdf': 54
                            }
                        }
                    ]
                },
                {
                    'payload': {
                        'ff': 'dd'
                    }
                }
            ]
        }

        root = self._convert(type_, payload)
        self.assertEqual(root['adsad'], 'sdsd')

    def test_defaults(self):
        spec = {
            'properties': {
                'with_default': {
                    'type': 'integer',
                    'default': 5
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {}

        obj = self._convert(type_, payload)
        self.assertEqual(obj['with_default'], 5)

        spec = {
            'properties': {
                'with_default': {
                    'type': 'string',
                    'pattern': r'^\+?\d{7,20}$',
                    'default': 'sdfdf'
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {}

        with self.assertSchemaErrorRaises({
            '#/with_default': "Does not match the pattern"
        }):
            self._convert(type_, payload)

    def test_enum_primitive(self):
        spec = {
            'properties': {
                'type_': {
                    'type': 'integer',
                    'enum': [5, 'ret', '56']
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': 5
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_'], 5)

        payload = {
            'type_': 45
        }

        with self.assertSchemaErrorRaises({
            '#/type_': "Must be equal to one of the following values: '56', 'ret', 5"
        }):
            self._convert(type_, payload)

        spec = {
            'properties': {
                'type_': {
                    'type': 'string',
                    'enum': ['5', 'ret', '56']
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': '5'
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_'], '5')

        spec = {
            'properties': {
                'type_': {
                    'type': 'boolean',
                    'enum': [True]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': True
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_'], True)

    def test_enum_list(self):
        spec = {
            'properties': {
                'type_': {
                    'type': 'array',
                    'items': {
                        'type': 'integer'
                    },
                    'enum': [[3], [1, 4]]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': [3]
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_'], [3])

        payload = {
            'type_': [1, 4]
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_'], [1, 4])

        payload = {
            'type_': [1, 45]
        }

        with self.assertSchemaErrorRaises({
            '#/type_': "Must be equal to one of the following values: [1, 4], [3]"
        }):
            self._convert(type_, payload)

    def test_enum_object(self):
        spec = {
            'properties': {
                'type_': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'type': {
                            'type': 'integer',
                            'nullable': True
                        }
                    },
                    'enum': [{'type': 0}, {'type': None}]
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': {
                'type': 0
            }
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_']['type'], 0)

        payload = {
            'type_': {
                'type': None
            }
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_']['type'], None)

        payload = {
            'type_': {
                'type': 1
            }
        }

        with self.assertSchemaErrorRaises({
            '#/type_': "Must be equal to one of the following values: {'type': 0}, {'type': None}"
        }):
            self._convert(type_, payload)

    def test_required(self):
        spec = {
            'required': ['type_'],
            'properties': {
                'type_': {
                    'type': 'object',
                    'required': ['subprop'],
                    'properties': {
                        'subprop': {
                            'type': 'integer'
                        }
                    }
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': {
                'subprop': 314
            }
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_']['subprop'], 314)

        payload = {
        }

        with self.assertSchemaErrorRaises({
            '#': "The following required properties are missed: 'type_'"
        }):
            self._convert(type_, payload)

        payload = {
            'type_': {}
        }

        with self.assertSchemaErrorRaises({
            '#/type_': "The following required properties are missed: 'subprop'"
        }):
            self._convert(type_, payload)

    def test_nullable(self):
        spec = {
            'properties': {
                'type_': {
                    'type': 'integer',
                    'nullable': True
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': None
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['type_'], None)

        spec = {
            'properties': {
                'type_': {
                    'type': 'integer',
                    'nullable': False
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'type_': None
        }

        with self.assertSchemaErrorRaises({
            '#/type_': "Null values not allowed"
        }):
            self._convert(type_, payload)

    def test_strict(self):
        spec = {
            'allOf': [
                {'type': 'integer'},
                {'type': 'string'}
            ]
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = 5

        with self.assertSchemaErrorRaises({
            '#': "Does not match all schemas from `allOf`. Invalid schema indexes: 1",
            '#/1': "Must be a string"
        }):
            self._convert(type_, payload)

        payload = 5

        obj = self._convert(type_, payload, strict=False)
        self.assertEqual(obj, '5')

    def test_date(self):
        today = datetime.datetime.now().date()

        spec = {
            'properties': {
                'date': {
                    'type': 'string',
                    'format': 'date',
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'date': today.isoformat()
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['date'], today)

    def test_datetime(self):
        now = datetime.datetime.now().replace(microsecond=0)

        spec = {
            'properties': {
                'datetime': {
                    'type': 'string',
                    'format': 'date-time',
                }
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'datetime': rfc3339.rfc3339(now)
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['datetime'], now)

    def test_min_max_properties(self):
        spec = {
            'additionalProperties': True,
            'minProperties': 2,
            'maxProperties': 4,
            'properties': {
                'prop1': {'type': 'string'}
            }
        }

        spec = self._load(SchemaObjectType, spec)
        type_ = self._generate_type(spec)

        payload = {
            'prop1': 'abracadabra',
            'prop2': 2
        }

        obj = self._convert(type_, payload)
        self.assertEqual(obj['prop1'], 'abracadabra')
        self.assertEqual(obj['prop2'], 2)

        payload = {
            'prop1': 'abracadabra'
        }

        with self.assertSchemaErrorRaises({
            '#': "Object must have at least 2 properties. It had only 1 properties"
        }):
            self._convert(type_, payload)

        payload = {
            'prop1': 'abracadabra',
            'prop2': 2,
            'prop3': 3,
            'prop4': 4,
            'prop5': 5
        }

        with self.assertSchemaErrorRaises({
            '#': "Object must have no more than 4 properties. It had 5 properties"
        }):
            self._convert(type_, payload)

    def test_polymorphic(self):
        spec = {
            "schemas": {
                "Pet": {
                    "deprecated": True,
                    "type": "object",
                    "discriminator": {
                        "propertyName": "petType"
                    },
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "petType": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "name",
                        "petType"
                    ]
                },
                "Cat": {
                    "description": (
                        "A representation of a cat. Note that `Cat` will be used as the discriminator value."),
                    "allOf": [
                        {
                            "$ref": "#/schemas/Pet"
                        },
                        {
                            "type": "object",
                            "properties": {
                                "huntingSkill": {
                                    "type": "string",
                                    "description": "The measured skill for hunting",
                                    "default": "lazy",
                                    "enum": [
                                        "clueless",
                                        "lazy",
                                        "adventurous",
                                        "aggressive"
                                    ]
                                }
                            },
                            "required": [
                                "huntingSkill"
                            ]
                        }
                    ]
                },
                "Dog": {
                    "description": (
                        "A representation of a dog. Note that `Dog` will be used as the discriminator value."),
                    "allOf": [
                        {
                            "$ref": "#/schemas/Pet"
                        },
                        {
                            "type": "object",
                            "properties": {
                                "packSize": {
                                    "type": "integer",
                                    "format": "int32",
                                    "description": "the size of the pack the dog is from",
                                    "default": 0,
                                    "minimum": 0
                                }
                            },
                            "required": [
                                "packSize"
                            ]
                        },
                    ]
                }
            }
        }

        spec = self._load(ComponentsObjectType, spec)
        type_ = self._generate_type(spec['schemas']['Pet'])

        payload = {
            "petType": "Cat",
            "name": "Misty",
            "huntingSkill": "adventurous",
            "age": 3
        }

        cat = self._convert(type_, payload)
        self.assertEqual(cat['age'], 3)
        self.assertEqual(cat['name'], "Misty")
        self.assertEqual(cat['huntingSkill'], "adventurous")

        payload = {
            "petType": "Dog",
            "name": "Max",
            "packSize": 314,
            "age": 2
        }

        dog = self._convert(type_, payload)
        self.assertEqual(dog['age'], 2)
        self.assertEqual(dog['name'], "Max")
        self.assertEqual(dog['packSize'], 314)

        payload = {
            "age": 3
        }

        with self.assertSchemaErrorRaises({
            '#': "A property with name 'petType' must be present"
        }):
            self._convert(type_, payload)

        payload = {
            "petType": "Cat",
            "name": "Misty"
        }

        with self.assertSchemaErrorRaises({
            '#': "Does not match all schemas from `allOf`. Invalid schema indexes: 1",
            '#/1': "The following required properties are missed: 'huntingSkill'"
        }):
            self._convert(type_, payload)


if __name__ == '__main__':
    unittest.main()
