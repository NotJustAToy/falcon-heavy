import warnings
import unittest

from falcon_heavy.core.types import path, exceptions
from falcon_heavy.core.context import make_specification_conversion_context
from falcon_heavy.core.openapi import (
    InfoObjectType,
    ContactObjectType,
    LicenseObjectType,
    ServerObjectType,
    ComponentsObjectType,
    PathItemObjectType,
    OperationObjectType,
    ExternalDocumentationObjectType,
    HeaderParameterObjectType,
    PathParameterObjectType,
    QueryParameterObjectType,
    RequestBodyObjectType,
    MediaTypeObjectType,
    ResponsesObjectType,
    ResponseObjectType,
    TagObjectType,
    SchemaObjectType
)


class SchemaTest(unittest.TestCase):

    def _valid(self, object_type, payload):
        try:
            return object_type().convert(
                payload,
                path.Path('#'),
                **make_specification_conversion_context('#', payload)
            )
        except exceptions.SchemaError as e:
            self.fail(e)

    def _invalid(self, object_type, payload, expected_errors=None):
        try:
            object_type().convert(
                payload,
                path.Path('#'),
                **make_specification_conversion_context('#', payload)
            )
        except exceptions.SchemaError as e:
            if expected_errors is not None:
                actual_errors = [(error.path, error.message) for error in e.errors]
                self.assertEqual(sorted(expected_errors), sorted(actual_errors))
        else:
            self.fail()

    def test_valid_info(self):
        self._valid(InfoObjectType, {
            "title": "Sample Pet Store App",
            "description": "This is a sample server for a pet store.",
            "termsOfService": "http://example.com/terms/",
            "contact": {
                "name": "API Support",
                "url": "http://www.example.com/support",
                "email": "support@example.com"
            },
            "license": {
                "name": "Apache 2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
            },
            "version": "1.0.1"
        })

    def test_valid_contact(self):
        self._valid(ContactObjectType, {
            "name": "API Support",
            "url": "http://www.example.com/support",
            "email": "support@example.com"
        })

    def test_valid_license(self):
        self._valid(LicenseObjectType, {
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
        })

    def test_valid_server(self):
        self._valid(ServerObjectType, {
            "url": "https://{username}.gigantic-server.com:{port}/{basePath}",
            "description": "The production API server",
            "variables": {
                "username": {
                    "default": "demo",
                    "description": ("this value is assigned by the service provider, "
                                    "in this example `gigantic-server.com`")
                },
                "port": {
                    "enum": [
                        "8443",
                        "443"
                    ],
                    "default": "8443"
                },
                "basePath": {
                    "default": "v2"
                }
            }
        })

    def test_valid_components(self):
        self._valid(ComponentsObjectType, {
            "schemas": {
                "GeneralError": {
                    "type": "string"
                },
                "Category": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int64"
                        },
                        "name": {
                            "type": "string"
                        }
                    }
                },
                "Tag": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int64"
                        },
                        "name": {
                            "type": "string"
                        }
                    }
                }
            },
            "parameters": {
                "skipParam": {
                    "name": "skip",
                    "in": "query",
                    "description": "number of items to skip",
                    "required": True,
                    "schema": {
                        "type": "integer",
                        "format": "int32"
                    }
                },
                "limitParam": {
                    "name": "limit",
                    "in": "query",
                    "description": "max records to return",
                    "required": True,
                    "schema": {
                        "type": "integer",
                        "format": "int32"
                    }
                }
            },
            "responses": {
                "NotFound": {
                    "description": "Entity not found."
                },
                "IllegalInput": {
                    "description": "Illegal input for operation."
                },
                "GeneralError": {
                    "description": "General Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/schemas/GeneralError"
                            }
                        }
                    }
                }
            },
            "securitySchemes": {
                "api_key": {
                    "type": "apiKey",
                    "name": "api_key",
                    "in": "header"
                },
                "petstore_auth": {
                    "type": "oauth2",
                    "flows": {
                        "implicit": {
                            "authorizationUrl": "http://example.org/api/oauth/dialog",
                            "scopes": {
                                "write:pets": "modify pets in your account",
                                "read:pets": "read your pets"
                            },
                            "tokenUrl": "https://"
                        }
                    }
                }
            }
        })

    def test_invalid_component_names(self):
        self._invalid(
            ComponentsObjectType,
            {
                "schemas": {
                    "%Error": {
                        "type": "string"
                    }
                }
            },
            expected_errors=[
                ("#/schemas", "The following component names are invalid: '%Error'")
            ]
        )

    def test_valid_path_item(self):
        self._valid(PathItemObjectType, {
            "x-schemas": {
                "Pet": {
                    "type": "string"
                }
            },
            "x-resource": "controllers.Pets",
            "get": {
                "description": "Returns all pets from the system that the user has access to",
                "responses": {
                    "200": {
                        "description": "A list of pets.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/x-schemas/Pet"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        })

    def test_deprecated_operation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self._valid(OperationObjectType, {
                "responses": {
                    "200": {
                        "description": "Successful"
                    }
                },
                "deprecated": True,
            })
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertTrue("deprecated" in str(w[-1].message))

    def test_valid_operation(self):
        self._valid(OperationObjectType, {
            "tags": [
                "pet"
            ],
            "summary": "Updates a pet in the store with form data",
            "operationId": "updatePetWithForm",
            "parameters": [
                {
                    "name": "petId",
                    "in": "path",
                    "description": "ID of pet that needs to be updated",
                    "required": True,
                    "schema": {
                        "type": "string"
                    }
                }
            ],
            "requestBody": {
                "content": {
                    "application/x-www-form-urlencoded": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "description": "Updated name of the pet",
                                    "type": "string"
                                },
                                "status": {
                                    "description": "Updated status of the pet",
                                    "type": "string"
                                }
                            },
                            "required": [
                                "status"
                            ]
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Pet updated.",
                    "content": {
                        "application/json": {},
                        "application/xml": {}
                    }
                },
                "405": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {},
                        "application/xml": {}
                    }
                }
            },
            "security": [
                {
                    "petstore_auth": [
                        "write:pets",
                        "read:pets"
                    ]
                }
            ]
        })

    def test_valid_external_documentation(self):
        self._valid(ExternalDocumentationObjectType, {
            "description": "Find more info here",
            "url": "https://example.com"
        })

    def test_deprecated_parameter(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self._valid(HeaderParameterObjectType, {
                "name": "token",
                "in": "header",
                "deprecated": True,
            })
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertTrue("deprecated" in str(w[-1].message))

    def test_valid_header_parameter(self):
        self._valid(HeaderParameterObjectType, {
            "name": "token",
            "in": "header",
            "deprecated": True,
            "description": "token to be passed as a header",
            "required": True,
            "schema": {
                "type": "array",
                "items": {
                    "type": "integer",
                    "format": "int64"
                }
            },
            "style": "simple",
            "x-property": "property"
        })

    def test_valid_path_parameter(self):
        self._valid(PathParameterObjectType, {
            "name": "username",
            "in": "path",
            "description": "username to fetch",
            "required": True,
            "schema": {
                "type": "string"
            }
        })

    def test_valid_query_parameter(self):
        self._valid(QueryParameterObjectType, {
            "name": "id",
            "in": "query",
            "description": "ID of the object to fetch",
            "required": False,
            "schema": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "style": "form",
            "explode": True
        })

    def test_valid_complex_query_parameter(self):
        self._valid(QueryParameterObjectType, {
            "in": "query",
            "name": "coordinates",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": [
                            "lat",
                            "long"
                        ],
                        "properties": {
                            "lat": {
                                "type": "number"
                            },
                            "long": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        })

    def test_valid_request_body(self):
        self._valid(RequestBodyObjectType, {
            "x-schemas": {
                "User": {
                    "type": "string"
                }
            },
            "description": "user to add to the system",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/x-schemas/User"
                    },
                    "examples": {
                        "user": {
                            "summary": "User Example",
                            "externalValue": "http://foo.bar/examples/user-example.json"
                        }
                    }
                },
                "application/xml": {
                    "schema": {
                        "$ref": "#/x-schemas/User"
                    },
                    "examples": {
                        "user": {
                            "summary": "User example in XML",
                            "externalValue": "http://foo.bar/examples/user-example.xml"
                        }
                    }
                },
                "text/plain": {
                    "examples": {
                        "user": {
                            "summary": "User example in Plain text",
                            "externalValue": "http://foo.bar/examples/user-example.txt"
                        }
                    }
                },
                "*/*": {
                    "examples": {
                        "user": {
                            "summary": "User example in other format",
                            "externalValue": "http://foo.bar/examples/user-example.whatever"
                        }
                    }
                }
            }
        })

    def test_valid_media_type(self):
        self._valid(MediaTypeObjectType, {
            "x-schemas": {
                "Pet": {
                    "type": "string"
                }
            },
            "x-examples": {
                "frog-example": {
                    "value": "example"
                }
            },
            "schema": {
                "$ref": "#/x-schemas/Pet"
            },
            "examples": {
                "cat": {
                    "summary": "An example of a cat",
                    "value": {
                        "name": "Fluffy",
                        "petType": "Cat",
                        "color": "White",
                        "gender": "male",
                        "breed": "Persian"
                    }
                },
                "dog": {
                    "summary": "An example of a dog with a cat's name",
                    "value": {
                        "name": "Puma",
                        "petType": "Dog",
                        "color": "Black",
                        "gender": "Female",
                        "breed": "Mixed"
                    },
                },
                "frog": {
                    "$ref": "#/x-examples/frog-example"
                }
            }
        })

    def test_valid_responses(self):
        self._valid(ResponsesObjectType, {
            "200": {
                "description": "Successful"
            },
            "default": {
                "description": "Something went wrong"
            }
        })

    def test_invalid_responses_with_invalid_response_code(self):
        self._invalid(
            ResponsesObjectType,
            {
                "code": {
                    "description": "Something"
                }
            },
            expected_errors=[
                ("#", "Should contains HTTP status codes or `default`."
                      " The following invalid definitions were found: 'code'")
            ]
        )

    def test_invalid_responses_without_response_codes(self):
        self._invalid(
            ResponsesObjectType,
            {
                "default": {
                    "description": "Something went wrong"
                }
            },
            expected_errors=[
                ("#", "Responses must contains at least one response code")
            ]
        )

    def test_valid_response(self):
        self._valid(ResponseObjectType, {
            "x-schemas": {
                "VeryComplexType": {
                    "type": "string"
                }
            },
            "description": "A complex object array response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {
                            "$ref": "#/x-schemas/VeryComplexType"
                        }
                    }
                }
            },
            "headers": {
                "X-Rate-Limit-Limit": {
                    "description": "The number of allowed requests in the current period",
                    "schema": {
                        "type": "integer"
                    }
                },
                "X-Rate-Limit-Remaining": {
                    "description": "The number of remaining requests in the current period",
                    "schema": {
                        "type": "integer"
                    }
                },
                "X-Rate-Limit-Reset": {
                    "description": "The number of seconds left in the current period",
                    "schema": {
                        "type": "integer"
                    }
                }
            }
        })

    def test_valid_response_with_no_return_value(self):
        self._valid(ResponseObjectType, {
            "description": "ObjectType created"
        })

    def test_valid_tag(self):
        self._valid(TagObjectType, {
            "name": "pet",
            "description": "Pets operations"
        })

    def test_deprecated_schema(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self._valid(SchemaObjectType, {
                "deprecated": True,
            })
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertTrue("deprecated" in str(w[-1].message))

    def test_valid_schema(self):
        self._valid(SchemaObjectType, {
            "x-schemas": {
                "Address": {
                    "type": "string"
                }
            },
            "type": "object",
            "required": [
                "name"
            ],
            "properties": {
                "name": {
                    "type": "string"
                },
                "address": {
                    "$ref": "#/x-schemas/Address"
                },
                "age": {
                    "type": "integer",
                    "format": "int32",
                    "minimum": 0
                }
            }
        })

    def test_valid_schema_with_additional_properties(self):
        self._valid(SchemaObjectType, {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        })

    def test_valid_schema_for_mapping(self):
        self._valid(SchemaObjectType, {
            "x-schemas": {
                "ComplexModel": {
                    "type": "string"
                }
            },
            "type": "object",
            "additionalProperties": {
                "$ref": "#/x-schemas/ComplexModel"
            }
        })

    def test_valid_schema_with_example(self):
        self._valid(SchemaObjectType, {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "format": "int64"
                },
                "name": {
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "example": {
                "name": "Puma",
                "id": 1
            }
        })

    def test_valid_schema_with_composition(self):
        self._valid(ComponentsObjectType, {
            "schemas": {
                "ErrorModel": {
                    "type": "object",
                    "required": [
                        "message",
                        "code"
                    ],
                    "properties": {
                        "message": {
                            "type": "string"
                        },
                        "code": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 600
                        }
                    }
                },
                "ExtendedErrorModel": {
                    "allOf": [
                        {
                            "$ref": "#/schemas/ErrorModel"
                        },
                        {
                            "type": "object",
                            "required": [
                                "rootCause"
                            ],
                            "properties": {
                                "rootCause": {
                                    "type": "string"
                                }
                            }
                        }
                    ]
                }
            }
        })

    def test_valid_schema_with_polymorphism_support(self):
        self._valid(ComponentsObjectType, {
            "schemas": {
                "Pet": {
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
                        },
                        "pet": {
                            "$ref": "#/schemas/Pet"
                        }
                    },
                    "required": [
                        "name",
                        "petType"
                    ]
                },
                "Cat": {
                    "description": "A representation of a cat. "
                                   "Note that `Cat` will be used as the discriminator value.",
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
                    "description": "A representation of a dog. "
                                   "Note that `Dog` will be used as the discriminator value.",
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
                        }
                    ]
                }
            }
        })

    def test_valid_schema_object_with_discriminator(self):
        self._valid(SchemaObjectType, {
            "discriminator": {
                "propertyName": "petType"
            },
            "properties": {
                "petType": {
                    "type": "string"
                }
            },
            "required": [
                "petType"
            ]
        })

    def test_valid_schema_one_of_with_duscriminator(self):
        self._valid(SchemaObjectType, {
            "discriminator": {
                "propertyName": "petType"
            },
            "oneOf": [
                {
                    "properties": {
                        "petType": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "petType"
                    ]
                }
            ]
        })

    def test_invalid_schema_invalid_type_for_minimum(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "object",
                "minimum": 314
            },
            expected_errors=[
                ("#", "`minimum` can only be used for number types")
            ]
        )

    def test_invalid_schema_invalid_type_for_maximum(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "object",
                "maximum": 314
            },
            expected_errors=[
                ("#", "`maximum` can only be used for number types")
            ]
        )

    def test_invalid_schema_maximum_must_be_greater_than_minimum(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "number",
                "minimum": 400,
                "maximum": 314
            },
            expected_errors=[
                ("#", "The value of `maximum` must be greater than or equal to the value of `minimum`")
            ]
        )

    def test_invalid_schema_invalid_type_for_multiple_of(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "string",
                "multipleOf": 10
            },
            expected_errors=[
                ("#", "`multipleOf` can only be used for number types")
            ]
        )

    def test_invalid_schema_invalid_type_for_min_length(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "minLength": 1
            },
            expected_errors=[
                ("#", "`minLength` can only be used for string types")
            ]
        )

    def test_invalid_schema_invalid_type_for_max_length(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "maxLength": 255
            },
            expected_errors=[
                ("#", "`maxLength` can only be used for string types")
            ]
        )

    def test_invalid_schema_max_length_must_be_greater_than_min_length(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "string",
                "minLength": 314,
                "maxLength": 255
            },
            expected_errors=[
                ("#", "The value of `maxLength` must be greater than or equal to the `minLength` value")
            ]
        )

    def test_invalid_schema_invalid_type_for_min_items(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "string",
                "minItems": 7
            },
            expected_errors=[
                ("#", "`minItems` can only be used for array types")
            ]
        )

    def test_invalid_schema_invalid_type_for_max_items(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "string",
                "maxItems": 256
            },
            expected_errors=[
                ("#", "`maxItems` can only be used for array types")
            ]
        )

    def test_invalid_schema_max_items_must_be_greater_than_min_items(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "array",
                "minItems": 512,
                "maxItems": 256,
                "items": {
                    "description": "Any"
                }
            },
            expected_errors=[
                ("#", "The value of `maxItems` must be greater than or equal to the value of `minItems`")
            ]
        )

    def test_invalid_schema_invalid_type_for_unique_items(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "uniqueItems": True
            },
            expected_errors=[
                ("#", "`uniqueItems` can only be used for array types")
            ]
        )

    def test_invalid_schema_items_required_for_type_array(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "array"
            },
            expected_errors=[
                ("#", "`items` must be specified for array type")
            ]
        )

    def test_invalid_schema_invalid_type_for_properties(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "properties": {}
            },
            expected_errors=[
                ("#", "`properties` can only be used for object types")
            ]
        )

    def test_invalid_schema_invalid_type_for_additional_properties(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "additionalProperties": {}
            },
            expected_errors=[
                ("#", "`additionalProperties` can only be used for object types")
            ]
        )

    def test_invalid_schema_invalid_type_for_required(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "required": ["id"]
            },
            expected_errors=[
                ("#", "`required` can only be used for object types")
            ]
        )

    def test_invalid_schema_invalid_type_for_min_properties(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "minProperties": 5
            },
            expected_errors=[
                ("#", "`minProperties` can only be used for object types")
            ]
        )

    def test_invalid_schema_invalid_type_for_max_properties(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "integer",
                "maxProperties": 15
            },
            expected_errors=[
                ("#", "`maxProperties` can only be used for object types")
            ]
        )

    def test_invalid_schema_max_properties_must_be_greater_than_min_properties(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "object",
                "minProperties": 15,
                "maxProperties": 5
            },
            expected_errors=[
                ("#", "The value of `maxProperties` must be greater than or equal to `minProperties`")
            ]
        )

    def test_invalid_schema_ambiguous_type(self):
        self._invalid(
            SchemaObjectType,
            {
                "minItems": 20,
                "minProperties": 30
            },
            expected_errors=[
                ("#", "The schema type is ambiguous")
            ]
        )

    def test_invalid_schema_invalid_type_for_discriminator(self):
        self._invalid(
            SchemaObjectType,
            {
                "discriminator": {
                    "propertyName": "petType"
                },
                "allOf": [
                    {
                        "type": "object"
                    }
                ]
            },
            expected_errors=[
                ("#", "The `discriminator` can only be used with the keywords `anyOf` or `oneOf`")
            ]
        )

    def test_invalid_schema_read_only_and_write_only_are_mutually_exclusive(self):
        self._invalid(
            SchemaObjectType,
            {
                "type": "string",
                "readOnly": True,
                "writeOnly": True
            },
            expected_errors=[
                ("#", "`readOnly` and `writeOnly` are mutually exclusive and cannot be set simultaneously")
            ]
        )

    def test_valid_schema_with_recursive_dependency(self):
        self._valid(
            ComponentsObjectType,
            {
                "schemas": {
                    "Pet": {
                        "properties": {
                            "parent": {
                                '$ref': '#/schemas/Pet'
                            }
                        }
                    }
                }
            }
        )

    def test_valid_schema_with_recursive_references(self):
        self._valid(ComponentsObjectType, {
            "schemas": {
                "Pet": {
                    "allOf": [
                        {
                            '$ref': '#/schemas/NewPet'
                        }
                    ]
                },
                "NewPet": {
                    "type": "object",
                    "properties": {
                        "pet": {
                            "$ref": "#/schemas/NewPet"
                        }
                    }
                }
            }
        })

    def test_recursive_references_through_other(self):
        self._invalid(
            ComponentsObjectType,
            {
                "schemas": {
                    "Pet": {
                        "$ref": "#/schemas/Bee"
                    },
                    "Bee": {
                        "$ref": "#/schemas/Pet"
                    }
                }
            },
            expected_errors=[
                ("#/schemas/Bee", "$refs must reference a valid location in the document"),
                ("#/schemas/Pet", "$refs must reference a valid location in the document"),
                ("#/schemas/Pet", "Recursive reference was found")
            ]
        )

    def test_recursive_reference_on_self(self):
        self._invalid(
            ComponentsObjectType,
            {
                "schemas": {
                    "Pet": {
                        "$ref": "#/schemas/Pet"
                    }
                }
            },
            expected_errors=[
                ("#/schemas/Pet", "Recursive reference was found")
            ]
        )

    def test_improperly_x_merge_usage(self):
        self._invalid(
            SchemaObjectType,
            {
                "allOf": [
                    {
                        "type": "integer"
                    },
                    {
                        "type": "string"
                    }
                ],
                "x-merge": True
            },
            expected_errors=[
                ("#", "The types of all subschemas in `allOf` must be the same when `x-merge` is true")
            ]
        )


if __name__ == '__main__':
    unittest.main()
