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

from ..endpoints.models import DocumentInput
from .connection import get_session
from .filtering import filter_by_pattern_many, filter_by_values_many, search_columns
from .operations import delete_from_db, modify_query, read_from_db
from .schemas import Document, Group


class DocumentManager:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.session = session

    def list_documents(
        self,
        where_clauses: list[Any] | None = None,
        order_by_clauses: list[Any] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Document]:
        query = modify_query(
            select(Document),
            where_clauses,
            order_by_clauses or [Document.id],
            offset,
            limit,
        )
        return self.session.execute(query).scalars().all()

    def create_document(
        self, group: Group, creation: DocumentInput, flush: bool = True
    ) -> Document:
        document = Document(**creation.dict())
        document.group = group
        self.session.add(document)
        if flush:
            self.session.flush()
        return document

    def get_document(self, document_id: int) -> Document:
        return read_from_db(self.session, Document, document_id)

    def update_document(
        self,
        document: Document,
        update: DocumentInput,
        patch: bool = False,
        flush: bool = True,
    ) -> None:
        # Update document
        for key, value in update.dict(exclude_unset=patch).items():
            setattr(document, key, value)

        if flush:
            self.session.flush()

    def delete_document(self, document: Document, flush: bool = True) -> None:
        delete_from_db(self.session, document, flush)


def get_document_filters(
    # filter by pattern
    title: str | None = None,
    #
    # filter by values
    languages: list[str] | None = Query(None),
    ids: list[int] | None = Query(None),
    group_ids: list[int] | None = Query(None),
    #
    # filter by search string
    search: str | None = None,
) -> list[Any]:
    where_clauses = []

    # filter by pattern
    where_clauses.extend(filter_by_pattern_many((Document.title, title)))

    # filter by values
    where_clauses.extend(
        filter_by_values_many(
            (Document.id, ids),
            (Document.language, languages),
            (Document.group_id, group_ids),
        )
    )

    # filter by search string
    if search:
        where_clauses.append(search_columns(search, Document.title))

    return where_clauses
