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

from typing import Optional
import jpype
from jpype import dbapi2
from loguru import logger

from .config import Config
from .config_singleton import get_config
from .exceptions import DsnNotFoundError


def get_connection(
    config: Optional[Config] = None,
) -> dbapi2.Connection:

    if not config:
        config = get_config()

    if not config.dsn:
        raise DsnNotFoundError()

    if not jpype.isJVMStarted():
        logger.debug("Starting JVM process.")
        jpype.startJVM(classpath=config.classpath)
        logger.debug("Successfully started JVM process.")

    connect_kwargs = {}
    if config.driver:
        connect_kwargs["driver"] = config.driver
    if config.driver_arg:
        connect_kwargs["driver_args"] = config.driver_arg

    logger.debug(f"Connection to the database at '{config.dsn}'.")
    connection = jpype.dbapi2.connect(config.dsn, **connect_kwargs)
    logger.debug(f"Successfully connected to the database.")

    return connection
