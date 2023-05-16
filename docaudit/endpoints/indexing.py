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


from typing import Any, Literal

from fastapi import APIRouter, Depends

from ..db.documents import DocumentManager
from ..db.haystack_hashes import HaystackHashManager
from ..errors import ClientError
from ..ml.indexing import faiss_document_store_writer, index_docx
from .models import DocumentOutput
from .temp_file import copy_upload_to_temp_file

router = APIRouter(tags=["indexing"])


@router.post(
    "/documents/{document_id}/index", status_code=201, response_model=DocumentOutput
)
def upload_and_index_docx(
    document_id: int,
    language: Literal["de", "en"],
    temp_file: Any = Depends(copy_upload_to_temp_file),
    document_manager: DocumentManager = Depends(),
):
    document = document_manager.get_document(document_id)
    if document.haystack_hashes:
        raise ClientError("There is already an index for this document.")

    haystack_documents = index_docx([temp_file.name], language)
    document.haystack_hashes = [d.id for d in haystack_documents]
    document_manager.session.flush()
    return document


@router.put(
    "/documents/{document_id}/index", status_code=200, response_model=DocumentOutput
)
def unindex(
    document_id: int,
    document_manager: DocumentManager = Depends(),
    haystack_hash_manager: HaystackHashManager = Depends(),
):
    document = document_manager.get_document(document_id)
    single_linked_hashes = haystack_hash_manager.get_single_linked_hashes(document_id)
    faiss_document_store_writer.delete_documents(single_linked_hashes)

    document.haystack_hashes = []
    document_manager.session.flush()
    return document
