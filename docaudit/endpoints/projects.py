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
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.connection import CRUDBase, delete_from_db, get_session, read_from_db
from ..models import ProjectInput, ProjectOutput
from ..db.schemas import Project


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

    def create_project(self, creation: ProjectInput, flush: bool = True) -> Project:
        project = Project(**creation.dict())
        self.session.add(project)
        if flush:
            self.session.flush()
        return project

    def get_project(self, project_id: int) -> Project:
        return read_from_db(self.session, Project, project_id)

    def update_project(
        self,
        project: Project,
        update: ProjectInput,
        patch: bool = False,
        flush: bool = True,
    ) -> None:
        # Update project
        for key, value in update.dict(exclude_unset=patch).items():
            setattr(project, key, value)

        # Flush session
        if flush:
            self.session.flush()

    def delete_project(self, project: Project, flush: bool = True) -> None:
        return delete_from_db(self.session, project, flush)


router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectOutput])
def get_projects(projects: Projects = Depends(Projects)) -> list[Project]:
    return projects.list_projects()


@router.post("/projects", status_code=201, response_model=ProjectOutput)
def create_project(
    project: ProjectInput, projects: Projects = Depends(Projects)
) -> Project:
    return projects.create_project(project)


@router.get("/projects/{project_id}", response_model=ProjectOutput)
def get_project(project_id: int, projects: Projects = Depends(Projects)) -> Project:
    return projects.get_project(project_id)


@router.put("/projects/{project_id}", response_model=ProjectOutput)
def update_project(
    project_id: int, project_input: ProjectInput, projects: Projects = Depends(Projects)
) -> Project:
    project = projects.get_project(project_id)
    projects.update_project(project, project_input)
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, projects: Projects = Depends(Projects)) -> None:
    project = projects.get_project(project_id)
    projects.delete_project(project)
