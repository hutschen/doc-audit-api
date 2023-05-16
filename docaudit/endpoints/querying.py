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


from fastapi import APIRouter
from haystack.schema import Document

from ..endpoints.models import ResultOutput
from ..ml.querying import query


router = APIRouter(tags=["querying"])


@router.get("/query", response_model=list[ResultOutput])
def run_query(query_: str, top_k: int = 3) -> list[Document]:
    return query(query_, top_k=top_k)
