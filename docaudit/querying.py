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
from retrieving import create_embedding_retriever
from storing import create_or_load_faiss_document_store

faiss_document_store = create_or_load_faiss_document_store()
embedding_retriever = create_embedding_retriever(faiss_document_store)

# fmt: off
querying_pipeline = Pipeline()
querying_pipeline.add_node(component=embedding_retriever, name="EmbeddingRetriever", inputs=["Query"])
# fmt: on

if __name__ == "__main__":
    while True:
        query = input("Please enter query: ")
        results = querying_pipeline.run(
            query=query, params={"EmbeddingRetriever": {"top_k": 3}}
        )

        # Print out the results
        for result in results["documents"]:  # type: ignore
            print(f"Text: {result.content} (Score: {result.score})")
            print("-" * 100)
