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

from typing import Literal

from haystack.nodes import BaseComponent, PreProcessor
from haystack.schema import Document


def create_preprocessor(
    *,
    language: Literal["en", "de"] = "en",  # Language must be either 'de' or 'en'
    clean_whitespace: bool = True,
    clean_header_footer: bool = True,
    clean_empty_lines: bool = True,
    split_by: Literal["word", "sentence", "passage"] = "word",
    split_length: int = 50,
    split_overlap: int = 5,
    split_respect_sentence_boundary: bool = True,
    progress_bar: bool = True,
    **kwargs,
) -> PreProcessor:
    return PreProcessor(
        language=language,
        clean_whitespace=clean_whitespace,
        clean_header_footer=clean_header_footer,
        clean_empty_lines=clean_empty_lines,
        split_by=split_by,
        split_length=split_length,
        split_overlap=split_overlap,
        split_respect_sentence_boundary=split_respect_sentence_boundary,
        progress_bar=progress_bar,
        **kwargs,
    )


class LanguageDispatcher(BaseComponent):
    outgoing_edges = 2

    def run(self, *, documents: list[Document], **kwargs):
        en_documents = []
        de_documents = []
        for document in documents:
            if document.meta["language"] == "de":
                de_documents.append(document)
            else:
                en_documents.append(document)

        return [
            ({"documents": en_documents, **kwargs}, "output_1"),
            ({"documents": de_documents, **kwargs}, "output_2"),
        ]

    def run_batch(self, **kwargs):
        raise NotImplementedError("run_batch is not implemented for LanguageDispatcher")
