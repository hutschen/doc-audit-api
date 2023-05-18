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

from typing import Literal

from fastapi import Depends
from haystack import Pipeline
from haystack.schema import Document

from ..utils import cache_first_result
from .parsing import DocxParser
from .preprocessing import LanguageDispatcher, create_preprocessor
from .retrieving import create_embedding_retriever
from .storing import FAISSDocumentStoreWriter, create_or_load_faiss_document_store


@cache_first_result
def create_indexing_pipeline():
    # fmt: off
    docx_parser = DocxParser()
    language_dispatcher = LanguageDispatcher()
    preprocessor_de = create_preprocessor(language="de")
    preprocessor_en = create_preprocessor(language="en")
    embedding_retriever = create_embedding_retriever()
    faiss_document_store = create_or_load_faiss_document_store()
    faiss_document_store_writer = FAISSDocumentStoreWriter(faiss_document_store, embedding_retriever)
    
    indexing_pipeline = Pipeline()
    indexing_pipeline.add_node(component=docx_parser, name="DocxParser", inputs=["File"])
    indexing_pipeline.add_node(component=language_dispatcher, name="LanguageDispatcher", inputs=["DocxParser"])
    indexing_pipeline.add_node(component=preprocessor_de, name="PreProcessorDe", inputs=["LanguageDispatcher.output_1"])
    indexing_pipeline.add_node(component=preprocessor_en, name="PreProcessorEn", inputs=["LanguageDispatcher.output_2"])
    indexing_pipeline.add_node(component=faiss_document_store_writer, name="DocumentStoreWriter", inputs=["PreProcessorDe", "PreProcessorEn"])
    # fmt: on

    return indexing_pipeline


class IndexingManager:
    def __init__(self, indexing_pipeline: Pipeline = Depends(create_indexing_pipeline)):
        self.pipeline = indexing_pipeline

    def index_docx_file(
        self,
        file_path: str,
        language: Literal["de", "en"] | None = None,
        index: str | None = None,
        file_id: int | None = None,
    ) -> list[Document]:
        results = self.pipeline.run(
            file_paths=[file_path],
            meta={
                **({"language": language} if language else {}),
                **({"file_id": file_id} if file_id is not None else {}),
            },
            params={"DocumentStoreWriter": {"index": index}},
        )
        return results.get("documents", []) if results else []
