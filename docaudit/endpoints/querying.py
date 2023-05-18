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


from fastapi import APIRouter, Depends
from haystack.schema import Document

from ..db.groups import GroupManager
from ..endpoints.models import ResultOutput
from ..ml.querying import query

router = APIRouter(tags=["querying"])


@router.get("/groups/{group_id}/query", response_model=list[ResultOutput])
def run_query(
    content: str, group_id: int, top_k: int = 3, group_manager: GroupManager = Depends()
) -> list[Document]:
    group = group_manager.get_group(group_id)
    return query(content, index=str(group.id), top_k=top_k)
