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

from typing import Literal
from pydantic import BaseModel


class LabelInput(BaseModel):
    name: str


class LabelOutput(LabelInput):
    class Config:
        orm_mode = True


class DocumentInput(BaseModel):
    title: str
    labels: list[LabelInput] = []
    language: Literal["de", "en"] = "de"


class DocumentOutput(DocumentInput):
    class Config:
        orm_mode = True

    id: int
    labels: LabelOutput
