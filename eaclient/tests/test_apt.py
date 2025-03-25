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

"""Tests related to eaclient.apt module."""

import os
import stat
import subprocess
from textwrap import dedent
from typing import List, Optional

import mock
import pytest

from eaclient import exceptions, messages, system
from eaclient.apt import (
    APT_AUTH_COMMENT,
    APT_CONFIG_GLOBAL_PROXY_HTTP,
    APT_CONFIG_GLOBAL_PROXY_HTTPS,
    APT_HELPER_TIMEOUT,
    APT_KEYS_DIR,
    APT_PROXY_CONF_FILE,
    APT_PROXY_CONFIG_HEADER,
    APT_RETRIES,
    KEYRINGS_DIR,
    SERIES_NOT_USING_DEB822,
    add_apt_auth_conf_entry,
    add_auth_apt_repo,
    assert_valid_apt_credentials,
    remove_auth_apt_repo,
    remove_repo_from_apt_auth_file,
    setup_apt_proxy,
)

POST_INSTALL_APT_CACHE_NO_UPDATES = """
-32768 https://mirror.elxr.dev {0}-updates/main amd64 Packages
     release v=12,o={1},a={0}-updates,n={0},l=elxr,c=main
     origin mirror.elxr.dev
"""

APT_LIST_RETURN_STRING = """\
"Listing... Done
a/release, now 1.2+3 arch123 [i,a]
b/release-updates, now 1.2+3 arch123 [i,a]
"""


def mock_origin(
    component: str, archive: str, origin: str, site: str
) -> mock.MagicMock:
    mock_origin = mock.MagicMock()
    mock_origin.component = component
    mock_origin.archive = archive
    mock_origin.origin = origin
    mock_origin.site = site
    return [mock_origin, 0]


def mock_version(
    version: str,
    origin_list: List[mock.MagicMock] = [],
    size: int = 1,
) -> mock.MagicMock:
    mock_version = mock.MagicMock()
    mock_version.__gt__ = lambda self, other: self.ver_str > other.ver_str
    mock_version.ver_str = version
    mock_version.file_list = origin_list
    mock_version.size = size
    return mock_version


def mock_package(
    name: str,
    installed_version: Optional[mock.MagicMock] = None,
    other_versions: List[mock.MagicMock] = [],
):
    mock_package = mock.MagicMock()
    mock_package.name = name
    mock_package.version_list = []

    mock_package.current_ver = None
    if installed_version:
        mock_package.current_ver = installed_version
        installed_version.parent_pkg = mock_package
        mock_package.version_list.append(installed_version)

    for version in other_versions:
        version.parent_pkg = mock_package
        mock_package.version_list.append(version)

    return mock_package


