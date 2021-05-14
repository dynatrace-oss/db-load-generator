# Copyright 2020-2021 Dynatrace LLC
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

from typing import Dict, Optional

from .config import Config


global_config: Optional[Config] = None


def get_config(cli_args: Dict = {}) -> Config:
    """Get global config instance.

    If global instance does not exist, creates it and returns it.
    """

    global global_config

    if global_config is None:
        global_config = Config(cli_args)

    return global_config
