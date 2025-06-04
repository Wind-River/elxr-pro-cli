# Copyright (c) 2025 Wind River Systems, Inc.
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

import datetime
import logging
import os
import pathlib
import re
import stat
import subprocess  # nosec B404
import tempfile
import time
import uuid
from functools import lru_cache
from typing import (
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

from eaclient import (
    defaults,
    exceptions,
    util,
)

ETC_MACHINE_ID = "/etc/machine-id"
DBUS_MACHINE_ID = "/var/lib/dbus/machine-id"

CPU_VENDOR_MAP = {"GenuineIntel": "intel"}
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))

RE_KERNEL_UNAME = (
    r"^"
    r"(?P<major>[\d]+)"
    r"[.-]"
    r"(?P<minor>[\d]+)"
    r"[.-]"
    r"(?P<patch>[\d]+)"
    r"-"
    r"(?P<abi>[\d]+)"
    r"-"
    r"(?P<flavor>[A-Za-z0-9_-]+)"
    r"$"
)

KernelInfo = NamedTuple(
    "KernelInfo",
    [
        ("uname_machine_arch", str),
        ("uname_release", str),
        ("build_date", Optional[datetime.datetime]),
        ("major", Optional[int]),
        ("minor", Optional[int]),
        ("patch", Optional[int]),
        ("abi", Optional[str]),
        ("flavor", Optional[str]),
    ],
)

ReleaseInfo = NamedTuple(
    "ReleaseInfo",
    [
        ("distribution", str),
        ("release", str),
        ("series", str),
        ("variant", str),
    ],
)

CpuInfo = NamedTuple(
    "CpuInfo",
    [
        ("vendor_id", str),
        ("model", Optional[int]),
        ("stepping", Optional[int]),
    ],
)


RE_KERNEL_EXTRACT_BUILD_DATE = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun).*"


def _get_kernel_changelog_timestamp(
    uname: os.uname_result,
) -> Optional[datetime.datetime]:
    if is_container():
        LOG.warning(
            "Not attempting to use timestamp of kernel "
            "changelog because we're in a container"
        )
        return None

    LOG.warning("Falling back to using timestamp of kernel changelog")

    try:
        stat_result = os.stat(
            "/usr/share/doc/linux-image-{}/changelog.gz".format(
                uname.release
            )
        )
        return datetime.datetime.fromtimestamp(
            stat_result.st_mtime, datetime.timezone.utc
        )
    except Exception:
        LOG.warning("Unable to stat kernel changelog")
        return None


def _get_kernel_build_date(
    uname: os.uname_result,
) -> Optional[datetime.datetime]:
    date_match = re.search(RE_KERNEL_EXTRACT_BUILD_DATE, uname.version)
    if date_match is None:
        LOG.warning("Unable to find build date in uname version")
        return _get_kernel_changelog_timestamp(uname)
    date_str = date_match.group(0)
    try:
        dt = datetime.datetime.strptime(date_str, "%a %b %d %H:%M:%S %Z %Y")
    except ValueError:
        LOG.warning("Unable to parse build date from uname version")
        return _get_kernel_changelog_timestamp(uname)
    if dt.tzinfo is None:
        # Give it a default timezone if it didn't get one from strptime
        # The Livepatch API requires a timezone
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


@lru_cache(maxsize=None)
def get_kernel_info() -> KernelInfo:
    uname = os.uname()
    uname_machine_arch = uname.machine.strip()
    build_date = _get_kernel_build_date(uname)

    uname_release = uname.release.strip()
    uname_match = re.match(RE_KERNEL_UNAME, uname_release)
    if uname_match is None:
        LOG.warning("Failed to parse kernel: %s", uname_release)
        return KernelInfo(
            uname_machine_arch=uname_machine_arch,
            uname_release=uname_release,
            build_date=build_date,
            major=None,
            minor=None,
            patch=None,
            abi=None,
            flavor=None,
        )
    else:
        return KernelInfo(
            uname_machine_arch=uname_machine_arch,
            uname_release=uname_release,
            build_date=build_date,
            major=int(uname_match.group("major")),
            minor=int(uname_match.group("minor")),
            patch=int(uname_match.group("patch")),
            abi=uname_match.group("abi"),
            flavor=uname_match.group("flavor"),
        )


