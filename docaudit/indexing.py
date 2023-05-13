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
from parsing import DocxParser
from preprocessing import create_preprocessor, LanguageDispatcher
from storing import create_faiss_document_store, save_faiss_document_store

indexing_pipeline = Pipeline()
docx_parser = DocxParser()
faiss_document_store = create_faiss_document_store()

language_dispatcher = LanguageDispatcher()
preprocessor_de = create_preprocessor(language="de")
preprocessor_en = create_preprocessor(language="en")

# fmt: off
indexing_pipeline.add_node(component=docx_parser, name="DocxParser", inputs=["File"])
indexing_pipeline.add_node(component=language_dispatcher, name="LanguageDispatcher", inputs=["DocxParser"])
indexing_pipeline.add_node(component=preprocessor_de, name="PreProcessorDe", inputs=["LanguageDispatcher.output_1"])
indexing_pipeline.add_node(component=preprocessor_en, name="PreProcessorEn", inputs=["LanguageDispatcher.output_2"])
indexing_pipeline.add_node(component=faiss_document_store, name="DocumentStore", inputs=["PreProcessorDe", "PreProcessorEn"])
indexing_pipeline.run(file_paths=["../tests/data/test.docx"], meta={"language": "de"})
# fmt: on

save_faiss_document_store(faiss_document_store)
