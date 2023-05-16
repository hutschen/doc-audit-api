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


from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .connection import get_session
from .schemas import Document, HaystackHash


class HaystackHashManager:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.session = session

    def get_single_linked_hashes(self, document_id: int) -> list[str]:
        # Subquery to find hashes linked to multiple documents
        multiple_linked_hashes_subquery = (
            select(HaystackHash.hash)
            .join(Document)
            .group_by(HaystackHash.hash)
            .having(func.count(Document.id) > 1)
        )

        # Query to find hashes linked to the specified document
        single_linked_hashes_query = (
            select(HaystackHash.hash)
            .join(Document)
            .filter(Document.id == document_id)
            # Exclude hashes that are linked to multiple documents
            .filter(HaystackHash.hash.notin_(multiple_linked_hashes_subquery))
        )

        # Execute the query and return the result
        return [row[0] for row in self.session.execute(single_linked_hashes_query)]
