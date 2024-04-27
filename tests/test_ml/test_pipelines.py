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

from haystack import Pipeline
import pytest

from docaudit.ml.components import DocxToDocuments
from docaudit.ml.pipelines import get_indexing_pipeline, run_query_pipeline


@pytest.mark.sketched
def test_parse_docx_pipeline():
    docx_converter = DocxToDocuments()

    parsing_pipeline = Pipeline()
    parsing_pipeline.add_component("docx_converter", docx_converter)
    parsing_pipeline.run(dict(docx_converter=dict(sources=["tests/data/test.docx"])))


@pytest.mark.sketched
def test_index_pipeline():
    pipeline = get_indexing_pipeline()
    result = pipeline.run(dict(docx_converter=dict(sources=["tests/data/test.docx"])))
    print(result["writer"])


@pytest.mark.sketched
def test_query_pipeline():
    documents = run_query_pipeline("Active content has to be disabled.")
    print(documents)