@lru_cache(maxsize=None)
def get_dpkg_arch() -> str:
    out, _err = subp(["dpkg", "--print-architecture"])
    return out.strip()


@lru_cache(maxsize=None)
def get_virt_type() -> str:
    try:
        out, _ = subp(["systemd-detect-virt"])
        return out.strip()
    except exceptions.ProcessExecutionError:
        # The main known place where that will fail is in a docker/podman
        # container that doesn't have it installed. So we look for hints
        # of that situation to report it accurately.
        try:
            proc_1_cgroup = load_file("/proc/1/cgroup")
            if "docker" in proc_1_cgroup or "buildkit" in proc_1_cgroup:
                return "docker"
            elif "buildah" in proc_1_cgroup:
                return "podman"
            else:
                return ""
        except Exception:
            return ""


@lru_cache(maxsize=None)
def get_cpu_info() -> CpuInfo:
    cpu_info_content = load_file("/proc/cpuinfo")
    cpu_info_values = {}
    for field in ["vendor_id", "model", "stepping"]:
        cpu_match = re.search(
            r"^{}\s*:\s*(?P<info>\w*)".format(field),
            cpu_info_content,
            re.MULTILINE,
        )
        if cpu_match:
            value = cpu_match.group("info")
            cpu_info_values[field] = value

    vendor_id_base = cpu_info_values.get("vendor_id", "")
    model = cpu_info_values.get("model")
    stepping = cpu_info_values.get("stepping")
    return CpuInfo(
        vendor_id=CPU_VENDOR_MAP.get(vendor_id_base, vendor_id_base),
        model=int(model) if model else None,
        stepping=int(stepping) if stepping else None,
    )


@lru_cache(maxsize=None)
def get_machine_id(cfg) -> str:
    """
    Get system's unique machine-id or create our own in data_dir.
    We first check for the machine-id in machine-token.json before
    looking at the system file.
    """
    from eaclient.files import machine_token

    machine_token_file = machine_token.get_machine_token_file()
    if machine_token_file.machine_token:
        machine_id = machine_token_file.machine_token.get("machineId")
        if machine_id:
            return machine_id

    for path in [ETC_MACHINE_ID, DBUS_MACHINE_ID]:
        if os.path.exists(path):
            content = load_file(path).rstrip("\n")
            if content:
                return content

    machine_id = str(uuid.uuid4())
    return machine_id


@lru_cache(maxsize=None)
def get_release_info() -> ReleaseInfo:
    os_release = _parse_os_release()
    distribution = os_release.get("NAME", "UNKNOWN")
    series = os_release.get("VERSION_CODENAME", "")
    release = os_release.get("VERSION_ID", "")
    variant = os_release.get("VARIANT_ID", "")

    return ReleaseInfo(
        distribution=distribution,
        release=release,
        series=series.lower(),
        variant=variant,
    )


@lru_cache(maxsize=None)
def is_desktop() -> bool:
    """Checks to see if this code running in desktop env"""
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return True
    try:
        result, _ = subp(["tasksel", "--list-tasks"])
        for line in result.splitlines():
            parts = line.strip().split(None, 2)
            if len(parts) >= 2 and parts[0] == "i" and "desktop" in parts[1]:
                return True
    except exceptions.ProcessExecutionError:
        pass
    return False


@lru_cache(maxsize=None)
def is_container(run_path: str = "/run") -> bool:
    """Checks to see if this code running in a container of some sort"""

    # We may mistake schroot environments for containers by just relying
    # in the other checks present in that function. To guarantee that
    # we do not identify a schroot as a container, we are explicitly
    # using the 'ischroot' command here.
    try:
        subp(["ischroot"])
        return False
    except exceptions.ProcessExecutionError:
        pass

    try:
        subp(["systemd-detect-virt", "--quiet", "--container"])
        return True
    except (IOError, OSError):
        pass

    for filename in ("container_type", "systemd/container"):
        path = os.path.join(run_path, filename)
        if os.path.exists(path):
            return True
    return False


