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

from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from .connection import Base


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    # Relationship to Label and HaystackDocument
    labels = relationship(
        "Label",
        back_populates="document",
        cascade="all, delete, delete-orphan",
        lazy="joined",
    )
    haystack_documents = relationship(
        "HaystackDocument",
        back_populates="document",
        cascade="all, delete, delete-orphan",
        lazy="joined",
    )


class Label(Base):
    __tablename__ = "label"
    document_id = Column(Integer, ForeignKey("document.id"), primary_key=True)
    name = Column(String, primary_key=True)

    # Relationship to Document
    document = relationship("Document", back_populates="labels")


class HaystackDocument(Base):
    __tablename__ = "haystack_document"
    document_id = Column(Integer, ForeignKey("document.id"), primary_key=True)
    hash = Column(String, primary_key=True)

    # Relationship to Document
    document = relationship("Document", back_populates="haystack_documents")
