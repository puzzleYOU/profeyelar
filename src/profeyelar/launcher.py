import json
import traceback
from contextlib import suppress
from dataclasses import dataclass
from functools import reduce
from http import HTTPStatus
from pathlib import Path
from subprocess import PIPE, CalledProcessError, check_output, run
from time import sleep
from urllib.parse import urljoin
from uuid import uuid4

import requests
from preferences import ProfilingPreferences
from profiling import CProfileContext, TracemallocContext
from ui import MainFrame


def is_service_running(name: str) -> bool:
    cmdline = ["docker", "compose", "ps", name, "--format", "json"]
    if (out := check_output(cmdline).decode()) == "":
        return False
    return json.loads(out)["State"] == "running"


@dataclass(frozen=True, slots=True)
class DockerContainer:
    service_name: str
    container_name: str
    command: str
    command_args: list[str]
    env: dict[str, str]

    def build(self):
        cmdline = ["docker", "compose", "build", self.service_name]
        run(cmdline, stdout=PIPE, stderr=PIPE, check=True)

    def run(self, detached: bool = False):
        envs = reduce(
            lambda interim, pair: [*interim, "--env", f"{pair[0]}={pair[1]}"],
            self.env.items(),
            [],
        )
        maybe_detached = ["-d"] if detached else []
        cmdline = [
            "docker",
            "compose",
            "run",
            *maybe_detached,
            *envs,
            "--name",
            self.container_name,
            self.service_name,
            self.command,
            *self.command_args,
        ]

        try:
            run(cmdline, stdout=PIPE, stderr=PIPE, check=True)
        except CalledProcessError as exc:
            stdout = exc.stdout.decode("utf-8")
            stderr = exc.stderr.decode("utf-8")
            text = f"""
            Starting container failed.
            cmdline: {cmdline}
            stdout: {stdout}
            stderr: {stderr}
            """
            raise RuntimeError(text) from exc

    def stop(self):
        cmdline = ["docker", "container", "stop", self.container_name]
        run(cmdline, stdout=PIPE, stderr=PIPE, check=True)


def start_profiling(
    parsed_settings: dict, prefs: ProfilingPreferences, ui: MainFrame
):
    ui.freeze()
    service_name = parsed_settings["service__name"]
    if is_service_running(service_name):
        ui.notify_err(
            f"Please stop {service_name} first. The Professor takes care"
            " of starting it with the expected environment settings."
        )
        return

    container = _initialize_container(parsed_settings, prefs)
    try:
        ui.set_status_text("Building container...")
        container.build()
        ui.set_status_text("Starting container...")
        container.run(detached=True)
        ui.set_status_text(f"Waiting until {service_name} wakes up...")
        _wait_until_container_is_up(parsed_settings)
        _fire_requests(parsed_settings, prefs, ui)
    except Exception as e:
        traceback.print_exception(e)
        ui.notify_err(f"{e.__class__.__name__}: {e}")
    finally:
        ui.set_status_text("Stopping container...")
        container.stop()
        ui.unfreeze()
        ui.set_status_text("Ready")


def _initialize_container(
    parsed_settings: dict,
    prefs: ProfilingPreferences,
) -> DockerContainer:
    service_name = parsed_settings["service__name"]
    output_path = str(
        Path(parsed_settings["profiling__output_directory"])
        / "memray_output.bin"
    )
    return DockerContainer(
        service_name=service_name,
        container_name=f"{service_name}-{uuid4()}",
        command="serve-with-eyelar",
        command_args=[
            "memray",
            "run",
            "-o",
            output_path,
            "-f",
            "--follow-fork",
            "--native",
            "--trace-python-allocators",
        ],
        env={
            CProfileContext.associated_env: str(prefs.cprofile_enabled),
            TracemallocContext.associated_env: str(prefs.tracemalloc_enabled),
        },
    )


def _wait_until_container_is_up(parsed_settings: dict):
    max_tries = int(parsed_settings.get("profiling__retry_count", 0)) or 30
    tries = 0
    while tries <= max_tries:
        with suppress(Exception):
            resp = requests.get(
                urljoin(
                    parsed_settings["service__base_url"], "/_/kube/readiness/"
                )
            )
            if resp.status_code == HTTPStatus.OK:
                return
        sleep(1)
        tries += 1
    raise RuntimeError("retries exhausted")


def _fire_requests(
    parsed_settings: dict, prefs: ProfilingPreferences, ui: MainFrame
):
    maximum = prefs.repetitions * len(prefs.relative_urls)
    request_headers = prefs.request_headers or None

    i = 1
    for _ in range(prefs.repetitions):
        for url_path in prefs.relative_urls:
            ui.set_status_text(f"Performing request {i}/{maximum}...")
            resp = requests.get(
                urljoin(parsed_settings["service__base_url"], url_path),
                headers=request_headers,
            )
            if resp.status_code != HTTPStatus.OK:
                raise RuntimeError(f"ERROR {resp.status_code}: {resp.content}")
            i += 1
