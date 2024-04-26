# Copyright (C) 2024 Helmar Hutschenreuter
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import threading
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from ..ml.components import new_source_id
from ..ml.pipelines import run_indexing_pipeline
from .temp_file import copy_upload_to_temp_file

router = APIRouter(tags=["sources"])
qdrant_lock = threading.Lock()


class SourceStatus(BaseModel):
    id: str
    status: str


@router.post("/sources", status_code=201, response_model=SourceStatus)
def index_source(
    background_tasks: BackgroundTasks,
    temp_file: Any = Depends(copy_upload_to_temp_file),
    source_id: str = Depends(new_source_id),
):

    def index_in_background():
        qdrant_lock.acquire()
        try:
            run_indexing_pipeline(sources=[temp_file.name], source_ids=[source_id])
        finally:
            qdrant_lock.release()
            os.remove(temp_file.name)

    background_tasks.add_task(index_in_background)
    return SourceStatus(id=source_id, status="indexing")
