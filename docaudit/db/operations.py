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

from typing import Any, Type, TypeVar

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Select

from ..errors import NotFoundError
from .connection import Base

T = TypeVar("T", bound=Base)


def modify_query(
    query: Select,
    where_clauses: list[Any] | None = None,
    order_by_clauses: list[Any] | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Select:
    """Modify a query to include all required clauses and offset and limit."""
    if where_clauses:
        query = query.where(*where_clauses)
    if order_by_clauses:
        query = query.order_by(*order_by_clauses)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query


def read_from_db(session: Session, orm_class: Type[T], id: int) -> T:
    item = session.get(orm_class, id)
    if item:
        return item
    else:
        item_name = orm_class.__name__
        raise NotFoundError(f"No {item_name} with id={id}.")


def delete_from_db(session: Session, item: Any, flush: bool = False) -> None:
    session.delete(item)
    if flush:
        session.flush()
