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
import subprocess
import textwrap

import mock
import pytest

from eaclient import exceptions, system


class TestGetKernelInfo:
    @pytest.mark.parametrize(
        [
            "uname_machine",
            "uname_release",
            "build_date",
            "expected",
        ],
        (
            (
                "x86_64",
                "6.1.0-29-amd64",
                datetime.datetime(2023, 4, 6, 7, 48, 48),
                system.KernelInfo(
                    uname_machine_arch="x86_64",
                    uname_release="6.1.0-29-amd64",
                    build_date=datetime.datetime(2023, 4, 6, 7, 48, 48),
                    major=6,
                    minor=1,
                    patch=0,
                    abi="29",
                    flavor="amd64",
                ),
            ),
            (
                "aarch64",
                "6.1.0-29-imx-arm64",
                datetime.datetime(2023, 4, 6, 7, 48, 48),
                system.KernelInfo(
                    uname_machine_arch="aarch64",
                    uname_release="6.1.0-29-imx-arm64",
                    build_date=datetime.datetime(2023, 4, 6, 7, 48, 48),
                    major=6,
                    minor=1,
                    patch=0,
                    abi="29",
                    flavor="imx-arm64",
                ),
            ),
            (
                "x86_64",
                "6.1.29-something.invalid-security",
                datetime.datetime(2023, 4, 6, 7, 48, 48),
                system.KernelInfo(
                    uname_machine_arch="x86_64",
                    uname_release="6.1.29-something.invalid-security",
                    build_date=datetime.datetime(2023, 4, 6, 7, 48, 48),
                    major=None,
                    minor=None,
                    patch=None,
                    abi=None,
                    flavor=None,
                ),
            ),
        ),
    )
    @mock.patch("eaclient.system._get_kernel_build_date")
    @mock.patch("eaclient.system.load_file")
    @mock.patch("eaclient.system.os.uname")
    def test_get_kernel_info(
        self,
        m_uname,
        m_load_file,
        m_get_kernel_build_date,
        uname_machine,
        uname_release,
        build_date,
        expected,
    ):
        m_uname.return_value = mock.MagicMock(
            release=uname_release, machine=uname_machine
        )
        m_get_kernel_build_date.return_value = build_date
        assert system.get_kernel_info.__wrapped__() == expected

    @pytest.mark.parametrize(
        [
            "uname_result",
            "changelog_timestamp",
            "expected",
        ],
        [
            (
                os.uname_result(
                    [
                        "",
                        "",
                        "",
                        "#1 SMP PREEMPT_DYNAMIC Thu Apr  6 07:48:48 UTC 2023",  # noqa: E501
                        "",
                    ]
                ),
                mock.sentinel.changelog_timestamp,
                datetime.datetime(
                    2023, 4, 6, 7, 48, 48, tzinfo=datetime.timezone.utc
                ),
            ),
            (
                os.uname_result(["", "", "", "corrupted", ""]),
                mock.sentinel.changelog_timestamp,
                mock.sentinel.changelog_timestamp,
            ),
        ],
    )
    @mock.patch("eaclient.system._get_kernel_changelog_timestamp")
    def test_get_kernel_build_date(
        self,
        m_get_kernel_changelog_timestamp,
        uname_result,
        changelog_timestamp,
        expected,
    ):
        m_get_kernel_changelog_timestamp.return_value = changelog_timestamp
        assert expected == system._get_kernel_build_date(uname_result)

    @pytest.mark.parametrize(
        [
            "uname_result",
            "is_container",
            "stat_result",
            "expected_stat_call_args",
            "expected",
        ],
        [
            (
                None,
                True,
                None,
                [],
                None,
            ),
            (
                os.uname_result(["", "", "version-here", "", ""]),
                False,
                Exception(),
                [
                    mock.call(
                        "/usr/share/doc/linux-image-version-here/changelog.gz"  # noqa: E501
                    )
                ],
                None,
            ),
            (
                os.uname_result(["", "", "version-here", "", ""]),
                False,
                [os.stat_result([0, 0, 0, 0, 0, 0, 0, 0, 1680762951, 0])],
                [
                    mock.call(
                        "/usr/share/doc/linux-image-version-here/changelog.gz"  # noqa: E501
                    )
                ],
                datetime.datetime(
                    2023, 4, 6, 6, 35, 51, tzinfo=datetime.timezone.utc
                ),
            ),
        ],
    )
    @mock.patch("os.stat")
    @mock.patch("eaclient.system.is_container")
    def test_get_kernel_changelog_timestamp(
        self,
        m_is_container,
        m_os_stat,
        uname_result,
        is_container,
        stat_result,
        expected_stat_call_args,
        expected,
    ):
        m_is_container.return_value = is_container
        m_os_stat.side_effect = stat_result
        assert expected == system._get_kernel_changelog_timestamp(uname_result)
        assert expected_stat_call_args == m_os_stat.call_args_list


