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


from typing import IO

from haystack import Pipeline
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.retrievers import FilterRetriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from ..config import load_config
from ..utils import to_abs_path
from .components import (
    DocxToDocuments,
    DuplicateChecker,
    LocationRemover,
    MergeMetadata,
    SetContentBasedIds,
    new_source_id,
)


def get_document_store():
    return QdrantDocumentStore(
        host="qdrant",
        port=6333,
        grpc_port=6334,
        https=False,
        index="docaudit",  # Name of Qdrant collection
        return_embedding=True,
        wait_result_from_api=True,
        embedding_dim=1024,
        similarity="cosine",
        payload_fields_to_index=[
            dict(
                field_name="id",
                field_schema="keyword",
            ),
            dict(
                field_name="meta.locations[].id",
                field_schema="keyword",
            ),
        ],
    )


def get_embedder(for_documents: bool = True):
    config = load_config().transformers
    embedder_class = (
        SentenceTransformersDocumentEmbedder
        if for_documents
        else SentenceTransformersTextEmbedder
    )
    embedder = embedder_class(
        model=to_abs_path(config.embedding_model),
        progress_bar=True,
        batch_size=32,
        normalize_embeddings=True,
    )
    embedder.warm_up()
    return embedder


def get_indexing_pipeline():
    document_store = get_document_store()

    docx_converter = DocxToDocuments()
    cleaner = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
        remove_repeated_substrings=False,  # like headers or footers
    )
    splitter = DocumentSplitter(
        split_by="word",
        split_length=100,
        split_overlap=0,
    )
    duplicate_checker = DuplicateChecker(document_store=document_store, batch_size=32)
    embedder = get_embedder(for_documents=True)
    writer = DocumentWriter(
        document_store=document_store,
        policy=DuplicatePolicy.FAIL,
    )
    overwriter = DocumentWriter(
        document_store=document_store,
        policy=DuplicatePolicy.OVERWRITE,
    )

    pipeline = Pipeline()
    pipeline.add_component("docx_converter", docx_converter)
    pipeline.add_component("cleaner", cleaner)
    pipeline.add_component("splitter", splitter)
    # Overwrite the IDs with content-based IDs so that documents with the same content
    # have the same IDs.
    pipeline.add_component("content_ids", SetContentBasedIds())
    # Merge documents if the DOCX contains the same content multiple times
    pipeline.add_component("content_merger", MergeMetadata())
    # Check for duplicates in the document store and skip embedding for duplicates
    pipeline.add_component("duplicate_checker", duplicate_checker)
    pipeline.add_component("duplicate_merger", MergeMetadata())
    pipeline.add_component("overwriter", overwriter)
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("writer", writer)

    pipeline.connect("docx_converter", "cleaner")
    pipeline.connect("cleaner", "splitter")
    pipeline.connect("splitter", "content_ids")
    pipeline.connect("content_ids", "content_merger")
    pipeline.connect("content_merger", "duplicate_checker")
    pipeline.connect("duplicate_checker.retrieved", "duplicate_merger")
    pipeline.connect("duplicate_checker.hits", "duplicate_merger")
    pipeline.connect("duplicate_merger", "overwriter")
    pipeline.connect("duplicate_checker.misses", "embedder.documents")
    pipeline.connect("embedder", "writer")

    return pipeline


def get_deindexing_pipeline():
    document_store = get_document_store()
    filter_retriever = FilterRetriever(document_store=document_store)
    overwriter = DocumentWriter(
        document_store=document_store,
        policy=DuplicatePolicy.OVERWRITE,
    )

    pipeline = Pipeline()
    pipeline.add_component("retriever", filter_retriever)
    pipeline.add_component("location_remover", LocationRemover())
    pipeline.add_component("overwriter", overwriter)

    pipeline.connect("retriever", "location_remover")
    pipeline.connect("location_remover", "overwriter")
    return pipeline


def get_querying_pipeline():
    embedder = get_embedder(for_documents=False)
    retriever = QdrantEmbeddingRetriever(document_store=get_document_store())

    pipeline = Pipeline()
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.connect("embedder.embedding", "retriever.query_embedding")

    return pipeline


def index(sources: list[str | IO[bytes]]):
    pipeline = get_indexing_pipeline()
    source_ids = [new_source_id() for _ in range(len(sources))]
    pipeline.run(dict(docx_converter=dict(sources=sources, source_ids=source_ids)))
    return source_ids


def query(
    query: str,
    top_k: int = 3,
    source_ids: list[str] = None,
):
    if source_ids:
        filters = dict(field="meta.locations[].id", operator="in", value=source_ids)
    else:
        filters = None

    pipeline = get_querying_pipeline()
    return pipeline.run(
        dict(
            embedder=dict(text=query),
            retriever=dict(top_k=top_k, filters=filters),
        )
    )["retriever"]["documents"]
