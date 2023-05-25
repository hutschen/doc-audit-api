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

from fastapi import Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..endpoints.models import GroupInput
from .connection import get_session
from .filtering import filter_by_pattern_many, filter_by_values_many, search_columns
from .operations import delete_from_db, modify_query, read_from_db
from .schemas import Group


class GroupManager:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.session = session

    def list_groups(
        self,
        where_clauses: list[Any] | None = None,
        order_by_clauses: list[Any] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Group]:
        query = modify_query(
            select(Group),
            where_clauses,
            order_by_clauses or [Group.id],
            offset,
            limit,
        )
        return self.session.execute(query).scalars().all()

    def create_group(self, creation: GroupInput, flush: bool = True) -> Group:
        document = Group(**creation.dict())
        self.session.add(document)
        if flush:
            self.session.flush()
        return document

    def get_group(self, group_id: int) -> Group:
        return read_from_db(self.session, Group, group_id)

    def update_group(
        self, group: Group, update: GroupInput, patch: bool = False, flush: bool = True
    ) -> None:
        for key, value in update.dict(exclude_unset=patch).items():
            setattr(group, key, value)

        if flush:
            self.session.flush()

    def delete_group(self, group: Group, flush: bool = True) -> None:
        delete_from_db(self.session, group, flush)


def get_group_filters(
    # filter by pattern
    name: str | None = None,
    #
    # filter by values
    ids: list[int] | None = Query(None),
    #
    # filter by search string
    search: str | None = None,
) -> list[Any]:
    where_clauses = []

    # filter by pattern
    where_clauses.extend(filter_by_pattern_many((Group.name, name)))

    # filter by values
    where_clauses.extend(filter_by_values_many((Group.id, ids)))

    # filter by search string
    if search:
        where_clauses.append(search_columns(search, Group.name))

    return where_clauses