class TestValidAptCredentials:
    @mock.patch("eaclient.system.subp")
    @mock.patch("os.path.exists", return_value=False)
    def test_passes_when_missing_apt_helper(self, m_exists, m_subp):
        """When apt-helper tool is absent perform no validation."""
        assert None is assert_valid_apt_credentials(
            repo_url="http://fakerepo", username="username", password="pass"
        )
        expected_calls = [mock.call("/usr/lib/apt/apt-helper")]
        assert expected_calls == m_exists.call_args_list
        assert 0 == m_subp.call_count

    @mock.patch("eaclient.apt.tempfile.TemporaryDirectory")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.os.path.exists", return_value=True)
    def test_passes_on_valid_creds(
        self, m_exists, m_subp, m_temporary_directory
    ):
        """Succeed when apt-helper succeeds in authenticating to repo."""
        m_temporary_directory.return_value.__enter__.return_value = (
            "/does/not/exist"
        )
        # Success apt-helper response
        m_subp.return_value = "Get:1 https://fakerepo\nFetched 285 B in 1s", ""

        assert None is assert_valid_apt_credentials(
            repo_url="http://fakerepo", username="user", password="pwd"
        )
        exists_calls = [mock.call("/usr/lib/apt/apt-helper")]
        assert exists_calls == m_exists.call_args_list
        expected_path = os.path.join(
            m_temporary_directory.return_value.__enter__.return_value,
            "apt-helper-output",
        )
        apt_helper_call = mock.call(
            [
                "/usr/lib/apt/apt-helper",
                "download-file",
                "http://user:pwd@fakerepo/pool/",
                expected_path,
            ],
            timeout=60,
            retry_sleeps=APT_RETRIES,
        )
        assert [apt_helper_call] == m_subp.call_args_list

    @pytest.mark.parametrize(
        "exit_code,stderr,error_msg",
        (
            (
                1,
                "something broke",
                (
                    "Unexpected APT error.\n"
                    "Failed running command 'apt-helper ' [exit(1)]. Message: "
                    "something broke\n"
                    "See /var/log/elxr-advantage.log"
                ),
            ),
            (
                100,
                "E: Failed to fetch ... HttpError401 on xenial",
                "Invalid APT credentials provided for http://fakerepo",
            ),
            (
                100,
                "E: Failed to fetch ... 401 Unauthorized on xenial",
                "Invalid APT credentials provided for http://fakerepo",
            ),
            (
                100,
                "E: Failed to fetch ... Connection timed out",
                "Timeout trying to access APT repository at http://fakerepo",
            ),
        ),
    )
    @mock.patch("eaclient.apt.tempfile.TemporaryDirectory")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.os.path.exists", return_value=True)
    def test_errors_on_process_execution_errors(
        self,
        m_exists,
        m_subp,
        m_temporary_directory,
        exit_code,
        stderr,
        error_msg,
    ):
        """Raise the appropriate user facing error from apt-helper failure."""
        m_temporary_directory.return_value.__enter__.return_value = (
            "/does/not/exist"
        )
        # Failure apt-helper response
        m_subp.side_effect = exceptions.ProcessExecutionError(
            cmd="apt-helper ",
            exit_code=exit_code,
            stdout="Err:1...",
            stderr=stderr,
        )

        with pytest.raises(exceptions.ELxrProError) as excinfo:
            assert_valid_apt_credentials(
                repo_url="http://fakerepo", username="user", password="pwd"
            )
        assert error_msg == str(excinfo.value)
        exists_calls = [mock.call("/usr/lib/apt/apt-helper")]
        assert exists_calls == m_exists.call_args_list
        expected_path = os.path.join(
            m_temporary_directory.return_value.__enter__.return_value,
            "apt-helper-output",
        )
        apt_helper_call = mock.call(
            [
                "/usr/lib/apt/apt-helper",
                "download-file",
                "http://user:pwd@fakerepo/pool/",
                expected_path,
            ],
            timeout=60,
            retry_sleeps=APT_RETRIES,
        )
        assert [apt_helper_call] == m_subp.call_args_list

    @mock.patch("eaclient.apt.tempfile.TemporaryDirectory")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.os.path.exists", return_value=True)
    def test_errors_on_apt_helper_process_timeout(
        self, m_exists, m_subp, m_temporary_directory
    ):
        """Raise the appropriate user facing error from apt-helper timeout."""
        m_temporary_directory.return_value.__enter__.return_value = (
            "/does/not/exist"
        )
        # Failure apt-helper response
        m_subp.side_effect = subprocess.TimeoutExpired(
            "something timed out", timeout=1000000
        )
        with pytest.raises(exceptions.ELxrProError) as excinfo:
            assert_valid_apt_credentials(
                repo_url="http://fakerepo", username="user", password="pwd"
            )
        error_msg = (
            "Cannot validate credentials for APT repo. Timeout"
            " after {} seconds trying to reach fakerepo.".format(
                APT_HELPER_TIMEOUT
            )
        )
        assert error_msg == excinfo.value.msg
        exists_calls = [mock.call("/usr/lib/apt/apt-helper")]
        assert exists_calls == m_exists.call_args_list
        expected_path = os.path.join(
            m_temporary_directory.return_value.__enter__.return_value,
            "apt-helper-output",
        )
        apt_helper_call = mock.call(
            [
                "/usr/lib/apt/apt-helper",
                "download-file",
                "http://user:pwd@fakerepo/pool/",
                expected_path,
            ],
            timeout=APT_HELPER_TIMEOUT,
            retry_sleeps=APT_RETRIES,
        )
        assert [apt_helper_call] == m_subp.call_args_list


