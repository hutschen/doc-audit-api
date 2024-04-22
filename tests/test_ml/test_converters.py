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

from docaudit.ml.converters import DocxParser, DocxToDocuments
from haystack import Pipeline


# TODO: Build up a test Document with python-docx and test parsing it.
def test_parse_docx():
    list(DocxParser.parse("tests/data/test.docx"))


def test_parse_docx_pipeline():
    docx_converter = DocxToDocuments()

    parsing_pipeline = Pipeline()
    parsing_pipeline.add_component("docx_converter", docx_converter)
    parsing_pipeline.run(dict(docx_converter=dict(sources=["tests/data/test.docx"])))
