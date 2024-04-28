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

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .angular import AngularFiles
from .config import get_config
from .endpoints import query, sources
from .ml.pipelines import get_indexing_pipeline, get_querying_pipeline
from .utils import to_abs_path


def get_app(lifespan=None) -> FastAPI:
    config = get_config().fastapi
    app = FastAPI(
        title="DocAudit API",
        docs_url=config.docs_url,
        redoc_url=config.redoc_url,
        lifespan=lifespan,
    )

    app.include_router(sources.router, prefix="/api")
    app.include_router(query.router, prefix="/api")
    app.mount("/", AngularFiles(directory=to_abs_path("htdocs"), html=True))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup logic
    # Warm up pipelines that use an embedder to speed up the first request
    get_indexing_pipeline()
    get_querying_pipeline()
    yield
    # Shutdown logic


app = get_app(lifespan)


def serve():
    config = get_config().uvicorn
    uvicorn.run(
        "docaudit:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.log_level,
        log_config=config.log_config,
        ssl_keyfile=config.ssl_keyfile,
        ssl_certfile=config.ssl_certfile,
        ssl_keyfile_password=config.ssl_keyfile_password,
        ssl_version=config.ssl_version,
        ssl_cert_reqs=config.ssl_cert_reqs,
        ssl_ca_certs=config.ssl_ca_certs,
        ssl_ciphers=config.ssl_ciphers,
    )
