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
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from ..config import load_config
from ..utils import to_abs_path
from .converters import DocxToDocuments


def get_indexing_pipeline():
    config = load_config().transformers

    document_store = QdrantDocumentStore(
        host="qdrant",
        port=6333,
        grpc_port=6334,
        https=False,
        recreate_index=True,
        return_embedding=True,
        wait_result_from_api=True,
        embedding_dim=1024,
        similarity="cosine",
    )

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
    embedder = SentenceTransformersDocumentEmbedder(
        model=to_abs_path(config.embedding_model),
        progress_bar=True,
        batch_size=32,
        normalize_embeddings=True,
    )
    embedder.warm_up()
    writer = DocumentWriter(
        document_store=document_store,
        policy=DuplicatePolicy.SKIP,
    )

    pipeline = Pipeline()
    pipeline.add_component("docx_converter", docx_converter)
    pipeline.add_component("cleaner", cleaner)
    pipeline.add_component("splitter", splitter)
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("writer", writer)

    pipeline.connect("docx_converter", "cleaner")
    pipeline.connect("cleaner", "splitter")
    pipeline.connect("splitter", "embedder")
    pipeline.connect("embedder", "writer")

    return pipeline
