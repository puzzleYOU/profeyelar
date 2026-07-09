import logging
import os
import tracemalloc
import types
from abc import abstractmethod
from contextlib import AbstractContextManager, contextmanager
from cProfile import Profile
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)


class ProfilerContext(AbstractContextManager):
    associated_env: str
    output_directory: Path
    enabled: bool

    @abstractmethod
    def _start_tracing(self): ...

    @abstractmethod
    def _stop_tracing(self): ...

    @abstractmethod
    def _save_snapshots(self): ...

    def __init__(
        self, session_id: str, output_directory: Path, log: bool = False
    ) -> None:
        super().__init__()
        self.session_id = session_id
        self.enabled = os.environ.get(self.associated_env) == "True"
        self.output_directory = output_directory
        if log:
            logger.info(f"→ {self.associated_env}: {self.enabled}")

    def __enter__(self) -> None:
        if self.enabled:
            self._start_tracing()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> bool | None:
        if self.enabled:
            self._stop_tracing()
            self._save_snapshots()


class CProfileContext(ProfilerContext):
    associated_env = "EYELAR_DEBUG_WITH_CPROFILE"

    def __init__(
        self, session_id: str, output_directory: Path, log: bool = False
    ):
        super().__init__(
            session_id=session_id, output_directory=output_directory, log=log
        )
        self.profile = Profile()

    def _start_tracing(self):
        self.profile.enable()

    def _stop_tracing(self):
        # Profile.dump_stats() also calls Profile.disable()
        pass

    def _save_snapshots(self):
        self.profile.dump_stats(
            str(self.output_directory / f"{self.session_id}.cprofile")
        )


class TracemallocContext(ProfilerContext):
    associated_env = "EYELAR_DEBUG_WITH_TRACEMALLOC"

    def __init__(
        self, session_id: str, output_directory: Path, log: bool = False
    ):
        super().__init__(
            session_id=session_id, output_directory=output_directory, log=log
        )

    def _start_tracing(self):
        tracemalloc.start()
        self.snapshot_start = tracemalloc.take_snapshot()

    def _stop_tracing(self):
        self.snapshot_end = tracemalloc.take_snapshot()
        tracemalloc.stop()

    def _save_snapshots(self):
        self.snapshot_start.dump(
            str(self.output_directory / f"{self.session_id}.0.tracemalloc")
        )
        self.snapshot_end.dump(
            str(self.output_directory / f"{self.session_id}.1.tracemalloc")
        )


@contextmanager
def profiling_session_if_enabled(output_directory: Path):
    session_id = str(uuid4())
    logger.info(f"profiling session ID: {session_id}")
    with (
        CProfileContext(session_id, output_directory, log=True),
        TracemallocContext(session_id, output_directory, log=True),
    ):
        yield
