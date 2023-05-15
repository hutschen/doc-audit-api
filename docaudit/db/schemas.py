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

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .connection import Base


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    language = Column(String, default="de", nullable=False)

    # Relationship to Label and HaystackDocument
    _labels = relationship(
        "Label", back_populates="document", cascade="all, delete, delete-orphan"
    )
    _haystack_hashes = relationship(
        "HaystackHash", back_populates="document", cascade="all, delete, delete-orphan"
    )

    @property
    def labels(self) -> list[str]:
        return [label.name for label in self._labels]  # type: ignore

    @labels.setter
    def labels(self, labels: list[str]):
        existing_labels = {l.name: l for l in self._labels}
        self._labels = [
            existing_labels.get(label, Label(name=label)) for label in labels
        ]

    @property
    def haystack_hashes(self) -> list[str]:
        return [hd.hash for hd in self._haystack_hashes]

    @haystack_hashes.setter
    def haystack_hashes(self, hashes: list[str]):
        existing_hashes = {hd.hash: hd for hd in self._haystack_hashes}
        self._haystack_hashes = [
            existing_hashes.get(hash, HaystackHash(hash=hash)) for hash in hashes
        ]


class Label(Base):
    __tablename__ = "label"
    document_id = Column(Integer, ForeignKey("document.id"), primary_key=True)
    name = Column(String, primary_key=True)

    # Relationship to Document
    document = relationship("Document", back_populates="_labels")


class HaystackHash(Base):
    __tablename__ = "haystack_hash"
    document_id = Column(Integer, ForeignKey("document.id"), primary_key=True)
    hash = Column(String, primary_key=True)

    # Relationship to Document
    document = relationship("Document", back_populates="_haystack_hashes")
