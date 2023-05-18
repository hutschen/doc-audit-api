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

from haystack.document_stores.faiss import FAISSDocumentStore
from haystack.nodes import BaseComponent, EmbeddingRetriever
from haystack.schema import Document

from ..utils import to_abs_path


# TODO: Make this thread-safe using a read-write lock
class GroupDocumentStore:
    FAISS_DIRNAME = to_abs_path("faiss")

    def __init__(self, group_id: int):
        # fmt: off
        self._db_filename = os.path.join(self.FAISS_DIRNAME, f"{group_id}_faiss_document_store.db")
        self._index_filename = os.path.join(self.FAISS_DIRNAME, f"{group_id}_faiss_index.faiss")
        self.document_store = self._create_or_load_document_store()
        self._user_count = 0
        # fmt: on

    def _delete_files(self):
        for filename in [self._db_filename, self._index_filename]:
            if os.path.isfile(filename):
                os.remove(filename)

    def _create_or_load_document_store(self) -> FAISSDocumentStore:
        config = dict(
            sql_url=f"sqlite:///{self._db_filename}",
            faiss_index_factory_str="Flat",
            duplicate_documents="skip",
            embedding_dim=1024,
            similarity="cosine",
        )

        if os.path.isfile(self._index_filename) and os.path.isfile(self._db_filename):
            # Load existing document store
            return FAISSDocumentStore(faiss_index_path=self._index_filename, **config)
        else:
            # Create new document store
            self._delete_files()
            return FAISSDocumentStore(**config)

    def write_documents(
        self, documents: list[Document], retriever: EmbeddingRetriever
    ) -> None:
        self.document_store.write_documents(documents, duplicate_documents="skip")
        # Update and save embeddings
        self.document_store.update_embeddings(
            retriever, update_existing_embeddings=False
        )
        self.document_store.save(self._index_filename)

    def delete_documents(self, file_id: int | None = None):
        self.document_store.delete_documents(
            filters={"file_id": [file_id]} if file_id is not None else None,
        )
        self.document_store.save(self._index_filename)

    def query_by_embedding(self, *args, **kwargs):
        """Method is used in EmbeddingRetriever.retrieve"""
        # TODO: Check if this is thread-safe (probably not) / use read lock
        return self.document_store.query_by_embedding(*args, **kwargs)


class MultiGroupDocumentStore(BaseComponent):
    outgoing_edges = 1

    def __init__(self):
        self.document_stores_lock = threading.Lock()
        self.document_stores: dict[int, GroupDocumentStore] = {}
        self.index = "document"  # Attribute is used in EmbeddingRetriever.retrieve

    def _acquire_document_store(self, group_id: int):
        with self.document_stores_lock:
            if group_id not in self.document_stores:
                self.document_stores[group_id] = GroupDocumentStore(group_id)
            self.document_stores[group_id]._user_count += 1
            return self.document_stores[group_id]

    def _release_document_store(self, index):
        with self.document_stores_lock:
            self.document_stores[index]._user_count -= 1
            if self.document_stores[index]._user_count == 0:
                del self.document_stores[index]

    @contextmanager
    def _document_store(self, index):
        document_store = self._acquire_document_store(index)
        try:
            yield document_store
        finally:
            self._release_document_store(index)

    def run(
        self,
        *,
        documents: list[Document],
        index: str,
        retriever: EmbeddingRetriever,
        **kwargs,
    ):
        # Method will be called by indexing pipeline
        with self._document_store(index) as document_store:
            document_store.write_documents(documents, retriever)
            return {"documents": documents, **kwargs}, "output_1"

    def run_batch(self, **_):
        raise NotImplementedError(
            "run_batch is not implemented for MultiGroupDocumentStore"
        )

    def query_by_embedding(self, *args, **kwargs):
        with self._document_store(self.index) as document_store:
            return document_store.query_by_embedding(*args, **kwargs)


@lru_cache()
def get_multi_group_document_store():
    return MultiGroupDocumentStore()