class TestGetDpkgArch:
    @pytest.mark.parametrize(
        "stdout, expected",
        (
            (
                "amd64",
                "amd64",
            ),
            (
                "arm64\n",
                "arm64",
            ),
            (
                "   arm64    \n",
                "arm64",
            ),
        ),
    )
    @mock.patch("eaclient.system.subp")
    def test_get_dpkg_arch(self, m_subp, stdout, expected):
        m_subp.return_value = (stdout, "")
        assert system.get_dpkg_arch.__wrapped__() == expected
        assert m_subp.call_args_list == [
            mock.call(["dpkg", "--print-architecture"])
        ]


class TestGetVirtType:
    @pytest.mark.parametrize(
        [
            "subp_side_effect",
            "load_file_side_effect",
            "expected",
        ],
        [
            ([("", "")], None, ""),
            ([("lxc\n", "")], None, "lxc"),
            ([("lxc\n", "anything")], None, "lxc"),
            (
                exceptions.ProcessExecutionError(cmd="", stdout="", stderr=""),
                [""],
                "",
            ),
            (
                exceptions.ProcessExecutionError(cmd="", stdout="", stderr=""),
                ["line\nline\nlinedockerline\nline"],
                "docker",
            ),
            (
                exceptions.ProcessExecutionError(cmd="", stdout="", stderr=""),
                ["line\nline\nlinebuildkitline\nline"],
                "docker",
            ),
            (
                exceptions.ProcessExecutionError(cmd="", stdout="", stderr=""),
                ["line\nline\nlinebuildahline\nline"],
                "podman",
            ),
            (
                exceptions.ProcessExecutionError(cmd="", stdout="", stderr=""),
                ["line\nline\nline\nline"],
                "",
            ),
            (
                exceptions.ProcessExecutionError(cmd="", stdout="", stderr=""),
                FileNotFoundError(),
                "",
            ),
        ],
    )
    @mock.patch("eaclient.system.load_file")
    @mock.patch("eaclient.system.subp")
    def test_get_virt_type(
        self,
        m_subp,
        m_load_file,
        subp_side_effect,
        load_file_side_effect,
        expected,
    ):
        m_subp.side_effect = subp_side_effect
        m_load_file.side_effect = load_file_side_effect
        assert expected == system.get_virt_type.__wrapped__()


