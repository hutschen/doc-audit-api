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

# Using a Debian-based lightweight base image
FROM python:3.12-slim

# Set working directory
WORKDIR /workspace

# Install dependencies including build-essential to compile Python C extensions
COPY ./Pipfile ./Pipfile.lock ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        make \
        git \
        git-lfs \
        zsh \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --upgrade pip \
    && pip3 install pipenv \
    && pipenv install --ignore-pipfile --dev

# Install Oh-My-Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended