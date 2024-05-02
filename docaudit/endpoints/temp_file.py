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

import shutil
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper

from fastapi import UploadFile


def copy_upload_to_temp_file(upload_file: UploadFile) -> _TemporaryFileWrapper:
    """Copies the contents of an upload file to a temporary file.

    Please note that the temporary file is not automatically deleted and must be deleted
    manually.

    Args:
        upload_file (UploadFile): The upload file to copy.

    Returns:
        NamedTemporaryFile: The temporary file.
    """
    temp_file = NamedTemporaryFile(delete=False)
    shutil.copyfileobj(upload_file.file, temp_file.file)
    temp_file.file.seek(0)  # Reset cursor after copying
    return temp_file


def copy_uploads_to_temp_files(
    upload_files: list[UploadFile],
) -> list[_TemporaryFileWrapper]:
    """Copies uploaded files to temporary files.

    Please note that the temporary files are not automatically deleted and must be
    deleted manually.

    Args:
        upload_files (list[UploadFile]): The upload files to copy.

    Returns:
        list[_NamedTemporaryFile]: A generator of temporary files.
    """
    return [copy_upload_to_temp_file(upload_file) for upload_file in upload_files]
