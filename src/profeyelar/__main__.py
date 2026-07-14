"""
Profeyelar (a.k.a. Prof. Eyelar a.k.a Professor Eyelar) is an end-to-end
profiling tool for projects.
"""

import argparse
import json
from os.path import isfile
from tkinter import Tk

from profeyelar.parsing import (ConfigurationParseError,
                                EnvironmentVariableNotFoundError,
                                parse_setting)
from profeyelar.ui import MainFrame


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group("General")

    group.add_argument(
        "configuration_file",
        metavar="configuration-file",
        type=str,
        help="""
        The configuration file with the information that Profeyelar
        requires in order to profile. This must be a valid JSON file
        with the structure described in the README.md
        """,
    )

    options = parser.parse_args()
    return options


def run_professor():
    options = parse_args()
    config_file_path = options.configuration_file
    if not isfile(config_file_path):
        raise ConfigurationParseError(config_file_path)

    try:
        with open(config_file_path, "r") as settings_file:
            json_settings = json.load(settings_file)
        prefixed_settings = {
            f"{prefix}__{key}": parse_setting(value)
            for prefix in json_settings.keys()
            for key, value in json_settings[prefix].items()
        }
    except KeyError as ke:
        raise EnvironmentVariableNotFoundError(config_file_path, str(ke))
    except Exception:
        raise ConfigurationParseError(config_file_path)

    print("👓 Professor Eyelar is coming, please wait a few seconds... 👓")

    root = Tk()
    frame = MainFrame(root, prefixed_settings)
    frame.enter_main_loop()


if __name__ == "__main__":
    run_professor()
