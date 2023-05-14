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

from haystack.document_stores.faiss import FAISSDocumentStore
from haystack.nodes import BaseComponent, DenseRetriever
from haystack.schema import Document

from .utils import to_abs_path

FAISS_DOCUMENT_STORE_FILENAME = to_abs_path("faiss/faiss_document_store.db")
FAISS_INDEX_FILENAME = to_abs_path("faiss/faiss_index.faiss")
FAISS_CONFIG_FILENAME = to_abs_path("faiss/faiss_config.json")


def delete_faiss_files():
    for filename in [
        FAISS_DOCUMENT_STORE_FILENAME,
        FAISS_INDEX_FILENAME,
        FAISS_CONFIG_FILENAME,
    ]:
        if os.path.isfile(filename):
            os.remove(filename)


def create_or_load_faiss_document_store():
    if os.path.isfile(FAISS_INDEX_FILENAME) and os.path.isfile(FAISS_CONFIG_FILENAME):
        # Load existing index
        return FAISSDocumentStore.load(FAISS_INDEX_FILENAME, FAISS_CONFIG_FILENAME)
    else:
        # Create new index
        delete_faiss_files()
        return FAISSDocumentStore(
            sql_url=f"sqlite:///{FAISS_DOCUMENT_STORE_FILENAME}",
            faiss_index_factory_str="Flat",
            duplicate_documents="skip",
            embedding_dim=1024,
        )


def update_and_save_embeddings(
    document_store: FAISSDocumentStore, retriever: DenseRetriever
):
    document_store.update_embeddings(retriever, update_existing_embeddings=False)
    document_store.save(FAISS_INDEX_FILENAME, FAISS_CONFIG_FILENAME)


class FAISSDocumentStoreWriter(BaseComponent):
    outgoing_edges = 1
    _write_lock = threading.Lock()

    def __init__(
        self,
        document_store: FAISSDocumentStore,
        retriever: DenseRetriever | None = None,
    ):
        self.document_store = document_store
        self.retriever = retriever

    def run(self, *, documents: list[Document], **kwargs):
        with self._write_lock:
            self.document_store.write_documents(documents, duplicate_documents="skip")
            if self.retriever is not None:
                update_and_save_embeddings(self.document_store, self.retriever)
        return {"documents": documents, **kwargs}, "output_1"

    def run_batch(self, **kwargs):
        raise NotImplementedError(
            "run_batch is not implemented for FAISSDocumentStoreWriter"
        )