class TestAddAuthAptRepo:
    @pytest.mark.parametrize("series", ("aria"))
    @mock.patch("eaclient.apt.gpg.export_gpg_key")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    @mock.patch("eaclient.apt.assert_valid_apt_credentials")
    @mock.patch("eaclient.system.get_release_info")
    def test_add_auth_apt_repo_writes_sources_file(
        self,
        m_get_release_info,
        m_valid_creds,
        m_get_apt_auth_file,
        m_subp,
        m_gpg_export,
        series,
        tmpdir,
    ):
        """Write a properly configured sources file to repo_filename."""
        repo_file = tmpdir.join("repo.conf").strpath
        auth_file = tmpdir.join("auth.conf").strpath
        m_get_apt_auth_file.return_value = auth_file
        m_subp.return_value = "500 https://mirror.elxr.dev/elxr...", ""
        m_get_release_info.return_value = mock.MagicMock(series=series)

        add_auth_apt_repo(
            repo_filename=repo_file,
            repo_url="http://fakerepo",
            credentials="mycreds",
            suites=(series,),
            components="main",
            keyring_file="keyring",
        )

        if series in SERIES_NOT_USING_DEB822:
            expected_content = (
                "deb http://fakerepo {series} main\n"
                "# deb-src http://fakerepo {series} main\n"
            ).format(series=series)
            src_keyfile = os.path.join(KEYRINGS_DIR, "keyring")
            dest_keyfile = os.path.join(APT_KEYS_DIR, "keyring")
            gpg_export_calls = [mock.call(src_keyfile, dest_keyfile)]
        else:
            expected_content = (
                "# Written by elxr-pro-client\n"
                "Types: deb\n"
                "URIs: http://fakerepo\n"
                "Suites: {series}\n"
                "Components: main\n"
                "Signed-By: /usr/share/keyrings/keyring\n"
            ).format(series=series)
            gpg_export_calls = []

        assert expected_content == system.load_file(repo_file)
        assert gpg_export_calls == m_gpg_export.call_args_list

    @pytest.mark.parametrize("series", ("stable", "bookworm"))
    @mock.patch("eaclient.apt.gpg.export_gpg_key")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    @mock.patch("eaclient.apt.assert_valid_apt_credentials")
    @mock.patch("eaclient.system.get_release_info")
    def test_add_auth_apt_repo_ignores_suites_not_matching_series(
        self,
        m_get_release_info,
        m_valid_creds,
        m_get_apt_auth_file,
        m_subp,
        m_gpg_export,
        series,
        tmpdir,
    ):
        """Skip any apt suites that don't match the current series."""
        repo_file = tmpdir.join("repo.conf").strpath
        auth_file = tmpdir.join("auth.conf").strpath
        m_get_apt_auth_file.return_value = auth_file
        stdout = dedent(
            """\
            500 https://mirror.elxr.dev/elxr {series}/main amd64 \
                        Packages
                release o=. {series},a={series},n={series},\
                        l=. aria,c=main,b=amd64""".format(
                series=series
            )
        )
        m_subp.return_value = stdout, ""
        m_get_release_info.return_value = mock.MagicMock(series=series)

        add_auth_apt_repo(
            repo_filename=repo_file,
            repo_url="http://fakerepo",
            credentials="mycreds",
            suites=(
                "{}-one".format(series),
            ),
            components="main",
            keyring_file="keyring",
        )

        if series in SERIES_NOT_USING_DEB822:
            expected_content = dedent(
                """\
                deb http://fakerepo {series}-one main
                # deb-src http://fakerepo {series}-one main
                deb http://fakerepo {series}-updates main
                # deb-src http://fakerepo {series}-updates main
            """
            ).format(series=series)
        else:
            expected_content = dedent(
                """\
                # Written by elxr-pro-client
                Types: deb
                URIs: http://fakerepo
                Suites: {series}-one
                Components: main
                Signed-By: /usr/share/keyrings/keyring
            """
            ).format(series=series)

        assert expected_content == system.load_file(repo_file)

    @pytest.mark.parametrize("series", ("aria"))
    @mock.patch("eaclient.apt.gpg.export_gpg_key")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    @mock.patch("eaclient.apt.assert_valid_apt_credentials")
    @mock.patch("eaclient.system.get_release_info")
    def test_add_auth_apt_repo_comments_updates_suites_on_non_update_machine(
        self,
        m_get_release_info,
        m_valid_creds,
        m_get_apt_auth_file,
        m_subp,
        m_gpg_export,
        series,
        tmpdir,
    ):
        """Skip any apt suites that don't match the current series."""
        repo_file = tmpdir.join("repo.conf").strpath
        auth_file = tmpdir.join("auth.conf").strpath
        m_get_apt_auth_file.return_value = auth_file
        # apt policy without series-updates enabled
        m_subp.return_value = (
            POST_INSTALL_APT_CACHE_NO_UPDATES.format(series, "test-origin"),
            "",
        )
        m_get_release_info.return_value = mock.MagicMock(series=series)

        add_auth_apt_repo(
            repo_filename=repo_file,
            repo_url="http://fakerepo",
            credentials="mycreds",
            suites=(
                "{}".format(series),
            ),
            components="main",
            keyring_file="keyring",
        )

        if series in SERIES_NOT_USING_DEB822:
            expected_content = dedent(
                """\
                deb http://fakerepo {series}-one main
                # deb-src http://fakerepo {series}-one main
                # deb http://fakerepo {series}-updates main
                # deb-src http://fakerepo {series}-updates main
            """
            ).format(series=series)
        else:
            expected_content = dedent(
                """\
                # Written by elxr-pro-client
                Types: deb
                URIs: http://fakerepo
                Suites: {series}
                Components: main
                Signed-By: /usr/share/keyrings/keyring
            """
            ).format(series=series)

        assert expected_content == system.load_file(repo_file)

    @mock.patch("eaclient.apt.gpg.export_gpg_key")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    @mock.patch("eaclient.apt.assert_valid_apt_credentials")
    @mock.patch(
        "eaclient.system.get_release_info",
        return_value=mock.MagicMock(series="aria-pro"),
    )
    def test_add_auth_apt_repo_writes_username_password_to_auth_file(
        self,
        m_get_release_info,
        m_valid_creds,
        m_get_apt_auth_file,
        m_subp,
        m_gpg_export,
        tmpdir,
    ):
        """Write apt authentication file when credentials are user:pwd."""
        repo_file = tmpdir.join("repo.conf").strpath
        auth_file = tmpdir.join("auth.conf").strpath
        m_get_apt_auth_file.return_value = auth_file
        m_subp.return_value = "500 https://mirror.elxr.dev/elxr...", ""

        add_auth_apt_repo(
            repo_filename=repo_file,
            repo_url="http://fakerepo",
            credentials="user:password",
            suites=("aria-pro",),
            components="main",
            keyring_file="keyring",
        )

        expected_content = (
            "machine fakerepo/ login user password password"
            "{}\n".format(APT_AUTH_COMMENT)
        )
        assert expected_content == system.load_file(auth_file)

    @mock.patch("eaclient.apt.gpg.export_gpg_key")
    @mock.patch("eaclient.system.subp")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    @mock.patch("eaclient.apt.assert_valid_apt_credentials")
    @mock.patch(
        "eaclient.system.get_release_info",
        return_value=mock.MagicMock(series="aria-pro"),
    )
    def test_add_auth_apt_repo_writes_bearer_resource_token_to_auth_file(
        self,
        m_get_release_info,
        m_valid_creds,
        m_get_apt_auth_file,
        m_subp,
        m_gpg_export,
        tmpdir,
    ):
        """Write apt authentication file when credentials are bearer token."""
        repo_file = tmpdir.join("repo.conf").strpath
        auth_file = tmpdir.join("auth.conf").strpath
        m_get_apt_auth_file.return_value = auth_file
        m_subp.return_value = "500 https://mirror.elxr.dev/dev...", ""

        add_auth_apt_repo(
            repo_filename=repo_file,
            repo_url="http://fakerepo/",
            credentials="SOMELONGTOKEN",
            suites=("aria-pro",),
            components="main",
            keyring_file="keyring",
        )

        expected_content = (
            "machine fakerepo/ login bearer password"
            " SOMELONGTOKEN{}\n".format(APT_AUTH_COMMENT)
        )
        assert expected_content == system.load_file(auth_file)


