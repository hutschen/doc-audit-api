# Copyright (C) 2024 Helmar Hutschenreuter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest
from haystack import Pipeline

from docaudit.ml.converters import DocxParser, DocxToDocuments, recursively_merge_dicts
from docaudit.ml.index import get_indexing_pipeline, get_querying_pipeline


@pytest.mark.parametrize(
    "d1,d2,expected",
    [
        # General assumption: Values of d1 have priority
        # Case 1: Empty dictionaries
        ({}, {}, {}),
        # Case 2: No overlapping keys
        ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
        # Case 3: Overlapping keys, no deeper structures
        ({"a": 1}, {"a": 2}, {"a": 1}),
        # Case 4: Nested dictionaries
        ({"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 1}}),
        # Case 5: Lists as values
        ({"a": [1, 2]}, {"a": [3, 4]}, {"a": [1, 2, 3, 4]}),
        # Case 6: Lists with dictionaries as values
        ({"a": [{"b": 1}]}, {"a": [{"b": 2}]}, {"a": [{"b": 1}, {"b": 2}]}),
        # Case 7: Unequal structures for equal keys, reversion to d1 value
        ({"a": [1, 2]}, {"a": {"b": 2}}, {"a": [1, 2]}),
        # Case 8: A key only in d2
        ({}, {"a": 2}, {"a": 2}),
    ],
)
def test_recursively_merge_dicts(d1, d2, expected):
    assert recursively_merge_dicts(d1, d2) == expected


# TODO: Build up a test Document with python-docx and test parsing it.
def test_parse_docx():
    list(DocxParser.parse("tests/data/test.docx"))


def test_parse_docx_pipeline():
    docx_converter = DocxToDocuments()

    parsing_pipeline = Pipeline()
    parsing_pipeline.add_component("docx_converter", docx_converter)
    parsing_pipeline.run(dict(docx_converter=dict(sources=["tests/data/test.docx"])))


def test_index_pipeline():
    pipeline = get_indexing_pipeline()
    result = pipeline.run(dict(docx_converter=dict(sources=["tests/data/test.docx"])))
    print(result["writer"])


def test_query_pipeline():
    pipeline = get_querying_pipeline()
    result = pipeline.run(
        dict(
            embedder=dict(text="Active content has to be disabled."),
            retriever=dict(
                top_k=3,
                # filters=dict(
                #     field="id",
                #     operator="==",
                #     value="2a0f71336c6fe56bc3c14c5965975751233142a0f47fe034b5a1eeac222dfe1e",
                # ),
            ),
        )
    )
    print(result["retriever"]["documents"])
