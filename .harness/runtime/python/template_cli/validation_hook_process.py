from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HOOK_DESCENDANT_LIMIT = 256
HOOK_CLEANUP_SECONDS = 2.0
_PR_SET_CHILD_SUBREAPER = 36
_PR_GET_CHILD_SUBREAPER = 37


@dataclass(frozen=True)
class _ProcessIdentity:
    pid: int
    start_time: int


@dataclass(frozen=True)
class _ProcessInfo:
    identity: _ProcessIdentity
    parent_pid: int
    state: str


class LinuxProcessContainment:
    def __init__(self, previous_subreaper: int, baseline_children: set[_ProcessIdentity]) -> None:
        self._previous_subreaper = previous_subreaper
        self._baseline_children = baseline_children
        self._self_pid = os.getpid()
        self._root: _ProcessIdentity | None = None
        self._known: dict[int, _ProcessIdentity] = {}

    @classmethod
    def establish(cls) -> LinuxProcessContainment:
        if sys.platform != "linux" or not Path("/proc/self/task").is_dir():
            raise OSError("strong descendant containment is supported only on Linux with /proc")
        previous = _get_child_subreaper()
        if previous != 1:
            _set_child_subreaper(1)
        try:
            baseline = _direct_children(os.getpid())
        except OSError:
            if previous != 1:
                _set_child_subreaper(previous)
            raise
        return cls(previous, baseline)

    def attach(self, pid: int) -> None:
        info = _process_info(pid)
        if info is None:
            raise OSError("hook process disappeared before containment attached")
        self._root = info.identity
        self._known[pid] = info.identity

    def observe(self) -> list[_ProcessInfo]:
        if self._root is None:
            return []
        discovered: dict[int, _ProcessInfo] = {}
        queue: list[_ProcessIdentity] = []

        root_info = _matching_process(self._root)
        if root_info is not None:
            discovered[root_info.identity.pid] = root_info
            queue.append(root_info.identity)

        for identity in _direct_children(self._self_pid):
            if identity in self._baseline_children or identity == self._root:
                continue
            info = _matching_process(identity)
            if info is not None:
                discovered[identity.pid] = info
                queue.append(identity)

        for identity in self._known.values():
            info = _matching_process(identity)
            if info is not None and identity.pid not in discovered:
                discovered[identity.pid] = info
                queue.append(identity)

        visited: set[_ProcessIdentity] = set()
        while queue:
            identity = queue.pop()
            if identity in visited:
                continue
            visited.add(identity)
            for child_identity in _direct_children(identity.pid):
                child_info = _matching_process(child_identity)
                if child_info is None:
                    continue
                if child_identity.pid not in discovered:
                    discovered[child_identity.pid] = child_info
                    queue.append(child_identity)
                if _descendant_count(discovered, self._root) > HOOK_DESCENDANT_LIMIT:
                    self._known.update({pid: info.identity for pid, info in discovered.items()})
                    raise RuntimeError(f"project validation hook exceeded {HOOK_DESCENDANT_LIMIT} descendant processes")
            if _descendant_count(discovered, self._root) > HOOK_DESCENDANT_LIMIT:
                self._known.update({pid: info.identity for pid, info in discovered.items()})
                raise RuntimeError(f"project validation hook exceeded {HOOK_DESCENDANT_LIMIT} descendant processes")

        self._known = {pid: info.identity for pid, info in discovered.items()}
        self._reap_adopted_zombies(discovered.values())
        return [
            info
            for info in discovered.values()
            if info.identity != self._root and info.state != "Z" and _matching_process(info.identity) is not None
        ]

    def terminate(self, process: subprocess.Popen[bytes], *, kill_process_group: bool) -> str:
        if kill_process_group:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
        try:
            process.kill()
        except OSError:
            pass

        deadline = time.monotonic() + HOOK_CLEANUP_SECONDS
        last_survivors: list[_ProcessInfo] = []
        while time.monotonic() < deadline:
            try:
                last_survivors = self.observe()
            except RuntimeError:
                last_survivors = self._live_known()
            except OSError as exc:
                return f"descendant cleanup monitoring failed: {exc}"
            for info in last_survivors:
                try:
                    os.kill(info.identity.pid, signal.SIGKILL)
                except (OSError, ProcessLookupError):
                    pass
            try:
                process.wait(timeout=0.02)
            except (subprocess.TimeoutExpired, ChildProcessError):
                pass
            self._reap_known_children()
            if process.poll() is not None and not last_survivors:
                return ""
            time.sleep(0.01)
        identities = ", ".join(f"{info.identity.pid}/{info.identity.start_time}" for info in last_survivors[:5])
        return f"descendant cleanup did not drain within {HOOK_CLEANUP_SECONDS:g} seconds ({identities or 'hook root'})"

    def close(self) -> None:
        self._reap_known_children()
        if self._previous_subreaper != 1:
            _set_child_subreaper(self._previous_subreaper)

    def _reap_adopted_zombies(self, processes) -> None:
        for info in processes:
            if info.state != "Z" or info.parent_pid != self._self_pid or info.identity == self._root:
                continue
            _reap_pid(info.identity.pid)

    def _reap_known_children(self) -> None:
        for identity in list(self._known.values()):
            info = _matching_process(identity)
            if info is not None and info.parent_pid == self._self_pid and identity != self._root:
                _reap_pid(identity.pid)

    def _live_known(self) -> list[_ProcessInfo]:
        live: list[_ProcessInfo] = []
        for identity in self._known.values():
            info = _matching_process(identity)
            if info is not None and info.identity != self._root and info.state != "Z":
                live.append(info)
        return live


