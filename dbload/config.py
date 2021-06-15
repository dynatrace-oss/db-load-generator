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

import sys
from pathlib import Path
from typing import Dict, List, Union, Sequence

from loguru import logger
import ilexconf

from .exceptions import SqlFileEmptyError


class Config(ilexconf.Config):
    defaults = ilexconf.Config(
        # Path to the Java installation
        # java_home=os.environ.get("JAVA_HOME", None),
        module=None,
        # Path to the JDBC Type 4 driver jar
        classpath=[],
        # Name of the JDBC driver class (example: com.ibm.db2.jcc.DB2Jcc)
        driver=None,
        dsn=None,
        driver_arg=None,
        # Path to annotated SQL files with queries
        sql=[],
        # Whether to ignore errors during query execution by default
        ignore=False,
        # Limit the printed results of the queries
        limit=50,
        # Log verbosity for the command line interface
        verbose=0,
        # Be quiet, do not print non-error results in CLI
        quiet=False,
        # Name of predefined simmulation for supported DB
        predefined=None,
        # Predefined simulations
        predefined_simulations=["sap-hana"],
        # Schedule for APScheduler
        schedule=None
    )

    def __init__(self, cli_args):

        non_empty_cli_args = {}
        for k in cli_args:
            # Only take non empty CLI arguments
            if cli_args[k]:
                non_empty_cli_args[k] = cli_args[k]

        config_path = Path("dbload.json")
        is_different_config_path = False
        if "config" in non_empty_cli_args:
            config_path_arg = non_empty_cli_args.pop("config")
            config_path = Path(config_path_arg)
            is_different_config_path = True
        cfg = ilexconf.from_json(config_path, ignore_errors=True)

        # Adjust paths in case config file was loaded from a different
        # directory.
        if is_different_config_path:
            config_path_parent = config_path.absolute().parent

            if "classpath" in cfg:
                for i, cp in enumerate(cfg.classpath):
                    cp_instance = Path(cp)
                    if not cp_instance.is_absolute():
                        cfg.classpath[i] = str(
                            config_path_parent / cp_instance
                        )

            if "sql" in cfg:
                for i, s in enumerate(cfg.sql):
                    s_instance = Path(s)
                    if not s_instance.is_absolute():
                        cfg.sql[i] = config_path_parent / s_instance

            if "module" in cfg:
                m_instance = Path(cfg.module)
                if not m_instance.is_absolute():
                    cfg.module = str(config_path_parent / m_instance)

        env = ilexconf.from_env(prefix="DBLOAD_")

        super().__init__(
            self.defaults,
            cfg,
            env,
            non_empty_cli_args,
        )

        # Set verbosity
        max_level = logger.level(name="ERROR").no
        min_level = logger.level(name="DEBUG").no
        level = max(max_level - self.verbose * 10, min_level)
        logger.remove()
        logger.add(sys.stderr, level=level)

        self.sources = self._read_files(self.sql)

        # Parse driver args, if present
        if self.driver_arg and isinstance(self.driver_arg, Sequence):
            driver_args_list = []
            driver_args_dict = {}

            for arg in self.driver_arg:
                if "=" in arg:
                    key, value = arg.split("=")
                    driver_args_dict[key] = value
                else:
                    driver_args_list.append(arg)

            if driver_args_dict:
                self.driver_arg = driver_args_dict
            else:
                self.driver_arg = driver_args_list

    @staticmethod
    def _read_files(sql_files: List[Union[str, Path]]) -> List[str]:
        texts: List[str] = []

        for path in sql_files:
            # Convert to PathLike object if ``path`` is string.
            if isinstance(path, str):
                path = Path(path)

            with path.open("r") as f:
                text = f.read()
                if not text:
                    raise SqlFileEmptyError(path)

                texts.append(text)
        return texts
