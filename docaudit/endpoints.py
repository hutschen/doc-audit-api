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
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Select
from fastapi import APIRouter, Depends

from .database import get_session
from .schemas import Project
from .models import ProjectOutput


class CRUDBase:
    @staticmethod
    def _modify_query(
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


class Projects(CRUDBase):
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def list_projects(
        self,
        where_clauses: list[Any] | None = None,
        order_by_clauses: list[Any] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Project]:
        # Construct projects query
        query = self._modify_query(
            select(Project),
            where_clauses,
            order_by_clauses or [Project.id],
            offset,
            limit,
        )

        # Execute query
        return self.session.execute(query).scalars().all()


project_router = APIRouter(tags=["projects"])


@project_router.get("/projects", response_model=list[ProjectOutput])
def get_projects(projects: Projects = Depends(Projects)) -> list[Project]:
    return projects.list_projects()
