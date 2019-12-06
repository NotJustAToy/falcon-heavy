import unittest

from falcon_heavy.core.types.path import Path


class TestPath(unittest.TestCase):

    def test_instantiation(self):
        path = Path('http://domain/specification.yaml#/Pokemon')
        self.assertEqual('http://domain/specification.yaml', path.url)
        self.assertEqual(('Pokemon', ), path.parts)

    def test_elongation(self):
        path = Path('http://domain/specification.yaml#/Pokemon') / 1 / 'Bulbasaur'
        self.assertEqual('http://domain/specification.yaml', path.url)
        self.assertEqual(('Pokemon', '1', 'Bulbasaur'), path.parts)

    def test_escaping(self):
        path = Path('http://domain/specification.yaml#/Pokemon') / '1/~Bulbasaur'
        self.assertEqual('http://domain/specification.yaml', path.url)
        self.assertEqual(('Pokemon', '1/~Bulbasaur'), path.parts)
        self.assertEqual('http://domain/specification.yaml#/Pokemon/1~1~0Bulbasaur', str(path))

    def test_parent_getting(self):
        path = Path('http://domain/specification.yaml#/Pokemon') / 1 / 'Bulbasaur'
        parent = path.parent
        self.assertEqual('http://domain/specification.yaml#/Pokemon/1', str(parent))
        parent = parent.parent
        self.assertEqual('http://domain/specification.yaml#/Pokemon', str(parent))
        parent = parent.parent
        self.assertEqual('http://domain/specification.yaml', str(parent))
        parent = parent.parent
        self.assertEqual('http://domain/specification.yaml', str(parent))

    def test_equaling(self):
        path = Path('http://domain/specification.yaml#/Pokemon')
        self.assertTrue(path == 'http://domain/specification.yaml#/Pokemon')
        self.assertTrue(path == path)


if __name__ == '__main__':
    unittest.main()
