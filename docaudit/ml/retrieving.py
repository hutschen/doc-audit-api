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


from functools import lru_cache
from haystack.document_stores.base import get_batches_from_generator
from haystack.nodes import EmbeddingRetriever, BaseComponent
from haystack.schema import Document
from tqdm.auto import tqdm


@lru_cache()
def get_embedding_retriever():
    # Create embedding retriever that can process German texts
    return EmbeddingRetriever(
        embedding_model="deutsche-telekom/gbert-large-paraphrase-cosine",
        use_gpu=False,
    )


class EmbeddingGenerator(BaseComponent):
    outgoing_edges = 1

    def __init__(
        self,
        retriever: EmbeddingRetriever,
        progress_bar: bool = True,
        batch_size: int = 10_000,
    ):
        self.retriever = retriever
        self.progress_bar = progress_bar
        self.batch_size = batch_size

    def run(self, *, documents: list[Document], **kwargs):
        document_count = len(documents)
        batched_documents = get_batches_from_generator(documents, self.batch_size)
        with tqdm(
            total=document_count,
            disable=not self.progress_bar,
            position=0,
            unit=" docs",
            desc="Generating embeddings",
        ) as progress_bar:
            for document_batch in batched_documents:
                embeddings = self.retriever.embed_documents(document_batch)  # type: ignore
                for document, embedding in zip(document_batch, embeddings):
                    document.embedding = embedding

                progress_bar.set_description("Documents processed")
                progress_bar.update(self.batch_size)

        return {"documents": documents, **kwargs}, "output_1"

    def run_batch(self, **kwargs):
        raise NotImplementedError("run_batch is not implemented for EmbeddingGenerator")