@lru_cache(maxsize=None)
def _parse_os_release() -> Dict[str, str]:
    try:
        file_contents = load_file("/etc/os-release")
    except FileNotFoundError:
        file_contents = load_file("/usr/lib/os-release")
    data = {}
    for line in file_contents.splitlines():
        key, value = line.split("=", 1)
        if value:
            data[key] = value.strip().strip('"')
    return data


def is_exe(path: str) -> bool:
    # return boolean indicating if path exists and is executable.
    return os.path.isfile(path) and os.access(path, os.X_OK)


def load_file(filename: str) -> str:
    """Read filename and decode content."""
    with open(filename, "rb") as stream:
        LOG.debug("Reading file: %s", filename)
        content = stream.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        raise exceptions.InvalidFileEncodingError(
            file_name=filename, file_encoding="utf-8"
        )


def create_file(filename: str, mode: int = 0o644) -> None:
    LOG.debug("Creating file: %s", filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    pathlib.Path(filename).touch()
    os.chmod(filename, mode)


def write_file(
    filename: str, content: str, mode: Optional[int] = None
) -> None:
    """Write content to the provided filename encoding it if necessary.

    We preserve the file ownership and permissions if the file is present
    and no mode argument is provided.

    @param filename: The full path of the file to write.
    @param content: The content to write to the file.
    @param mode: The filesystem mode to set on the file.
    """
    tmpf = None
    is_file_present = os.path.isfile(filename)
    if is_file_present:
        file_stat = pathlib.Path(filename).stat()
        f_mode = stat.S_IMODE(file_stat.st_mode)
        if mode is None:
            mode = f_mode

    elif mode is None:
        mode = 0o644
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        tmpf = tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=os.path.dirname(filename)
        )
        LOG.debug(
            "Writing file %s atomically via tempfile %s", filename, tmpf.name
        )
        tmpf.write(content.encode("utf-8"))
        tmpf.flush()
        tmpf.close()
        os.chmod(tmpf.name, mode)
        if is_file_present:
            os.chown(tmpf.name, file_stat.st_uid, file_stat.st_gid)
        os.rename(tmpf.name, filename)
    except Exception as e:
        if tmpf is not None:
            os.unlink(tmpf.name)
        raise e


def ensure_file_absent(file_path: str) -> None:
    """Remove a file if it exists, logging a message about removal."""
    try:
        os.unlink(file_path)
        LOG.debug("Removed file: %s", file_path)
    except FileNotFoundError:
        LOG.debug("Tried to remove %s but file does not exist", file_path)


