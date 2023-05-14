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
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from docaudit.models import DocumentInput

from docaudit.schemas import Document, Project
from ..database import CRUDBase, delete_from_db, get_session, read_from_db


class Documents(CRUDBase):
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.session = session

    def list_documents(
        self,
        where_clauses: list[Any] | None = None,
        order_by_clauses: list[Any] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Document]:
        query = self._modify_query(
            select(Document),
            where_clauses,
            order_by_clauses or [Document.id],
            offset,
            limit,
        )
        return self.session.execute(query).scalars().all()

    def create_document(
        self, project: Project, creation: DocumentInput, flush: bool = True
    ) -> Document:
        document = Document(**creation.dict(), project=project)
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
