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
import ssl
from pydantic import BaseModel
from uvicorn.config import LOGGING_CONFIG, SSL_PROTOCOL_VERSION
from .utils import to_abs_path


class DatabaseConfig(BaseModel):
    url: str = "sqlite://"
    echo: bool = False


class FastApiConfig(BaseModel):
    docs_url: str | None = None  # "/docs"
    redoc_url: str | None = None  # "/redoc"


class UvicornConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "error"
    log_filename: str | None = None
    ssl_keyfile: str | None = None
    ssl_certfile: str | None = None
    ssl_keyfile_password: str | None = None
    ssl_version: int = SSL_PROTOCOL_VERSION
    ssl_cert_reqs: int = ssl.CERT_NONE
    ssl_ca_certs: str | None = None
    ssl_ciphers: str = "TLSv1"

    @property
    def log_config(self) -> dict:
        if not self.log_filename:
            return LOGGING_CONFIG

        custom_logging_config = LOGGING_CONFIG.copy()
        custom_logging_config["formatters"]["default"]["use_colors"] = False
        custom_logging_config["formatters"]["access"]["use_colors"] = False
        custom_logging_config["handlers"] = {
            "default": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": self.log_filename,
                "mode": "a",
                "encoding": "utf-8",
            },
            "access": {
                "class": "logging.FileHandler",
                "formatter": "access",
                "filename": self.log_filename,
                "mode": "a",
                "encoding": "utf-8",
            },
        }
        return custom_logging_config


class Config(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    fastapi: FastApiConfig = FastApiConfig()
    uvicorn: UvicornConfig = UvicornConfig()


CONFIG_FILENAME = "config.yml"


@lru_cache()
def load_config() -> Config:
    with open(to_abs_path(CONFIG_FILENAME), "r") as config_file:
        config_data = yaml.safe_load(config_file)
    return Config.parse_obj(config_data)