class TestAddAptAuthConfEntry:
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    def test_replaces_old_credentials_with_new(
        self, m_get_apt_auth_file, tmpdir
    ):
        """Replace old credentials for this repo_url on the same line."""
        auth_file = tmpdir.join("auth.conf").strpath
        system.write_file(
            auth_file,
            dedent(
                """\
            machine fakerepo1/ login me password password1
            machine fakerepo/ login old password oldpassword
            machine fakerepo2/ login other password otherpass
        """
            ),
        )

        m_get_apt_auth_file.return_value = auth_file

        add_apt_auth_conf_entry(
            login="newlogin", password="newpass", repo_url="http://fakerepo/"
        )

        content_template = dedent(
            """\
            machine fakerepo1/ login me password password1
            machine fakerepo/ login newlogin password newpass{}
            machine fakerepo2/ login other password otherpass
        """
        )
        expected_content = content_template.format(APT_AUTH_COMMENT)
        assert expected_content == system.load_file(auth_file)

    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    def test_insert_repo_subroutes_before_existing_repo_basepath(
        self, m_get_apt_auth_file, tmpdir
    ):
        """Insert new repo_url before first matching url base path."""
        auth_file = tmpdir.join("auth.conf").strpath
        system.write_file(
            auth_file,
            dedent(
                """\
            machine fakerepo1/ login me password password1
            machine fakerepo/ login old password oldpassword
            machine fakerepo2/ login other password otherpass
        """
            ),
        )

        m_get_apt_auth_file.return_value = auth_file

        add_apt_auth_conf_entry(
            login="new",
            password="newpass",
            repo_url="http://fakerepo/subroute",
        )

        content_template = dedent(
            """\
            machine fakerepo1/ login me password password1
            machine fakerepo/subroute/ login new password newpass{}
            machine fakerepo/ login old password oldpassword
            machine fakerepo2/ login other password otherpass
        """
        )
        expected_content = content_template.format(APT_AUTH_COMMENT)
        assert expected_content == system.load_file(auth_file)


@pytest.fixture(params=(mock.sentinel.default, None, "some_string"))
def remove_auth_apt_repo_kwargs(request):
    """
    Parameterized fixture to generate all permutations of kwargs we need

    Note that this tests three states for keyring_file: using the default,
    explicitly passing None and explicitly passing a string.
    """
    keyring_file = request.param
    kwargs = {}
    if keyring_file != mock.sentinel.default:
        kwargs["keyring_file"] = keyring_file
    return kwargs


@mock.patch("eaclient.apt.system.subp")
@mock.patch("eaclient.apt.remove_repo_from_apt_auth_file")
@mock.patch("eaclient.apt.system.ensure_file_absent")
class TestRemoveAuthAptRepo:
    def test_repo_file_deleted(
        self,
        m_ensure_file_absent,
        _m_remove_repo,
        _m_subp,
        remove_auth_apt_repo_kwargs,
    ):
        """Ensure that repo_filename is deleted, regardless of other params."""
        repo_filename = "/etc/apt/sources.list.d/pro-repofile.list"
        repo_url = mock.sentinel.url

        remove_auth_apt_repo(
            repo_filename, repo_url, **remove_auth_apt_repo_kwargs
        )

        assert mock.call(repo_filename) in m_ensure_file_absent.call_args_list

    def test_old_repo_file_deleted_when_deb822(
        self,
        m_ensure_file_absent,
        _m_remove_repo,
        _m_subp,
        remove_auth_apt_repo_kwargs,
    ):
        repo_filename = "/etc/apt/sources.list.d/pro-repofile.sources"
        repo_url = mock.sentinel.url

        remove_auth_apt_repo(
            repo_filename, repo_url, **remove_auth_apt_repo_kwargs
        )

        assert mock.call(repo_filename) in m_ensure_file_absent.call_args_list
        assert (
            mock.call("/etc/apt/sources.list.d/pro-repofile.list")
            in m_ensure_file_absent.call_args_list
        )

    def test_remove_from_auth_file_called(
        self,
        _m_ensure_file_absent,
        m_remove_repo,
        _m_subp,
        remove_auth_apt_repo_kwargs,
    ):
        """Ensure that remove_repo_from_apt_auth_file is called."""
        repo_filename = "/etc/apt/sources.list.d/pro-repofile.list"
        repo_url = mock.sentinel.url

        remove_auth_apt_repo(
            repo_filename, repo_url, **remove_auth_apt_repo_kwargs
        )

        assert mock.call(repo_url) in m_remove_repo.call_args_list

    def test_keyring_file_deleted_if_given(
        self,
        m_ensure_file_absent,
        _m_remove_repo,
        _m_subp,
        remove_auth_apt_repo_kwargs,
    ):
        """We should always delete the keyring file if it is given"""
        repo_filename = "/etc/apt/sources.list.d/pro-repofile.list"
        repo_url = mock.sentinel.url

        remove_auth_apt_repo(
            repo_filename, repo_url, **remove_auth_apt_repo_kwargs
        )

        keyring_file = remove_auth_apt_repo_kwargs.get("keyring_file")
        if keyring_file:
            assert (
                mock.call(os.path.join(APT_KEYS_DIR, keyring_file))
                in m_ensure_file_absent.call_args_list
            )
        else:
            assert (
                mock.call(keyring_file)
                not in m_ensure_file_absent.call_args_list
            )


