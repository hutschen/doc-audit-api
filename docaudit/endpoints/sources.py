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

from functools import lru_cache
import os
import threading
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from ..ml.components import new_source_id
from ..ml.pipelines import is_indexed, run_indexing_pipeline
from .temp_file import copy_upload_to_temp_file

router = APIRouter(tags=["sources"])
qdrant_lock = threading.Lock()


class SourceStatus(BaseModel):
    id: str
    status: str


class SourceStatusBroker:
    """
    Thread-safe broker for managing the indexing status of uploaded sources.
    """

    WAITING = "waiting"
    ABORTED = "aborted"
    INDEXING = "indexing"
    INDEXED = "indexed"
    NOT_FOUND = "not found"

    def __init__(self):
        self.source_id_to_status_lock = threading.Lock()
        self.source_id_to_status: dict[str, str] = {}

    def get_status(self, source_id: str) -> str:
        with self.source_id_to_status_lock:
            status = self.source_id_to_status.get(source_id, None)
        if status is None:
            status = self.INDEXED if is_indexed(source_id) else self.NOT_FOUND
        return status

    def is_(self, source_id: str, status: str) -> bool:
        return self.get_status(source_id) == status

    def set_waiting(self, source_id: str):
        with self.source_id_to_status_lock:
            self.source_id_to_status[source_id] = self.WAITING

    def set_aborted(self, source_id: str):
        with self.source_id_to_status_lock:
            if self.source_id_to_status.get(source_id, None) != self.WAITING:
                return
            self.source_id_to_status[source_id] = self.ABORTED

    def set_indexing(self, source_id: str):
        with self.source_id_to_status_lock:
            if self.source_id_to_status.get(source_id, None) != self.WAITING:
                return
            self.source_id_to_status[source_id] = self.INDEXING

    def set_completed(self, source_id: str):
        with self.source_id_to_status_lock:
            try:
                del self.source_id_to_status[source_id]
            except KeyError:
                pass


@lru_cache
def get_source_status_broker() -> SourceStatusBroker:
    return SourceStatusBroker()


@router.post("/sources", status_code=201, response_model=SourceStatus)
def index_source(
    background_tasks: BackgroundTasks,
    temp_file: Any = Depends(copy_upload_to_temp_file),
    source_id: str = Depends(new_source_id),
    source_status_broker: SourceStatusBroker = Depends(get_source_status_broker),
):

    def index_in_background():
        qdrant_lock.acquire()
        try:
            if source_status_broker.is_(source_id, source_status_broker.ABORTED):
                return

            source_status_broker.set_indexing(source_id)
            run_indexing_pipeline(sources=[temp_file.name], source_ids=[source_id])

        finally:
            source_status_broker.set_completed(source_id)
            qdrant_lock.release()
            os.remove(temp_file.name)

    background_tasks.add_task(index_in_background)
    return SourceStatus(id=source_id, status="indexing")
