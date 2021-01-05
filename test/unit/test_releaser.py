import mock
import pytest
import requests
import subprocess
from homebrew_releaser.releaser import (
    check_required_env_variables,
    commit_formula,
    get_checksum,
    HEADERS,
    make_get_request,
    get_latest_tar_archive,
    run_github_action,
    SUBPROCESS_TIMEOUT,
    write_file
)


@mock.patch('homebrew_releaser.releaser.commit_formula')
@mock.patch('homebrew_releaser.releaser.write_file')
@mock.patch('homebrew_releaser.releaser.generate_formula')
@mock.patch('homebrew_releaser.releaser.get_checksum')
@mock.patch('homebrew_releaser.releaser.get_latest_tar_archive')
@mock.patch('homebrew_releaser.releaser.make_get_request')
@mock.patch('homebrew_releaser.releaser.check_required_env_variables')
def test_run_github_action(mock_check_env_variables, mock_make_get_request, mock_get_latest_tar_archive,
                           mock_get_checksum, mock_generate_formula, mock_write_file, mock_commit_fomrula):
    # TODO: Assert these `called_with` eventually
    run_github_action()
    mock_check_env_variables.assert_called_once()
    assert mock_make_get_request.call_count == 2
    mock_get_latest_tar_archive.assert_called_once()
    mock_get_checksum.assert_called_once()
    mock_generate_formula.assert_called_once()
    mock_write_file.assert_called_once()
    mock_commit_fomrula.assert_called_once()


def test_check_required_env_variables_missing_env_variable():
    with pytest.raises(SystemExit) as error:
        check_required_env_variables()
    assert str(error.value) == 'You must provide all necessary environment variables. Please reference the documentation.'  # noqa


@mock.patch('requests.get')
def test_make_get_request(mock_request):
    url = 'https://api.github.com/repos/Justintime50/homebrew-releaser'
    make_get_request(url, False)
    mock_request.assert_called_once_with(url, headers=HEADERS, stream=False)


@mock.patch('requests.get', side_effect=requests.exceptions.RequestException('mock-error'))
def test_make_get_request_exception(mock_request):
    url = 'https://api.github.com/repos/Justintime50/homebrew-releaser'
    with pytest.raises(SystemExit):
        make_get_request(url, False)


@mock.patch('homebrew_releaser.releaser.write_file')
@mock.patch('homebrew_releaser.releaser.make_get_request')
def test_get_latest_tar_archive(mock_make_get_request, mock_write_file):
    url = 'https://api.github.com/repos/Justintime50/homebrew-releaser/archive/v0.1.0.tar.gz'
    get_latest_tar_archive(url)
    mock_make_get_request.assert_called_once_with(url, True)
    mock_write_file.assert_called_once()  # TODO: Assert `called_with` here instead


def test_write_file():
    with mock.patch('builtins.open', mock.mock_open()):
        write_file('mock-file', 'mock-content', mode='w')


def test_write_file_exception():
    with mock.patch('builtins.open', mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception
        with pytest.raises(SystemExit):
            write_file('mock-file', 'mock-content', mode='w')


@mock.patch('subprocess.check_output')
def test_get_checksum(mock_subprocess):
    # TODO: Mock the subprocess better to ensure it does what it's supposed to
    mock_tar_file = 'mock-file.tar.gz'
    get_checksum(mock_tar_file)
    mock_subprocess.assert_called_once_with(
        f'shasum -a 256 {mock_tar_file}',
        stdin=None,
        stderr=None,
        shell=True,
        timeout=SUBPROCESS_TIMEOUT
    )


@mock.patch('subprocess.check_output', side_effect=subprocess.TimeoutExpired(cmd=subprocess.check_output, timeout=0.1))  # noqa
def test_get_checksum_subprocess_timeout(mock_subprocess):
    mock_tar_file = 'mock-file.tar.gz'
    with pytest.raises(SystemExit):
        get_checksum(mock_tar_file)


@mock.patch('subprocess.check_output', side_effect=subprocess.CalledProcessError(returncode=1, cmd=subprocess.check_output))  # noqa
def test_get_checksum_process_error(mock_subprocess):
    mock_tar_file = 'mock-file.tar.gz'
    with pytest.raises(SystemExit):
        get_checksum(mock_tar_file)


@mock.patch('subprocess.check_output')
def test_commit_formula(mock_subprocess):
    # TODO: Mock the subprocess better to ensure it does what it's supposed to
    owner = 'Justintime50'
    owner_email = 'justin@example.com'
    repo = 'repo-name'
    version = 'v0.1.0'
    commit_formula(owner, owner_email, repo, version)
    mock_subprocess.assert_called_once()  # TODO: Should we assert a `called_with` here since it's SO long?


@mock.patch('subprocess.check_output', side_effect=subprocess.TimeoutExpired(cmd=subprocess.check_output, timeout=0.1))  # noqa
def test_commit_formula_subprocess_timeout(mock_subprocess):
    owner = 'Justintime50'
    owner_email = 'justin@example.com'
    repo = 'repo-name'
    version = 'v0.1.0'
    with pytest.raises(SystemExit):
        commit_formula(owner, owner_email, repo, version)


@mock.patch('subprocess.check_output', side_effect=subprocess.CalledProcessError(returncode=1, cmd=subprocess.check_output))  # noqa
def test_commit_formula_process_error(mock_subprocess):
    owner = 'Justintime50'
    owner_email = 'justin@example.com'
    repo = 'repo-name'
    version = 'v0.1.0'
    with pytest.raises(SystemExit):
        commit_formula(owner, owner_email, repo, version)
