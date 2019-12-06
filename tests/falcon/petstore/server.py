from falcon import API

from falcon_heavy.contrib.name_resolver import RuntimeNameResolver

from .openapi import operations

app = API()

resolver = RuntimeNameResolver(base_path='tests.falcon.petstore')
for path, mapping in operations.items():
    first = next(iter(mapping.values()))

    resource_id = first.extensions.get('x-resource')
    if resource_id is None:
        continue

    resource_class = resolver.resolve(resource_id, silent=False)
    if resource_class is None:
        continue

    app.add_route(path.template, resource_class())
