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

from ..db.projects import ProjectManager
from ..db.schemas import Project
from .models import ProjectInput, ProjectOutput

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectOutput])
def get_projects(
    project_manager: ProjectManager = Depends(ProjectManager),
) -> list[Project]:
    return project_manager.list_projects()


@router.post("/projects", status_code=201, response_model=ProjectOutput)
def create_project(
    project: ProjectInput, project_manager: ProjectManager = Depends(ProjectManager)
) -> Project:
    return project_manager.create_project(project)


@router.get("/projects/{project_id}", response_model=ProjectOutput)
def get_project(
    project_id: int, project_manager: ProjectManager = Depends(ProjectManager)
) -> Project:
    return project_manager.get_project(project_id)


@router.put("/projects/{project_id}", response_model=ProjectOutput)
def update_project(
    project_id: int,
    project_input: ProjectInput,
    project_manager: ProjectManager = Depends(ProjectManager),
) -> Project:
    project = project_manager.get_project(project_id)
    project_manager.update_project(project, project_input)
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: int, project_manager: ProjectManager = Depends(ProjectManager)
) -> None:
    project = project_manager.get_project(project_id)
    project_manager.delete_project(project)
