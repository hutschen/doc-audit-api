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


from functools import lru_cache
from typing import IO, Any

from haystack import Document, Pipeline
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.retrievers import FilterRetriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack.utils import Secret
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from ..config import get_config
from ..utils import to_abs_path
from .components import (
    DocxToDocuments,
    DuplicateChecker,
    LocationRemover,
    MergeMetadata,
    SetContentBasedIds,
)


def get_document_store():
    config = get_config().qdrant
    return QdrantDocumentStore(
        host=config.host,
        port=config.port,
        grpc_port=config.grpc_port,
        prefer_grpc=config.prefer_grpc,
        https=config.https,
        api_key=Secret.from_token(config.api_key) if config.api_key else None,
        index=config.collection_name,
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
    config = get_config().haystack
    embedder_class = (
        SentenceTransformersDocumentEmbedder
        if for_documents
        else SentenceTransformersTextEmbedder
    )
    embedder = embedder_class(
        model=(
            config.embedding_model
            if config.remote_model
            else to_abs_path(config.embedding_model)
        ),
        progress_bar=True,
        batch_size=config.batch_size,
        normalize_embeddings=True,
    )
    embedder.warm_up()
    return embedder


@lru_cache
def get_indexing_pipeline():
    config = get_config().haystack
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
    duplicate_checker = DuplicateChecker(
        document_store=document_store,
        batch_size=config.batch_size,
    )
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


@lru_cache
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


@lru_cache
def get_querying_pipeline():
    embedder = get_embedder(for_documents=False)
    retriever = QdrantEmbeddingRetriever(document_store=get_document_store())

    pipeline = Pipeline()
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.connect("embedder.embedding", "retriever.query_embedding")

    return pipeline


def run_indexing_pipeline(
    sources: list[str | IO[bytes]], source_ids: list[str] | None = None
) -> dict[str, Any]:
    return get_indexing_pipeline().run(
        dict(docx_converter=dict(sources=sources, source_ids=source_ids))
    )


def run_deindexing_pipeline(source_ids: list[str]) -> dict[str, Any]:
    filters = dict(field="meta.locations[].id", operator="in", value=source_ids)
    return get_deindexing_pipeline().run(
        dict(
            retriever=dict(filters=filters),
            location_remover=dict(source_ids=source_ids),
        )
    )


def is_indexed(source_id: str) -> bool:
    filters = dict(field="meta.locations[].id", operator="==", value=source_id)

    # TODO: Count documents for a more efficient check if a source is indexed
    return bool(len(get_document_store().filter_documents(filters=filters)))


def are_indexed(source_ids: list[str]) -> dict[str, bool]:
    if not source_ids:
        return {}

    filters = dict(field="meta.locations[].id", operator="in", value=source_ids)
    missing_source_ids = set(source_ids)
    for doc in get_document_store().get_documents_generator(filters=filters):
        for location in doc.meta.get("locations", []):
            missing_source_ids.discard(location["id"])
        if not missing_source_ids:  # All source IDs are found
            break

    return {source_id: source_id not in missing_source_ids for source_id in source_ids}


def run_query_pipeline(
    query: str,
    top_k: int = 3,
    source_ids: list[str] = None,
) -> list[Document] | None:
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