class TestIsContainer:
    @mock.patch("eaclient.system.subp")
    def test_true_systemd_detect_virt_success(self, m_subp):
        """Return True when systemd-detect virt exits success."""
        system.is_container.cache_clear()
        m_subp.side_effect = [
            exceptions.ProcessExecutionError(
                "Failed running command 'ischroot' [exit(1)]"
            ),
            "",
            "",
        ]
        assert True is system.is_container()
        # Second call for lru_cache test
        system.is_container()
        calls = [
            mock.call(["ischroot"]),
            mock.call(["systemd-detect-virt", "--quiet", "--container"]),
        ]
        assert calls == m_subp.call_args_list

    @mock.patch("eaclient.system.subp")
    def test_true_on_run_container_type(self, m_subp, tmpdir):
        """Return True when /run/container_type exists."""
        system.is_container.cache_clear()
        m_subp.side_effect = [
            exceptions.ProcessExecutionError(
                "Failed running command 'ischroot' [exit(1)]"
            ),
            OSError("No systemd-detect-virt utility"),
        ]
        tmpdir.join("container_type").write("")

        assert True is system.is_container(run_path=tmpdir.strpath)
        calls = [
            mock.call(["ischroot"]),
            mock.call(["systemd-detect-virt", "--quiet", "--container"]),
        ]
        assert calls == m_subp.call_args_list

    @mock.patch("eaclient.system.subp")
    def test_true_on_run_systemd_container(self, m_subp, tmpdir):
        """Return True when /run/systemd/container exists."""
        system.is_container.cache_clear()
        m_subp.side_effect = [
            exceptions.ProcessExecutionError(
                "Failed running command 'ischroot' [exit(1)]"
            ),
            OSError("No systemd-detect-virt utility"),
        ]
        tmpdir.join("systemd/container").write("", ensure=True)

        assert True is system.is_container(run_path=tmpdir.strpath)
        calls = [
            mock.call(["ischroot"]),
            mock.call(["systemd-detect-virt", "--quiet", "--container"]),
        ]
        assert calls == m_subp.call_args_list

    @mock.patch("eaclient.system.subp")
    def test_false_on_non_sytemd_detect_virt_and_no_runfiles(
        self, m_subp, tmpdir
    ):
        """Return False when sytemd-detect-virt erros and no /run/* files."""
        system.is_container.cache_clear()
        m_subp.side_effect = [
            exceptions.ProcessExecutionError(
                "Failed running command 'ischroot' [exit(1)]"
            ),
            OSError("No systemd-detect-virt utility"),
        ]
        tmpdir.join("systemd/container").write("", ensure=True)

        with mock.patch("eaclient.util.os.path.exists") as m_exists:
            m_exists.return_value = False
            assert False is system.is_container(run_path=tmpdir.strpath)
        calls = [
            mock.call(["ischroot"]),
            mock.call(["systemd-detect-virt", "--quiet", "--container"]),
        ]
        assert calls == m_subp.call_args_list
        exists_calls = [
            mock.call(tmpdir.join("container_type").strpath),
            mock.call(tmpdir.join("systemd/container").strpath),
        ]
        assert exists_calls == m_exists.call_args_list

    @mock.patch("eaclient.system.subp")
    def test_false_on_chroot_system(self, m_subp):
        system.is_container.cache_clear()
        m_subp.return_value = ("", "")
        assert False is system.is_container()

        calls = [mock.call(["ischroot"])]
        assert calls == m_subp.call_args_list


class TestParseOSRelease:
    @pytest.mark.parametrize(
        "content, expected",
        (
            (
                """\
PRETTY_NAME="eLxr 12 (aria)"
NAME="eLxr"
VARIANT="Server Edition"
VARIANT_ID=server
VERSION_ID="12"
VERSION="12 (aria)"
VERSION_CODENAME=aria
ID=elxr
ID_LIKE=debian
HOME_URL="https://elxr.dev"
SUPPORT_URL="https://elxr.dev"
BUG_REPORT_URL="https://gitlab.com/groups/elxr/-/issues"
""",
                {
                    "PRETTY_NAME": "eLxr 12 (aria)",
                    "NAME": "eLxr",
                    "VARIANT": "Server Edition",
                    "VARIANT_ID": "server",
                    "VERSION_ID": "12",
                    "VERSION": "12 (aria)",
                    "VERSION_CODENAME": "aria",
                    "ID": "elxr",
                    "ID_LIKE": "debian",
                    "HOME_URL": "https://elxr.dev",
                    "SUPPORT_URL": "https://elxr.dev",
                    "BUG_REPORT_URL": "https://gitlab.com/groups/elxr/-/issues"
                },
            ),
        ),
    )
    @mock.patch("eaclient.system.load_file")
    def test_parse_os_release(self, m_load_file, content, expected):
        """_parse_os_release returns a dict of values from /etc/os-release."""
        m_load_file.return_value = content
        assert expected == system._parse_os_release.__wrapped__()
        assert m_load_file.call_args_list == [mock.call("/etc/os-release")]


class TestGetReleaseInfo:
    @pytest.mark.parametrize(
        ["os_release", "expected"],
        [
            (
                {
                    "NAME": "eLxr",
                    "VERSION_ID": "12",
                    "VERSION_CODENAME": "aria",
                },
                system.ReleaseInfo(
                    distribution="eLxr",
                    release="12",
                    series="aria",
                ),
            ),
        ],
    )
    @mock.patch("eaclient.system.get_kernel_info")
    @mock.patch("eaclient.system.get_dpkg_arch")
    @mock.patch("eaclient.system._parse_os_release")
    @mock.patch("eaclient.system.get_virt_type")
    def test_get_release_info_with_version(
        self,
        m_get_virt_type,
        m_parse_os_release,
        m_get_dpkg_arch,
        m_get_kernel_info,
        os_release,
        expected,
    ):
        m_parse_os_release.return_value = os_release
        assert expected == system.get_release_info.__wrapped__()


