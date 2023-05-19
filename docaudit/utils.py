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

import os
import re


def to_abs_path(file_path: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(current_dir, "..", file_path)
    return os.path.normpath(abs_path)


def cache_first_result(func):
    cache = []  # Use a list instead of a variable because of Python scoping rules

    def wrapper(*args, **kwargs):
        if not cache:
            result = func(*args, **kwargs)
            cache.append(result)
        return cache[0]

    return wrapper


def remove_extra_whitespace(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()
