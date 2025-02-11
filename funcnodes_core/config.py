from typing import Optional, TypedDict
from pathlib import Path
import os
import json
from .utils.data import deep_fill_dict
from .utils.plugins_types import RenderOptions
from .utils.files import write_json_secure
from dotenv import load_dotenv
from exposedfunctionality.function_parser.types import type_to_string
import tempfile
import shutil
import sys

load_dotenv(override=True)


BASE_CONFIG_DIR = Path(
    os.environ.get("FUNCNODES_CONFIG_DIR", Path.home() / ".funcnodes")
)


class WorkerManagerConfig(TypedDict, total=False):
    host: str
    port: int


class FrontendConfig(TypedDict, total=False):
    port: int
    host: str


class ConfigType(TypedDict, total=False):
    env_dir: str
    worker_manager: WorkerManagerConfig
    frontend: FrontendConfig


DEFAULT_CONFIG: ConfigType = {
    "env_dir": (BASE_CONFIG_DIR / "env").as_posix(),
    "worker_manager": {
        "host": "localhost",
        "port": 9380,
    },
    "frontend": {
        "port": 8000,
        "host": "localhost",
    },
}


CONFIG = DEFAULT_CONFIG
CONFIG_DIR = BASE_CONFIG_DIR


def _bupath(path: Path) -> Path:
    """
    Returns the backup path for the configuration file.

    Args:
        path (str): The path to the configuration file.

    Returns:
        str: The backup path.

    Examples:
        >>> _bupath("config.json")
        >>> "config.json.bu"
    """

    return path.with_suffix(path.suffix + ".bu")


def write_config(path: Path, config: ConfigType):
    """
    Writes the configuration file.

    Args:
      path (str): The path to the configuration file.
      config (dict): The configuration to write.

    Returns:
      None

    Examples:
      >>> write_config("config.json", {"env_dir": "env"})
    """
    path = Path(path)
    write_json_secure(config, path, indent=2)
    write_json_secure(config, _bupath(path), indent=2)


def load_config(path: Path):
    """
    Loads the configuration file.

    Args:
      path (str): The path to the configuration file.

    Returns:
      None

    Examples:
      >>> load_config("config.json")
    """
    global CONFIG
    config: Optional[ConfigType] = None
    path = Path(path)
    try:
        with open(path, "r") as f:
            config = json.load(f)
    except Exception:
        pass

    if config is None:
        try:
            with open(_bupath(path), "r") as f:
                config = json.load(f)
        except Exception:
            pass

    if config is None:
        config = DEFAULT_CONFIG

    deep_fill_dict(config, DEFAULT_CONFIG, inplace=True)
    write_config(path, config)
    CONFIG = config


def check_config_dir():
    """
    Checks the configuration directory.

    Returns:
      None

    Examples:
      >>> check_config_dir()
    """
    global CONFIG_DIR
    if not BASE_CONFIG_DIR.exists():
        BASE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    load_config(BASE_CONFIG_DIR / "config.json")
    if "custom_config_dir" in CONFIG:
        load_config(Path(CONFIG["custom_config_dir"]) / "config.json")
        CONFIG_DIR = CONFIG["custom_config_dir"]
    else:
        CONFIG_DIR = BASE_CONFIG_DIR


check_config_dir()


FUNCNODES_RENDER_OPTIONS: RenderOptions = {"typemap": {}, "inputconverter": {}}


def update_render_options(options: RenderOptions):
    """
    Updates the render options.

    Args:
      options (RenderOptions): The render options to update.

    Returns:
      None

    Examples:
      >>> update_render_options({"typemap": {"int": "int32"}, "inputconverter": {"str": "string"}})
    """
    if not isinstance(options, dict):
        return
    if "typemap" not in options:
        options["typemap"] = {}
    for k, v in list(options["typemap"].items()):
        if not isinstance(k, str):
            del options["typemap"][k]
            k = type_to_string(k)
            options["typemap"][k] = v

        if not isinstance(v, str):
            v = type_to_string(v)
            options["typemap"][k] = v

    if "inputconverter" not in options:
        options["inputconverter"] = {}
    for k, v in list(options["inputconverter"].items()):
        if not isinstance(k, str):
            del options["typemap"][k]
            k = type_to_string(k)
            options["inputconverter"][k] = v
        if not isinstance(v, str):
            v = type_to_string(v)
            options["inputconverter"][k] = v
        FUNCNODES_RENDER_OPTIONS["inputconverter"][k] = v

    # make sure its json serializable
    try:
        json.dumps(options)
    except json.JSONDecodeError:
        return
    deep_fill_dict(
        FUNCNODES_RENDER_OPTIONS, options, merge_lists=True, unfify_lists=True
    )


def reload(funcnodes_config_dir: Optional[Path] = None):
    global CONFIG, BASE_CONFIG_DIR, CONFIG_DIR
    load_dotenv(override=True)

    if funcnodes_config_dir is not None:
        os.environ["FUNCNODES_CONFIG_DIR"] = str(Path(funcnodes_config_dir))

    BASE_CONFIG_DIR = Path(
        os.environ.get("FUNCNODES_CONFIG_DIR", Path.home() / ".funcnodes")
    )
    CONFIG = DEFAULT_CONFIG
    CONFIG_DIR = BASE_CONFIG_DIR
    check_config_dir()


reload()

IN_NODE_TEST = False


class This(sys.__class__):  # sys.__class__ is <class 'module'>
    _IN_NODE_TEST = IN_NODE_TEST

    @property
    def IN_NODE_TEST(self):  # do the property things in this class
        return self._IN_NODE_TEST

    @IN_NODE_TEST.setter
    def IN_NODE_TEST(self, value):  # setter is also OK
        value = bool(value)
        # if value is the same as the current value, do nothing
        if value == self._IN_NODE_TEST:
            return
        if value:
            set_in_test()
        self._IN_NODE_TEST = value


del IN_NODE_TEST

sys.modules[__name__].__class__ = This  # set the __class__ of the module to This


def set_in_test(
    clear: bool = True, add_pid: bool = True, config: Optional[ConfigType] = None
):
    """
    Sets the configuration to be in test mode.

    Returns:
      None

    Examples:
      >>> set_in_test()
    """
    global BASE_CONFIG_DIR
    sys.modules[__name__]._IN_NODE_TEST = True

    fn = "funcnodes_test"
    if add_pid:
        fn += f"_{os.getpid()}"

    BASE_CONFIG_DIR = Path(tempfile.gettempdir()) / fn
    if clear:
        if BASE_CONFIG_DIR.exists():
            try:
                shutil.rmtree(BASE_CONFIG_DIR)
            except Exception:
                pass
    if config:
        write_config(BASE_CONFIG_DIR / "config.json", config)
    check_config_dir()

    # import here to avoid circular import

    from ._logging import set_logging_dir  # noqa C0415 # pylint: disable=import-outside-toplevel

    set_logging_dir(os.path.join(BASE_CONFIG_DIR, "logs"))


sys.modules[__name__].IN_NODE_TEST = bool(os.environ.get("IN_NODE_TEST", False))
