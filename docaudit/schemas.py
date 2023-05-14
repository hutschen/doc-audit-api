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
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association table for the many-to-many relationship between Project and Document
project_document_table = Table(
    "project_document",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("project.id")),
    Column("document_id", Integer, ForeignKey("document.id")),
)

# Association table for the many-to-many relationship between Document and HaystackDocument
document_haystackdocument_table = Table(
    "document_haystackdocument",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("document.id")),
    Column("haystack_document_id", String, ForeignKey("haystack_document.hash_id")),
)


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    # Relationship to Document
    documents = relationship(
        "Document",
        secondary=project_document_table,
        back_populates="projects",
    )


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    version = Column(String)
    author = Column(String)

    # Relationship to Project
    projects = relationship(
        "Project",
        secondary=project_document_table,
        back_populates="documents",
        # Cascade option to delete orphaned Document instances
        cascade="all, delete-orphan",
    )

    # Relationship to HaystackDocument
    haystack_documents = relationship(
        "HaystackDocument",
        secondary=document_haystackdocument_table,
        back_populates="documents",
    )


class HaystackDocument(Base):
    __tablename__ = "haystack_document"
    hash_id = Column(String, primary_key=True)

    # Relationship to Document
    documents = relationship(
        "Document",
        secondary=document_haystackdocument_table,
        back_populates="haystack_documents",
        # Cascade option to delete orphaned HaystackDocument instances
        cascade="all, delete-orphan",
    )