def _get_child_subreaper() -> int:
    value = ctypes.c_int()
    _prctl(_PR_GET_CHILD_SUBREAPER, ctypes.byref(value))
    return value.value


def _set_child_subreaper(value: int) -> None:
    _prctl(_PR_SET_CHILD_SUBREAPER, ctypes.c_ulong(value))


def _prctl(option: int, argument) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.prctl(ctypes.c_int(option), argument, 0, 0, 0)
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def _direct_children(pid: int) -> set[_ProcessIdentity]:
    path = Path(f"/proc/{pid}/task/{pid}/children")
    try:
        values = path.read_text(encoding="ascii").split()
    except FileNotFoundError:
        return set()
    except OSError as exc:
        raise OSError(f"cannot inspect descendants of PID {pid}: {exc}") from exc
    identities: set[_ProcessIdentity] = set()
    for value in values:
        info = _process_info(int(value))
        if info is not None:
            identities.add(info.identity)
    return identities


def _matching_process(identity: _ProcessIdentity) -> _ProcessInfo | None:
    info = _process_info(identity.pid)
    if info is None or info.identity != identity:
        return None
    return info


def _descendant_count(processes: dict[int, _ProcessInfo], root: _ProcessIdentity | None) -> int:
    return sum(info.identity != root for info in processes.values())


def _process_info(pid: int) -> _ProcessInfo | None:
    try:
        value = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    except (FileNotFoundError, ProcessLookupError):
        return None
    except OSError as exc:
        raise OSError(f"cannot inspect process identity for PID {pid}: {exc}") from exc
    closing = value.rfind(")")
    if closing < 0:
        raise OSError(f"cannot parse process identity for PID {pid}")
    fields = value[closing + 2 :].split()
    if len(fields) < 20:
        raise OSError(f"cannot parse process identity for PID {pid}")
    return _ProcessInfo(
        identity=_ProcessIdentity(pid=pid, start_time=int(fields[19])),
        parent_pid=int(fields[1]),
        state=fields[0],
    )


def _reap_pid(pid: int) -> None:
    try:
        os.waitpid(pid, os.WNOHANG)
    except (ChildProcessError, OSError):
        pass
