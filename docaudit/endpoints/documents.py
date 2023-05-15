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

from ..db.documents import DocumentManager
from ..db.projects import ProjectManager
from ..db.schemas import Document
from .models import DocumentInput, DocumentOutput

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentOutput])
def get_documents(
    document_manager: DocumentManager = Depends(DocumentManager),
    # TODO: Add option to filter by project_id
) -> list[Document]:
    return document_manager.list_documents()


@router.post(
    "/projects/{project_id}/documents", status_code=201, response_model=DocumentOutput
)
def create_document(
    project_id: int,
    document: DocumentInput,
    project_manager: ProjectManager = Depends(ProjectManager),
    document_manager: DocumentManager = Depends(DocumentManager),
) -> Document:
    project = project_manager.get_project(project_id)
    return document_manager.create_document(project, document)


@router.get("/documents/{document_id}", response_model=DocumentOutput)
def get_document(
    document_id: int, document_manager: DocumentManager = Depends(DocumentManager)
) -> Document:
    return document_manager.get_document(document_id)


@router.put("/documents/{document_id}", response_model=DocumentOutput)
def update_document(
    document_id: int,
    document_input: DocumentInput,
    document_manager: DocumentManager = Depends(DocumentManager),
) -> Document:
    document = document_manager.get_document(document_id)
    document_manager.update_document(document, document_input)
    return document


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int, document_manager: DocumentManager = Depends(DocumentManager)
) -> None:
    document = document_manager.get_document(document_id)
    document_manager.delete_document(document)