@mock.patch("eaclient.files.state_files.machine_id_file.write")
class TestGetMachineId:
    def test_get_machine_id_from_machine_token_file(
        self, _m_machine_id_file_write, fake_machine_token_file
    ):
        fake_machine_token_file.attached = True
        value = system.get_machine_id(None)
        assert "test_machine_id" == value

    @mock.patch("eaclient.files.state_files.machine_id_file.read")
    def test_get_machine_id_from_etc_machine_id(
        self,
        m_machine_id_file_read,
        _m_machine_id_file_write,
        FakeConfig,
        tmpdir,
    ):
        """Presence of /etc/machine-id is returned if it exists."""
        etc_machine_id = tmpdir.join("etc-machine-id")
        m_machine_id_file_read.return_value = None
        assert "/etc/machine-id" == system.ETC_MACHINE_ID
        etc_machine_id.write("etc-machine-id")
        cfg = FakeConfig()
        with mock.patch(
            "eaclient.system.ETC_MACHINE_ID", etc_machine_id.strpath
        ):
            value = system.get_machine_id(cfg)
            # Test lru_cache caches /etc/machine-id from first read
            etc_machine_id.write("does-not-change")
            cached_value = system.get_machine_id(cfg)
            assert value == cached_value
        assert "etc-machine-id" == value

    @mock.patch("eaclient.files.state_files.machine_id_file.read")
    def test_get_machine_id_from_var_lib_dbus_machine_id(
        self,
        m_machine_id_file_read,
        _m_machine_id_file_write,
        FakeConfig,
        tmpdir,
    ):
        """fallback to /var/lib/dbus/machine-id"""
        m_machine_id_file_read.return_value = None
        etc_machine_id = tmpdir.join("etc-machine-id")
        dbus_machine_id = tmpdir.join("dbus-machine-id")
        assert "/var/lib/dbus/machine-id" == system.DBUS_MACHINE_ID
        dbus_machine_id.write("dbus-machine-id")
        cfg = FakeConfig()
        with mock.patch(
            "eaclient.system.DBUS_MACHINE_ID", dbus_machine_id.strpath
        ):
            with mock.patch(
                "eaclient.system.ETC_MACHINE_ID", etc_machine_id.strpath
            ):
                value = system.get_machine_id(cfg)
        assert "dbus-machine-id" == value


class TestWriteFile:
    @mock.patch("os.unlink")
    @mock.patch("os.rename")
    @mock.patch("os.makedirs")
    @mock.patch("os.chmod")
    @mock.patch("tempfile.NamedTemporaryFile")
    def test_delete_tempfile_on_error(
        self,
        m_NamedTemporaryFile,
        m_chmod,
        m_makedirs,
        m_rename,
        m_unlink,
    ):
        test_tmpfile = mock.MagicMock()
        test_tmpfile.name = "test_tmpfile"
        m_NamedTemporaryFile.return_value = test_tmpfile

        m_rename.side_effect = Exception()

        with pytest.raises(Exception):
            system.write_file("test", "test")

        assert [mock.call("test_tmpfile")] == m_unlink.call_args_list


