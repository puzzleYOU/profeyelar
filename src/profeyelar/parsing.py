import os
import re


class ConfigurationParseError(Exception):
    def __init__(self, settings_file: str):
        super().__init__(
            "[ERROR] Profeyelar could not extract the required settings"
            f" from configuration file {settings_file}. Ensure that the"
            " .json File exists, is properly formatted and contains all"
            " required settings."
        )


class EnvironmentVariableNotFoundError(Exception):
    def __init__(self, settings_file: str, variable: str):
        super().__init__(
            "[ERROR] Profeyelar failed to parse the configuration"
            f" file {settings_file} due to the undefined"
            f" environment variable {variable}!"
        )


CONFIGURATION_FILE_ENV_REGEX = re.compile(r"\$ENV\{[a-zA-Z0-9_\-]+\}")


def parse_setting(value: object):
    if type(value) is str:
        env_matches = re.findall(CONFIGURATION_FILE_ENV_REGEX, value)
        for match in env_matches:
            value = value.replace(match, get_parsed_env_variable(match))
    return value


def get_parsed_env_variable(text: str) -> str:
    return os.environ[text.removeprefix("$ENV{").removesuffix("}")]
