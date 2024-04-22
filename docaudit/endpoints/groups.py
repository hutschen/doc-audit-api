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

from typing import Any

from fastapi import APIRouter, Depends

from ..db.groups import GroupManager, get_group_filters
from ..db.schemas import Group
# from ..ml.indexing import IndexingManager
from .models import GroupInput, GroupOutput

router = APIRouter(tags=["groups"])


@router.get("/groups", response_model=list[GroupOutput])
def get_groups(
    group_manager: GroupManager = Depends(),
    where_clauses: list[Any] = Depends(get_group_filters),
) -> list[Group]:
    return group_manager.list_groups(where_clauses)


@router.post("/groups", status_code=201, response_model=GroupOutput)
def create_group(
    group_input: GroupInput, group_manager: GroupManager = Depends()
) -> Group:
    return group_manager.create_group(group_input)


@router.get("/groups/{group_id}", response_model=GroupOutput)
def get_group(group_id: int, group_manager: GroupManager = Depends()) -> Group:
    return group_manager.get_group(group_id)


@router.put("/groups/{group_id}", response_model=GroupOutput)
def update_group(
    group_id: int,
    group_input: GroupInput,
    group_manager: GroupManager = Depends(),
) -> Group:
    group = group_manager.get_group(group_id)
    group_manager.update_group(group, group_input)
    return group


@router.delete("/groups/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    group_manager: GroupManager = Depends(),
    # indexing_manager: IndexingManager = Depends(),
) -> None:
    group = group_manager.get_group(group_id)
    group_manager.delete_group(group)
    # indexing_manager.delete_index(str(group_id))
