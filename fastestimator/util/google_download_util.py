# Copyright 2022 The FastEstimator Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
import random
import time
from typing import TypeVar

import requests
import wget
from tqdm import tqdm

from fastestimator.util.util import validate_file
from fastestimator.util.wget_util import callback_progress

wget.callback_progress = callback_progress
Response = TypeVar('Response', bound=requests.models.Response)


def _get_confirm_token(response: Response) -> str:
    """Retrieve the token from the cookie jar of HTTP request to keep the session alive.
    Args:
        response: Response object of the HTTP request.
    Returns:
        The value of cookie in the response object.
    """
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def _download_file_from_google_drive(file_id: str, destination: str) -> None:
    """Download the data from the Google drive public URL.

    This method will create a session instance to persist the requests and reuse TCP connection for the large files.

    Args:
        file_id: File ID of Google drive URL.
        destination: Destination path where the data needs to be stored.
    """
    URL = "https://drive.google.com/uc?export=download&confirm=t"
    CHUNK_SIZE = 128
    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)
    token = _get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    total_size = int(response.headers.get('Content-Length', 0))
    progress = tqdm(total=total_size, unit='B', unit_scale=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                progress.update(len(chunk))
                f.write(chunk)
    progress.close()


def download_file_from_google_drive(file_id: str, destination: str, max_retries: int = 3) -> None:
    """Download the data from the Google drive public URL.

    This method will try to download the file for given number of retries till successful.

    Args:
        file_id: File ID of Google drive URL.
        destination: Destination path where the data needs to be stored.
        max_retries: max number of retries.
    """
    found = False
    for _ in range(max_retries):
        try:
            _download_file_from_google_drive(file_id, destination)
            if validate_file(destination):
                print(f"Successfully download the file to {destination}.")
                found = True
                break
            else:
                print(f"The {file_id} was not downloaded completely, will be trying in around 5 seconds.")
                time.sleep(random.randint(5, 10))
        except Exception as e:
            print(f"Exception occurred while downloading the {file_id}, will be trying in around 5 seconds.", e)
            time.sleep(random.randint(5, 10))

    if not found:
        raise ValueError(f"Couldn't download {file_id} after {max_retries} retries.")
