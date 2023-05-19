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

from typing import Any, Literal, cast
from fastapi import APIRouter, Depends
from docaudit.db.groups import GroupManager

from ..endpoints.temp_file import copy_upload_to_temp_file
from ..ml.indexing import IndexingManager

from ..db.documents import DocumentManager, get_document_filters
from ..db.schemas import Document
from .models import DocumentInput, DocumentOutput

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentOutput])
def get_documents(
    document_manager: DocumentManager = Depends(DocumentManager),
    where_clauses: list[Any] = Depends(get_document_filters),
) -> list[Document]:
    return document_manager.list_documents(where_clauses)


@router.post(
    "groups/{group_id}/documents", status_code=201, response_model=DocumentOutput
)
def create_document(
    group_id: int,
    title: str,
    language: Literal["de", "en"] = "de",
    temp_file: Any = Depends(copy_upload_to_temp_file),
    group_manager: GroupManager = Depends(),
    document_manager: DocumentManager = Depends(),
    indexing_manager: IndexingManager = Depends(),
) -> Document:
    document = document_manager.create_document(
        group_manager.get_group(group_id),
        DocumentInput(title=title, language=language),
    )
    indexing_manager.index_docx_file(
        temp_file.name,
        str(group_id),
        language,
        file_id=cast(int, document.id),
    )
    return document


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
    faiss_document_store_writer.delete_documents(document.id)  # type: ignore
    document_manager.delete_document(document)
