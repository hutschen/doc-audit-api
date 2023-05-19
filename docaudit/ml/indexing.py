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

from functools import lru_cache
from typing import Literal

from haystack import Pipeline
from haystack.schema import Document

from .parsing import DocxParser
from .preprocessing import LanguageDispatcher, create_preprocessor
from .retrieving import get_embedding_retriever
from .storing import get_multi_document_store


@lru_cache()
def get_indexing_pipeline():
    # fmt: off
    docx_parser = DocxParser()
    language_dispatcher = LanguageDispatcher()
    preprocessor_de = create_preprocessor(language="de")
    preprocessor_en = create_preprocessor(language="en")
    document_store = get_multi_document_store()
    document_store.retriever = get_embedding_retriever()
    
    indexing_pipeline = Pipeline()
    indexing_pipeline.add_node(component=docx_parser, name="DocxParser", inputs=["File"])
    indexing_pipeline.add_node(component=language_dispatcher, name="LanguageDispatcher", inputs=["DocxParser"])
    indexing_pipeline.add_node(component=preprocessor_de, name="PreProcessorDe", inputs=["LanguageDispatcher.output_1"])
    indexing_pipeline.add_node(component=preprocessor_en, name="PreProcessorEn", inputs=["LanguageDispatcher.output_2"])
    indexing_pipeline.add_node(component=document_store, name="DocumentStore", inputs=["PreProcessorDe", "PreProcessorEn"])
    # fmt: on

    return indexing_pipeline


class IndexingManager:
    def __init__(self):
        self.pipeline = get_indexing_pipeline()
        self.multi_document_store = get_multi_document_store()

    def index_docx_file(
        self,
        file_path: str,
        index: str,
        language: Literal["de", "en"] | None = None,
        file_id: int | None = None,
    ) -> list[Document]:
        results = self.pipeline.run(
            file_paths=[file_path],
            meta={
                **({"language": language} if language else {}),
                **({"file_id": file_id} if file_id is not None else {}),
            },
            params={"DocumentStore": {"index": index}},
        )
        return results.get("documents", []) if results else []

    def unindex_file(self, index: str, file_id: int) -> None:
        with self.multi_document_store.sub_document_store(index) as document_store:
            document_store.delete_documents(file_id)

    def delete_index(self, index: str) -> None:
        self.multi_document_store.delete_sub_document_store(index)
