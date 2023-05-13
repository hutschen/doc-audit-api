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

from haystack.nodes import BaseComponent
from haystack.schema import Document


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