class TestRemoveRepoFromAptAuthFile:
    @mock.patch("eaclient.system.ensure_file_absent")
    @mock.patch("eaclient.apt.system.write_file")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    def test_auth_file_doesnt_exist_means_we_dont_remove_or_write_it(
        self, m_get_apt_auth_file, m_write_file, m_ensure_file_absent, tmpdir
    ):
        """If the auth file doesn't exist, we shouldn't do anything to it"""
        m_get_apt_auth_file.return_value = tmpdir.join("nonexistent").strpath

        remove_repo_from_apt_auth_file("http://url")

        assert 0 == m_write_file.call_count
        assert 0 == m_ensure_file_absent.call_count

    @pytest.mark.parametrize("trailing_slash", (True, False))
    @pytest.mark.parametrize(
        "repo_url,auth_file_content",
        (
            ("http://url1", b""),
            ("http://url2", b"machine url2/ login trailing content"),
            ("http://url3", b"machine url3/ login"),
            ("http://url4", b"leading content machine url4/ login"),
            (
                "http://url4",
                b"leading content machine url4/ login trailing content",
            ),
        ),
    )
    @mock.patch("eaclient.system.ensure_file_absent")
    @mock.patch("eaclient.apt.system.write_file")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    def test_file_removal(
        self,
        m_get_apt_auth_file,
        m_write_file,
        m_ensure_file_absent,
        tmpdir,
        trailing_slash,
        repo_url,
        auth_file_content,
    ):
        """Check that auth file is rm'd if empty or contains just our line"""
        auth_file = tmpdir.join("auth_file")
        auth_file.write(auth_file_content, "wb")
        m_get_apt_auth_file.return_value = auth_file.strpath

        remove_repo_from_apt_auth_file(
            repo_url + ("" if not trailing_slash else "/")
        )

        assert 0 == m_write_file.call_count
        assert [
            mock.call(auth_file.strpath)
        ] == m_ensure_file_absent.call_args_list

    @pytest.mark.parametrize("trailing_slash", (True, False))
    @pytest.mark.parametrize(
        "repo_url,before_content,after_content",
        (
            (
                "http://url1",
                b"should not be changed",
                b"should not be changed",
            ),
            (
                "http://url1",
                b"line before\nmachine url1/ login",
                b"line before",
            ),
            ("http://url1", b"machine url1/ login\nline after", b"line after"),
            (
                "http://url1",
                b"line before\nmachine url1/ login\nline after",
                b"line before\nline after",
            ),
            (
                "http://url1",
                b"unicode \xe2\x98\x83\nmachine url1/ login",
                b"unicode \xe2\x98\x83",
            ),
        ),
    )
    @mock.patch("eaclient.system.ensure_file_absent")
    @mock.patch("eaclient.apt.get_apt_auth_file_from_apt_config")
    def test_file_rewrite(
        self,
        m_get_apt_auth_file,
        m_ensure_file_absent,
        tmpdir,
        repo_url,
        before_content,
        after_content,
        trailing_slash,
    ):
        """Check that auth file is rewritten to only exclude our line"""
        auth_file = tmpdir.join("auth_file")
        auth_file.write(before_content, "wb")
        m_get_apt_auth_file.return_value = auth_file.strpath

        remove_repo_from_apt_auth_file(
            repo_url + ("" if not trailing_slash else "/")
        )

        assert 0 == m_ensure_file_absent.call_count
        assert 0o600 == stat.S_IMODE(os.lstat(auth_file.strpath).st_mode)
        assert after_content == auth_file.read("rb")