def _subp(
    args: Sequence[str],
    rcs: Optional[List[int]] = None,
    capture: bool = False,
    timeout: Optional[float] = None,
    override_env_vars: Optional[Dict[str, str]] = None,
    pipe_stdouterr: bool = True,
) -> Tuple[str, str]:
    """Run a command and return a tuple of decoded stdout, stderr.

    @param args: A list of arguments to feed to subprocess.Popen
    @param rcs: A list of allowed return_codes. If returncode not in rcs
        raise a ProcessExecutionError.
    @param capture: Boolean set True to log the command and response.
    @param timeout: Optional float indicating number of seconds to wait for
        subp to return.
    @param override_env_vars: Optional dictionary of environment variables.
        If None, the current os.environ is used for the subprocess.
        If defined, these env vars get merged with the current process'
        os.environ for the subprocess, overriding any values that already
        existed in os.environ.

    @return: Tuple of utf-8 decoded stdout, stderr
    @raises ProcessExecutionError on invalid command or returncode not in rcs.
    @raises subprocess.TimeoutError when timeout specified and the command
        exceeds that number of seconds.
    """
    bytes_args = [
        x if isinstance(x, bytes) else x.encode("utf-8") for x in args
    ]

    stdout = None
    stderr = None
    set_lang = {}

    if pipe_stdouterr:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        # Set LANG to avoid non-utf8 when we pipe the handlers
        set_lang = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}

    if override_env_vars is None:
        override_env_vars = {}
    merged_env = {**os.environ, **set_lang, **override_env_vars}

    if rcs is None:
        rcs = [0]
    redacted_cmd = util.redact_sensitive_logs(" ".join(args))
    try:
        proc = subprocess.Popen(  # nosec B603
            bytes_args,
            stdout=stdout,
            stderr=stderr,
            env=merged_env,
        )
        (out, err) = proc.communicate(timeout=timeout)
    except OSError:
        try:
            out_result = out.decode("utf-8", errors="ignore") if out else ""
            err_result = err.decode("utf-8", errors="ignore") if err else ""
            raise exceptions.ProcessExecutionError(
                cmd=redacted_cmd,
                exit_code=proc.returncode,
                stdout=out_result,
                stderr=err_result,
            )
        except UnboundLocalError:
            raise exceptions.ProcessExecutionError(cmd=redacted_cmd)

    out_result = out.decode("utf-8", errors="ignore") if out else ""
    err_result = err.decode("utf-8", errors="ignore") if err else ""
    if proc.returncode not in rcs:
        raise exceptions.ProcessExecutionError(
            cmd=redacted_cmd,
            exit_code=proc.returncode,
            stdout=out_result,
            stderr=err_result,
        )
    if capture:
        LOG.debug(
            "Ran cmd: %s, rc: %s stderr: %s",
            redacted_cmd,
            proc.returncode,
            err,
        )
    return out_result, err_result


def subp(
    args: Sequence[str],
    rcs: Optional[List[int]] = None,
    capture: bool = False,
    timeout: Optional[float] = None,
    retry_sleeps: Optional[List[float]] = None,
    override_env_vars: Optional[Dict[str, str]] = None,
    pipe_stdouterr: bool = True,
) -> Tuple[str, str]:
    """Run a command and return a tuple of decoded stdout, stderr.

     @param subp: A list of arguments to feed to subprocess.Popen
     @param rcs: A list of allowed return_codes. If returncode not in rcs
         raise a ProcessExecutionError.
     @param capture: Boolean set True to log the command and response.
     @param timeout: Optional float indicating number of seconds to wait for a
         subp call to return.
     @param retry_sleeps: Optional list of sleep lengths to apply between
        retries. Specifying a list of [0.5, 1] instructs subp to retry twice
        on failure; sleeping half a second before the first retry and 1 second
        before the next retry.
     @param override_env_vars: Optional dictionary of environment variables.
        If None, the current os.environ is used for the subprocess.
        If defined, these env vars get merged with the current process'
        os.environ for the subprocess, overriding any values that already
        existed in os.environ.

    @return: Tuple of utf-8 decoded stdout, stderr
    @raises ProcessExecutionError on invalid command or returncode not in rcs.
    @raises subprocess.TimeoutError when timeout specified and the command
        exceeds that number of seconds.
    """
    retry_sleeps = retry_sleeps.copy() if retry_sleeps is not None else None
    while True:
        try:
            out, err = _subp(
                args,
                rcs,
                capture,
                timeout,
                override_env_vars=override_env_vars,
                pipe_stdouterr=pipe_stdouterr,
            )
            break
        except exceptions.ProcessExecutionError as e:
            if capture:
                LOG.debug(str(e))
                LOG.warning("Stderr: %s\nStdout: %s", e.stderr, e.stdout)
            if not retry_sleeps:
                raise
            LOG.debug(str(e))
            LOG.debug("Retrying %d more times.", len(retry_sleeps))
            time.sleep(retry_sleeps.pop(0))
    return out, err


def get_user_cache_dir() -> str:
    if util.we_are_currently_root():
        return defaults.EAC_RUN_PATH

    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        return os.path.join(xdg_cache_home, defaults.USER_CACHE_SUBDIR)

    return os.path.join(
        os.path.expanduser("~"), ".cache", defaults.USER_CACHE_SUBDIR
    )
