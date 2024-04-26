# Copyright (C) 2024 Helmar Hutschenreuter
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from fastapi import APIRouter
from pydantic import BaseModel
import haystack

router = APIRouter(tags=["query"])


class ResultLocation(BaseModel):
    id: str
    type: str
    path: str


class Result(BaseModel):
    id: str
    score: float
    content: str
    locations: list[ResultLocation]

    @classmethod
    def from_haystack_document(
        cls,
        haystack_document: haystack.Document,
        queried_source_ids: list[str] | None = None,
    ) -> "Result":
        """
        Convert a Haystack Document to a Result object.

        Args:
            haystack_document: Document from Haystack
            queried_source_ids: List of source IDs queried so that only locations for
            those sources are included in the result.
        """
        locations = [
            ResultLocation(**location)
            for location in haystack_document.meta.get("locations", [])
            if queried_source_ids is None or location["id"] in queried_source_ids
        ]

        return cls(
            id=haystack_document.id,
            score=haystack_document.score,
            content=haystack_document.content,
            locations=locations,
        )
