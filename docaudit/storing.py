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

from haystack.document_stores.faiss import FAISSDocumentStore
from haystack.nodes import DenseRetriever


def delete_faiss_files():
    for filename in [
        "faiss_document_store.db",
        "faiss_index.faiss",
        "faiss_config.json",
    ]:
        if os.path.isfile(filename):
            os.remove(filename)


def create_or_load_faiss_document_store():
    if os.path.isfile("faiss_index.faiss") and os.path.isfile("faiss_config.json"):
        # Load existing index
        return FAISSDocumentStore.load("faiss_index.faiss", "faiss_config.json")
    else:
        # Create new index
        delete_faiss_files()
        return FAISSDocumentStore(
            sql_url="sqlite:///faiss_document_store.db",
            faiss_index_factory_str="Flat",
            duplicate_documents="skip",
            embedding_dim=1024,
        )


def update_and_save_embeddings(
    document_store: FAISSDocumentStore, retriever: DenseRetriever
):
    document_store.update_embeddings(retriever, update_existing_embeddings=False)
    document_store.save("faiss_index.faiss", "faiss_config.json")
