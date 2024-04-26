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
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel

from ..ml.components import new_source_id
from ..ml.pipelines import (
    are_indexed,
    is_indexed,
    run_deindexing_pipeline,
    run_indexing_pipeline,
)
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

    def get_statusses(self, source_ids: list[str]) -> dict[str, str]:
        with self.source_id_to_status_lock:
            statusses = {
                source_id: self.source_id_to_status.get(source_id, None)
                for source_id in source_ids
            }
        missing_source_ids = [
            source_id for source_id, status in statusses.items() if status is None
        ]
        for source_id, is_indexed in are_indexed(missing_source_ids).items():
            statusses[source_id] = self.INDEXED if is_indexed else self.NOT_FOUND
        return statusses

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


@router.get("/sources/{source_id}", response_model=SourceStatus)
def get_source_status(
    source_id: str,
    source_status_broker: SourceStatusBroker = Depends(get_source_status_broker),
):
    return SourceStatus(id=source_id, status=source_status_broker.get_status(source_id))


@router.get("/sources", response_model=list[SourceStatus])
def get_source_statusses(
    source_ids: list[str] = Query(...),
    source_status_broker: SourceStatusBroker = Depends(get_source_status_broker),
):
    return (
        SourceStatus(id=source_id, status=status)
        for source_id, status in source_status_broker.get_statusses(source_ids).items()
    )


@router.delete("/sources/{source_id}", status_code=204)
def deindex_source(
    background_tasks: BackgroundTasks,
    source_id: str,
    source_status_broker: SourceStatusBroker = Depends(get_source_status_broker),
) -> None:
    return deindex_sources(
        background_tasks=background_tasks,
        source_ids=[source_id],
        source_status_broker=source_status_broker,
    )


@router.delete("/sources", status_code=204)
def deindex_sources(
    background_tasks: BackgroundTasks,
    source_ids: list[str] = Query(...),
    source_status_broker: SourceStatusBroker = Depends(get_source_status_broker),
) -> None:
    def deindex_in_background(source_ids: list[str]):
        qdrant_lock.acquire()
        try:
            run_deindexing_pipeline(source_ids=source_ids)
        finally:
            qdrant_lock.release()

    ids_to_deindex = set()
    for source_id, status in source_status_broker.get_statusses(source_ids).items():
        if status == source_status_broker.INDEXED:
            ids_to_deindex.add(source_id)
        elif status == source_status_broker.WAITING:
            source_status_broker.set_aborted(source_id)

    background_tasks.add_task(deindex_in_background, list(ids_to_deindex))