class TestAptProxyConfig:
    @pytest.mark.parametrize(
        "kwargs, expected_remove_calls, expected_write_calls, expected_out",
        [
            ({}, [mock.call(APT_PROXY_CONF_FILE)], [], ""),
            (
                {"http_proxy": "mock_http_proxy"},
                [],
                [
                    mock.call(
                        APT_PROXY_CONF_FILE,
                        APT_PROXY_CONFIG_HEADER
                        + APT_CONFIG_GLOBAL_PROXY_HTTP.format(
                            proxy_url="mock_http_proxy"
                        ),
                    )
                ],
                messages.SETTING_SERVICE_PROXY_SCOPE.format(scope="global"),
            ),
            (
                {"https_proxy": "mock_https_proxy"},
                [],
                [
                    mock.call(
                        APT_PROXY_CONF_FILE,
                        APT_PROXY_CONFIG_HEADER
                        + APT_CONFIG_GLOBAL_PROXY_HTTPS.format(
                            proxy_url="mock_https_proxy"
                        ),
                    )
                ],
                messages.SETTING_SERVICE_PROXY_SCOPE.format(scope="global"),
            ),
            (
                {
                    "http_proxy": "mock_http_proxy",
                    "https_proxy": "mock_https_proxy",
                },
                [],
                [
                    mock.call(
                        APT_PROXY_CONF_FILE,
                        APT_PROXY_CONFIG_HEADER
                        + APT_CONFIG_GLOBAL_PROXY_HTTP.format(
                            proxy_url="mock_http_proxy"
                        )
                        + APT_CONFIG_GLOBAL_PROXY_HTTPS.format(
                            proxy_url="mock_https_proxy"
                        ),
                    )
                ],
                messages.SETTING_SERVICE_PROXY_SCOPE.format(scope="global"),
            ),
        ],
    )
    @mock.patch("eaclient.system.write_file")
    @mock.patch("eaclient.system.ensure_file_absent")
    def test_setup_apt_proxy_config(
        self,
        m_ensure_file_absent,
        m_util_write_file,
        kwargs,
        expected_remove_calls,
        expected_write_calls,
        expected_out,
        capsys,
        event,
    ):
        setup_apt_proxy(**kwargs)
        assert expected_remove_calls == m_ensure_file_absent.call_args_list
        assert expected_write_calls == m_util_write_file.call_args_list
        out, err = capsys.readouterr()
        assert expected_out == out.strip()
        assert "" == err
