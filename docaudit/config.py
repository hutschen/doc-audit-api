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

from functools import lru_cache
import yaml
from pydantic import BaseModel
from docaudit.utils import to_abs_path


class DatabaseConfig(BaseModel):
    url: str = "sqlite://"
    echo: bool = False


class Config(BaseModel):
    database: DatabaseConfig = DatabaseConfig()


CONFIG_FILENAME = "config.yml"


@lru_cache()
def load_config() -> Config:
    with open(to_abs_path(CONFIG_FILENAME), "r") as config_file:
        config_data = yaml.safe_load(config_file)
    return Config.parse_obj(config_data)