class TestSubp:
    def test_raise_error_on_timeout(self, _subp):
        """When cmd exceeds the timeout raises a TimeoutExpired error."""
        with mock.patch("eaclient.system._subp", side_effect=_subp):
            with pytest.raises(subprocess.TimeoutExpired) as excinfo:
                system.subp(["sleep", "2"], timeout=0)
        msg = "Command '[b'sleep', b'2']' timed out after 0 seconds"
        assert msg == str(excinfo.value)

    @mock.patch("eaclient.util.time.sleep")
    def test_default_do_not_retry_on_failure_return_code(self, m_sleep, _subp):
        """When no retry_sleeps are specified, do not retry failures."""
        with mock.patch("eaclient.system._subp", side_effect=_subp):
            with pytest.raises(exceptions.ProcessExecutionError) as excinfo:
                system.subp(["ls", "--bogus"])

        assert 2 == excinfo.value.exit_code
        assert "" == excinfo.value.stdout
        assert 0 == m_sleep.call_count  # no retries

    @mock.patch("eaclient.util.time.sleep")
    def test_no_error_on_accepted_return_codes(self, m_sleep, _subp):
        """When rcs list includes the exit code, do not raise an error."""
        with mock.patch("eaclient.system._subp", side_effect=_subp):
            out, _ = system.subp(["ls", "--bogus"], rcs=[2])

        assert "" == out
        assert 0 == m_sleep.call_count  # no retries

    @mock.patch("eaclient.util.time.sleep")
    def test_retry_with_specified_sleeps_on_error(self, m_sleep, _subp):
        """When retry_sleeps given, use defined sleeps between each retry."""
        with mock.patch("eaclient.system._subp", side_effect=_subp):
            with pytest.raises(exceptions.ProcessExecutionError) as excinfo:
                system.subp(["ls", "--bogus"], retry_sleeps=[1, 3, 0.4])

        expected_error = "Failed running command 'ls --bogus' [exit(2)]"
        assert expected_error in str(excinfo.value)
        expected_sleeps = [mock.call(1), mock.call(3), mock.call(0.4)]
        assert expected_sleeps == m_sleep.call_args_list

    @mock.patch("eaclient.util.time.sleep")
    def test_retry_doesnt_consume_retry_sleeps(self, m_sleep, _subp):
        """When retry_sleeps given, use defined sleeps between each retry."""
        sleeps = [1, 3, 0.4]
        expected_sleeps = sleeps.copy()
        with mock.patch("eaclient.system._subp", side_effect=_subp):
            with pytest.raises(exceptions.ProcessExecutionError):
                system.subp(["ls", "--bogus"], retry_sleeps=sleeps)

        assert expected_sleeps == sleeps

    @pytest.mark.parametrize("caplog_text", [logging.DEBUG], indirect=True)
    @mock.patch("eaclient.system._subp")
    @mock.patch("eaclient.util.time.sleep")
    def test_retry_logs_remaining_retries(self, m_sleep, m_subp, caplog_text):
        """When retry_sleeps given, use defined sleeps between each retry."""
        sleeps = [1, 3, 0.4]
        m_subp.side_effect = exceptions.ProcessExecutionError(
            "Funky apt %d error"
        )
        with pytest.raises(exceptions.ProcessExecutionError):
            system.subp(["apt", "dostuff"], retry_sleeps=sleeps)

        logs = caplog_text()
        expected_logs = [
            "Invalid command specified 'Funky apt %d error'.",
            "Retrying 3 more times.",
            "Invalid command specified 'Funky apt %d error'.",
            "Retrying 2 more times.",
            "Invalid command specified 'Funky apt %d error'.",
            "Retrying 1 more times.",
        ]
        for log in expected_logs:
            assert log in logs

    @pytest.mark.parametrize("caplog_text", [logging.WARNING], indirect=True)
    @pytest.mark.parametrize("capture", [True, False])
    @mock.patch("eaclient.system._subp")
    def test_log_subp_fails_stdout_stderr_capture_toggle(
        self, m_subp, capture, caplog_text
    ):
        """When subp fails, capture the logs in stdout/stderr"""
        out = "Tried downloading file"
        err = "Network error"
        m_subp.side_effect = exceptions.ProcessExecutionError(
            "Serious apt error", stdout=out, stderr=err
        )
        with pytest.raises(exceptions.ProcessExecutionError):
            system.subp(["apt", "nothing"], capture=capture)

        logs = caplog_text()
        expected_logs = ["Stderr: {}".format(err), "Stdout: {}".format(out)]
        for log in expected_logs:
            if capture:
                assert log in logs
            else:
                assert log not in logs

    @pytest.mark.parametrize(
        [
            "override_env_vars",
            "os_environ",
            "expected_env_arg",
        ],
        (
            (None, {}, {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}),
            (
                None,
                {"test": "val"},
                {"test": "val", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            ),
            (
                {},
                {"test": "val"},
                {"test": "val", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            ),
            (
                {"set": "new"},
                {"test": "val"},
                {
                    "test": "val",
                    "LANG": "C.UTF-8",
                    "LC_ALL": "C.UTF-8",
                    "set": "new",
                },
            ),
            (
                {"set": "new", "test": "newval"},
                {"test": "val"},
                {
                    "LANG": "C.UTF-8",
                    "LC_ALL": "C.UTF-8",
                    "test": "newval",
                    "set": "new",
                },
            ),
        ),
    )
    @mock.patch("subprocess.Popen")
    def test_subp_uses_environment_variables(
        self,
        m_popen,
        override_env_vars,
        os_environ,
        expected_env_arg,
        _subp,
    ):
        mock_process = mock.MagicMock(returncode=0)
        mock_process.communicate.return_value = (b"", b"")
        m_popen.return_value = mock_process

        with mock.patch("os.environ", os_environ):
            _subp(["apt", "nothing"], override_env_vars=override_env_vars)

        assert [
            mock.call(
                [b"apt", b"nothing"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=expected_env_arg,
            )
        ] == m_popen.call_args_list

    @mock.patch("subprocess.Popen")
    def test_subp_no_pipe_stdouterr(
        self,
        m_popen,
        _subp,
    ):
        mock_process = mock.MagicMock(returncode=0)
        mock_process.communicate.return_value = (b"", b"")
        m_popen.return_value = mock_process

        with mock.patch("os.environ", {}):
            _subp(["fake"], pipe_stdouterr=False)

        assert [
            mock.call(
                [b"fake"],
                stdout=None,
                stderr=None,
                env={},
            )
        ] == m_popen.call_args_list

    @mock.patch("subprocess.Popen")
    def test_subp_ignores_non_utf8(
        self,
        m_popen,
        _subp,
    ):
        mock_process = mock.MagicMock(returncode=0)
        mock_process.communicate.return_value = (b"T\x8fE\xacS\x93T\x87!", b"")
        m_popen.return_value = mock_process

        out, _ = _subp(["fake"], pipe_stdouterr=False)

        assert "TEST!" == out


class TestGetCpuInfo:
    @pytest.mark.parametrize(
        "cpuinfo,vendor_id,model,stepping",
        (
            (
                textwrap.dedent(
                    """
                processor       : 6
                vendor_id       : GenuineIntel
                cpu family      : 6
                model           : 142
                model name      : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
                stepping        : 10

                processor       : 7
                vendor_id       : GenuineIntel
                cpu family      : 6
                model           : 142
                model name      : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
                stepping        : 10"""
                ),
                "intel",
                142,
                10,
            ),
            (
                textwrap.dedent(
                    """
                processor       : 6
                vendor_id       : test
                cpu family      : 6
                model           : 148
                model name      : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
                stepping        : 12

                processor       : 7
                vendor_id       : GenuineIntel
                cpu family      : 6
                model           : 142
                model name      : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
                stepping        : 10"""
                ),
                "test",
                148,
                12,
            ),
            (
                textwrap.dedent(
                    """
                processor       : 6
                cpu family      : 6
                model name      : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz

                processor       : 7
                cpu family      : 6
                model name      : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz"""
                ),
                "",
                None,
                None,
            ),
        ),
    )
    @mock.patch("eaclient.system.load_file")
    def test_get_cpu_vendor(
        self, m_load_file, cpuinfo, vendor_id, model, stepping
    ):
        m_load_file.return_value = cpuinfo
        assert vendor_id == system.get_cpu_info.__wrapped__().vendor_id
        assert model == system.get_cpu_info.__wrapped__().model
        assert stepping == system.get_cpu_info.__wrapped__().stepping


class TestGetUserCacheDir:
    @pytest.mark.parametrize(
        [
            "is_root",
            "xdg_cache_home",
            "expanduser_result",
            "expected",
        ],
        (
            (True, None, None, "/run/elxr-advantage"),
            (False, None, "/home/user", "/home/user/.cache/elxr-pro"),
            (False, "/something", "/home/user", "/something/elxr-pro"),
        ),
    )
    @mock.patch("os.path.expanduser")
    @mock.patch("os.environ.get")
    @mock.patch("eaclient.util.we_are_currently_root")
    def test_get_user_cache_dir(
        self,
        m_we_are_currently_root,
        m_environ_get,
        m_expanduser,
        is_root,
        xdg_cache_home,
        expanduser_result,
        expected,
    ):
        m_we_are_currently_root.return_value = is_root
        m_environ_get.return_value = xdg_cache_home
        m_expanduser.return_value = expanduser_result
        assert expected == system.get_user_cache_dir()
