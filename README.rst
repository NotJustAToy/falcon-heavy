************
Falcon Heavy
************


About
#####

The framework for building app backends and microservices by specification-first API design approach based on the `OpenAPI Specification 3 <https://github.com/OAI/OpenAPI-Specification>`__.

Falcon Heavy converts and validates requests and renders responses corresponded specification. It can be used with `Django <https://www.djangoproject.com/>`__, `Falcon <https://falconframework.org/>`__ and `Flask <https://palletsprojects.com/p/flask/>`__ web frameworks.

Installation
############

Recommended way (via pip):

.. code:: bash

    $ pip install falcon-heavy

Usage
#####

1. Implement all abstract methods from a corresponding decorator class.
2. Set up routing based on a specification.
3. Decorate views with your decorator.

Limitations
###########

* XML is not supported.
* Can't use reserved characters in path and query parameters.
* Recursive dependencies detection not implemented.

License
#######

Copyright 2019 Not Just A Toy Corp.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
