# Copyright (C) 2023 Helmar Hutschenreuter
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from haystack import Pipeline
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import PreProcessor

from parsing import DocxParser

indexing_pipeline = Pipeline()
document_store = InMemoryDocumentStore(use_bm25=False, embedding_dim=1024)
docx_parser = DocxParser()

preprocessor = PreProcessor(
    language="de",  # TODO: make this configurable
    clean_whitespace=True,
    clean_header_footer=True,
    clean_empty_lines=True,
    split_by="word",
    split_length=50,
    split_overlap=5,
    split_respect_sentence_boundary=True,
    progress_bar=True,
)

# fmt: off
indexing_pipeline.add_node(component=docx_parser, name="DocxParser", inputs=["File"])
indexing_pipeline.add_node(component=preprocessor, name="PreProcessor", inputs=["DocxParser"])
indexing_pipeline.add_node(component=document_store, name="DocumentStore", inputs=["PreProcessor"])
indexing_pipeline.run(file_paths=["../tests/data/test.docx"])
# fmt: on
