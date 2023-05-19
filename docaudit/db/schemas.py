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


class Group(Base):
    __tablename__ = "group"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    # Relationship to Document
    documents = relationship("Document", back_populates="group", cascade="all,delete")


class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    language = Column(String, default="de", nullable=False)

    # Relationship to Group
    group_id = Column(Integer, ForeignKey("group.id"))
    group = relationship("Group", back_populates="documents")
