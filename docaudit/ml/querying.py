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

from haystack import Pipeline
from haystack.schema import Document

from .retrieving import get_embedding_retriever
from .storing import get_multi_document_store

embedding_retriever = get_embedding_retriever()
embedding_retriever.document_store = get_multi_document_store()  # type: ignore

# fmt: off
querying_pipeline = Pipeline()
querying_pipeline.add_node(component=embedding_retriever, name="EmbeddingRetriever", inputs=["Query"])
# fmt: on


def query(query: str, index: str | None = None, top_k: int = 3) -> list[Document]:
    results = querying_pipeline.run(
        query=query,
        params={"EmbeddingRetriever": {"top_k": top_k, "index": index}},
    )
    return results.get("documents", []) if results else []
