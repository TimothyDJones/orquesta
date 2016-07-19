# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from orchestra.expressions import default as expr
from orchestra.specs import types
from orchestra.specs.v2 import base


class MockSpec(base.BaseSpec):
    _version = '2.0'

    _schema = {
        'type': 'object',
        'properties': {
            'attr1': types.NONEMPTY_STRING,
            'attr2': types.NONEMPTY_DICT,
            'attr3': types.NONEMPTY_STRING
        },
        'required': ['attr1'],
        'additionalProperties': False
    }

    _expr_paths = ['attr3']

    @classmethod
    def _validate_expressions(cls, spec):
        evaluator = cls.get_expr_evaluator('yaql')

        errors = []

        for path in cls._expr_paths:
            errors = evaluator.validate(spec.get(path, ''))

            for error in errors:
                error['spec_path'] = path
                error['schema_path'] = 'properties.%s' % path

        return errors

class BaseSpecTest(unittest.TestCase):

    def setUp(self):
        super(BaseSpecTest, self).setUp()
        self.maxDiff = None

    def test_get_schema(self):
        schema = {
            'type': 'object',
            'properties': {
                'name': types.NONEMPTY_STRING,
                'version': dict(
                    list(types.VERSION.items()) +
                    [('enum', ['2.0', 2.0])]
                ),
                'description': types.NONEMPTY_STRING,
                'tags': types.UNIQUE_STRING_LIST,
                'attr1': types.NONEMPTY_STRING,
                'attr2': types.NONEMPTY_DICT,
                'attr3': types.NONEMPTY_STRING
            },
            'required': ['attr1', 'name', 'version'],
            'additionalProperties': False
        }

        self.assertDictEqual(schema, MockSpec.get_schema())

    def test_get_schema_no_meta(self):
        schema = {
            'type': 'object',
            'properties': {
                'attr1': types.NONEMPTY_STRING,
                'attr2': types.NONEMPTY_DICT,
                'attr3': types.NONEMPTY_STRING
            },
            'required': ['attr1'],
            'additionalProperties': False
        }

        self.assertDictEqual(schema, MockSpec.get_schema(includes=None))

    def test_get_expr_evaluator(self):
        evaluator = MockSpec.get_expr_evaluator('yaql')

        self.assertTrue(evaluator is expr.YAQLEvaluator)

    def test_spec_valid(self):
        spec = {
            'name': 'mock',
            'version': '2.0',
            'description': 'This is a mock spec.',
            'attr1': 'foobar',
            'attr2': {
                'macro': 'polo'
            }
        }

        self.assertDictEqual(MockSpec.validate(spec), {})

    def test_spec_invalid(self):
        spec = {
            'name': 'mock',
            'version': '1.0',
            'description': 'This is a mock spec.',
            'attr2': {
                'macro': 'polo'
            },
            'attr3': '<% 1 +/ 2 %> and <% {"a": 123} %>'
        }

        errors = {
            'syntax': [
                {
                    'spec_path': None,
                    'schema_path': 'required',
                    'message': '\'attr1\' is a required property'
                },
                {
                    'spec_path': 'version',
                    'schema_path': 'properties.version.enum',
                    'message': '\'1.0\' is not one of [\'2.0\', 2.0]'
                }
            ],
            'expressions': [
                {
                    'expression': '1 +/ 2',
                    'spec_path': 'attr3',
                    'schema_path': 'properties.attr3',
                    'message': 'Parse error: unexpected \'/\' at '
                               'position 3 of expression \'1 +/ 2\''
                },
                {
                    'expression': '{"a": 123}',
                    'spec_path': 'attr3',
                    'schema_path': 'properties.attr3',
                    'message': 'Lexical error: illegal character '
                               '\':\' at position 4',
                }
            ]
        }

        self.assertDictEqual(errors, MockSpec.validate(spec))
