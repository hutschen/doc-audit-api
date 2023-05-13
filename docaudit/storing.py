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

from haystack.document_stores.faiss import FAISSDocumentStore


def create_faiss_document_store():
    return FAISSDocumentStore(
        sql_url="sqlite:///faiss_document_store.db",
        faiss_index_factory_str="Flat",
        duplicate_documents="skip",
        embedding_dim=1024,
    )


def save_faiss_document_store(document_store: FAISSDocumentStore):
    document_store.save("faiss_index.faiss", "faiss_config.json")
