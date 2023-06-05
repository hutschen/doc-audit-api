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

import os
import threading
from contextlib import contextmanager
from functools import lru_cache
from typing import cast

from tqdm.auto import tqdm
from haystack.document_stores.base import get_batches_from_generator
from haystack.document_stores.faiss import FAISSDocumentStore
from haystack.nodes import BaseComponent, EmbeddingRetriever
from haystack.schema import Document

from ..errors import NotFoundError
from ..utils import to_abs_path


# TODO: Make this thread-safe using a read-write lock
class SubDocumentStore:
    FAISS_DIRNAME = to_abs_path("faiss")

    def __init__(self, index: str):
        # fmt: off
        self._index_name = index
        self._db_filename = os.path.join(self.FAISS_DIRNAME, f"{index}_faiss_document_store.db")
        self._index_filename = os.path.join(self.FAISS_DIRNAME, f"{index}_faiss_index.faiss")
        self._config_filename = os.path.join(self.FAISS_DIRNAME, f"{index}_faiss_config.json")
        # fmt: on

        self.document_store = self._create_or_load_document_store()
        self.document_store_lock = threading.Lock()

        self._mark_for_deletion = False
        self._user_count = 0

    def delete_files(self):
        for filename in [
            self._db_filename,
            self._index_filename,
            self._config_filename,
        ]:
            if os.path.isfile(filename):
                os.remove(filename)

    def _create_or_load_document_store(self) -> FAISSDocumentStore:
        if os.path.isfile(self._index_filename) and os.path.isfile(self._db_filename):
            # Load existing document store
            return FAISSDocumentStore.load(self._index_filename, self._config_filename)
        else:
            # Create new document store
            self.delete_files()
            return FAISSDocumentStore(
                sql_url=f"sqlite:///{self._db_filename}",
                faiss_index_factory_str="Flat",
                duplicate_documents="skip",
                embedding_dim=1024,
                similarity="cosine",
                index=self._index_name,
            )

    def _compute_embeddings(
        self,
        documents: list[Document],
        retriever: EmbeddingRetriever,
        batch_size: int = 10_000,
    ) -> None:
        document_count = len(documents)
        batched_documents = get_batches_from_generator(documents, batch_size)
        with tqdm(
            total=document_count,
            disable=not self.document_store.progress_bar,
            position=0,
            unit=" docs",
            desc="Generating embeddings",
        ) as progress_bar:
            for document_batch in batched_documents:
                document_batch = cast(list[Document], document_batch)
                embeddings = retriever.embed_documents(document_batch)

                self.document_store._validate_embeddings_shape(
                    embeddings=embeddings,
                    num_documents=len(document_batch),
                    embedding_dim=self.document_store.embedding_dim,
                )

                if self.document_store.similarity == "cosine":
                    self.document_store.normalize_embedding(embeddings)

                for document, embedding in zip(document_batch, embeddings):
                    document.embedding = embedding

                progress_bar.set_description("Documents processed")
                progress_bar.update(batch_size)

    def write_documents(
        self, documents: list[Document], retriever: EmbeddingRetriever | None = None
    ) -> None:
        # Compute embeddings
        if retriever is not None:
            self._compute_embeddings(documents, retriever)
        with self.document_store_lock:
            self.document_store.write_documents(
                documents, index=self._index_name, duplicate_documents="skip"
            )
            self.document_store.save(self._index_filename, self._config_filename)

    def delete_documents(self, file_id: int | None = None):
        with self.document_store_lock:
            document_ids = [
                d.id
                for d in self.document_store.get_all_documents_generator(
                    index=self._index_name,
                    filters={"file_id": [file_id]} if file_id is not None else None,
                )
            ]
            self.document_store.delete_documents(
                index=self._index_name, ids=document_ids
            )
            self.document_store.save(self._index_filename, self._config_filename)

    def query_by_embedding(self, *args, **kwargs):
        """Method is used in EmbeddingRetriever.retrieve"""
        # TODO: Check if this is thread-safe (probably not) / use read lock
        with self.document_store_lock:
            return self.document_store.query_by_embedding(
                *args, index=self._index_name, **kwargs
            )


class MultiDocumentStore(BaseComponent):
    outgoing_edges = 1

    def __init__(self):
        self.document_stores_lock = threading.Lock()
        self.document_stores: dict[str, SubDocumentStore] = {}
        self.index = "document"  # Attribute is used in EmbeddingRetriever.retrieve
        self.retriever: EmbeddingRetriever | None = None

    def _acquire_document_store(self, index: str):
        with self.document_stores_lock:
            if index not in self.document_stores:
                self.document_stores[index] = SubDocumentStore(index)
            if self.document_stores[index]._mark_for_deletion:
                raise NotFoundError(
                    f"Document store with index '{index}' is marked for deletion"
                )
            self.document_stores[index]._user_count += 1
            return self.document_stores[index]

    def _release_document_store(self, index: str):
        with self.document_stores_lock:
            self.document_stores[index]._user_count -= 1
            if self.document_stores[index]._user_count == 0:
                if self.document_stores[index]._mark_for_deletion:
                    self.document_stores[index].delete_files()
                del self.document_stores[index]

    @contextmanager
    def sub_document_store(self, index):
        document_store = self._acquire_document_store(index)
        try:
            yield document_store
        finally:
            self._release_document_store(index)

    def delete_sub_document_store(self, index: str):
        with self.sub_document_store(index) as document_store:
            with self.document_stores_lock:
                document_store._mark_for_deletion = True

    def run(
        self,
        *,
        documents: list[Document],
        index: str,
        **kwargs,
    ):
        # Method will be called by indexing pipeline
        with self.sub_document_store(index) as document_store:
            document_store.write_documents(documents, self.retriever)
            return {"documents": documents, **kwargs}, "output_1"

    def run_batch(self, **_):
        raise NotImplementedError(
            "run_batch is not implemented for MultiGroupDocumentStore"
        )

    def query_by_embedding(self, *args, index: str, **kwargs):
        with self.sub_document_store(index) as document_store:
            return document_store.query_by_embedding(*args, **kwargs)


@lru_cache()
def get_multi_document_store():
    return MultiDocumentStore()
