from __future__ import unicode_literals

import configparser
import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import types
import unittest

import mock

from sandboxie import Sandboxie, SandboxieError


class SandboxieUnitTests(unittest.TestCase):
    def setUp(self):
        os.environ = {'WinDir': 'does_not_exist'}
        self.config_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.config_dir, 'Sandboxie.ini')
        with io.open(self.config_path, 'w'):
            pass
        self.sbie = Sandboxie(install_dir=self.config_dir)

    def tearDown(self):
        shutil.rmtree(self.config_dir)

    @property
    def default_start_options(self):
        return set(['/box:{0}'.format(self.sbie.defaultbox),
                    '/silent', '/nosbiectrl'])

    def _build_command_matcher(self, command, options):
        start_exe = os.path.join(self.sbie.install_dir, 'Start.exe')
        return SandboxieStartCommandMatcher(start_exe, command, options)

    def _test_start(self, expected_options, command='test.exe', **startkwargs):
        self.sbie._shell_output = mock.Mock()
        self.sbie.start(command, **startkwargs)
        matcher = self._build_command_matcher(command, expected_options)
        self.sbie._shell_output.assert_called_once(matcher)

    def test_init_raises_when_sandboxie_config_not_found(self):
        try:
            Sandboxie()
        except SandboxieError:
            pass
        else:
            self.fail()

    def test_init_finds_config_in_windows_dir(self):
        os.environ['WinDir'] = self.config_dir
        sbie = Sandboxie()
        self.assertEqual(sbie.config_path, self.config_path)

    def test_init_finds_config_in_install_dir(self):
        sbie = Sandboxie(install_dir=self.config_dir)
        self.assertEqual(sbie.install_dir, self.config_dir)
        self.assertEqual(sbie.config_path, self.config_path)

    def test_init_default_install_dir(self):
        os.environ['WinDir'] = self.config_dir
        sbie = Sandboxie()
        self.assertEqual(sbie.install_dir, r'C:\Program Files\Sandboxie')

    def test_init_install_dir_from_env_var(self):
        os.environ['SANDBOXIE_INSTALL_DIR'] = 'some_dir'
        os.environ['WinDir'] = self.config_dir
        sbie = Sandboxie()
        self.assertEqual(sbie.install_dir, 'some_dir')
        self.assertEqual(sbie.config_path, self.config_path)

    def test_create_sandbox(self):
        os.environ['WinDir'] = self.config_dir
        sbie = Sandboxie()
        sbie.start = mock.Mock()
        sbie.create_sandbox('foo', {'Enabled': 'yes'})

        with io.open(self.config_path, 'r', encoding='utf-16-le') as f:
            config = configparser.ConfigParser()
            config.read_file(f)
            self.assertEqual(config['foo']['Enabled'], 'yes')

        sbie.start.assert_called_once(reload=True)

    def test_destroy_sandbox(self):
        config = configparser.ConfigParser()
        config['sandbox1'] = {'Enabled': 'yes'}
        config['sandbox2'] = {'Enabled': 'no'}

        with io.open(self.config_path, 'w', encoding='utf-16-le') as f:
            config.write(f)

        os.environ['WinDir'] = self.config_dir
        sbie = Sandboxie()
        sbie.start = mock.Mock()
        sbie.destroy_sandbox('sandbox1')

        with io.open(self.config_path, 'r', encoding='utf-16-le') as f:
            config = configparser.ConfigParser()
            config.read_file(f)
            self.assertEqual(config['sandbox2']['Enabled'], 'no')
            try:
                config.get('sandbox1', 'Enabled')
            except configparser.NoSectionError:
                pass
            else:
                self.fail()

        sbie.start.assert_called_once(reload=True)

    def test_reload_delegates_to_start(self):
        self.sbie.start = mock.Mock()
        self.sbie.reload_config()
        self.sbie.start.assert_called_once(reload=True)

    def test_delete_contents_delegates_to_start(self):
        self.sbie = Sandboxie(install_dir=self.config_dir)
        self.sbie.start = mock.Mock()
        self.sbie.delete_contents()
        self.sbie.start.assert_called_once('delete_sandbox_silent', box=None)

    def test_terminate_processes_delegates_to_start(self):
        self.sbie.start = mock.Mock()
        self.sbie.terminate_processes()
        self.sbie.start.assert_called_once(terminate=True, box=None)

    def test_terminate_all_processes_delegates_to_start(self):
        self.sbie.start = mock.Mock()
        self.sbie.terminate_all_processes()
        self.sbie.start.assert_called_once(terminate_all=True)

    def test_running_processes_delegates_to_start(self):
        self.sbie.start = mock.Mock()
        pidlist = '\r\n'.join(('13', '2705', '1336', '2914'))
        self.sbie.start.return_value = pidlist
        self.sbie.running_processes()
        self.sbie.start.assert_called_once(listpids=True, box=None)

    def test_running_processes_returns_pidlist_generator(self):
        self.sbie._shell_output = mock.Mock()
        pidlist = '\r\n'.join(('13', '2705', '1336', '2914'))
        self.sbie._shell_output.return_value = pidlist
        pid_generator = self.sbie.running_processes()
        self.assertEqual(type(pid_generator), types.GeneratorType)
        self.assertEqual(tuple(pid_generator), (13, 2705, 1336, 2914))

    def test_start_command_with_spaces(self):
        self._test_start(self.default_start_options,
                         'ping www.google.com -c 5')

    def test_start_custom_defaultbox(self):
        self.sbie.defaultbox = 'somebox'
        self._test_start(self.default_start_options, 'test.exe')

    def test_start_box_param_overrides_defaultbox(self):
        self.sbie.defaultbox = 'somebox'
        expected_options = self.default_start_options
        expected_options.remove('/box:somebox')
        expected_options.add('/box:anotherbox')
        self._test_start(expected_options, 'test.exe', box='anotherbox')

    def test_start_silent_true(self):
        self._test_start(self.default_start_options, silent=True)

    def test_start_silent_false(self):
        expected_options = self.default_start_options - set(['/silent'])
        self._test_start(expected_options, silent=False)

    def test_start_wait_true(self):
        expected_options = self.default_start_options | set(['/wait'])
        self._test_start(self.default_start_options, wait=True)

    def test_start_wait_false(self):
        self._test_start(self.default_start_options, wait=False)

    def test_start_nosbiectrl_true(self):
        self._test_start(self.default_start_options, nosbiectrl=True)

    def test_start_nosbiectrl_false(self):
        expected_options = self.default_start_options - set(['/nosbiectrl'])
        self._test_start(expected_options, nosbiectrl=False)

    def test_start_elevate_true(self):
        expected_options = self.default_start_options | set(['/elevate'])
        self._test_start(expected_options, elevate=True)

    def test_start_elevate_false(self):
        self._test_start(self.default_start_options, elevate=False)

    def test_start_disable_forced_true(self):
        expected_options = self.default_start_options | set(['/dfp'])
        self._test_start(expected_options, disable_forced=True)

    def test_start_disable_forced_false(self):
        self._test_start(self.default_start_options, disable_forced=False)

    def test_start_reload_ignored_when_command_not_None(self):
        self._test_start(self.default_start_options, reload=True)

    def test_start_reload_not_ignored_when_command_is_none(self):
        expected_options = self.default_start_options | set(['/reload'])
        self._test_start(expected_options, command=None, reload=True)

    def test_start_terminate_ignored_when_command_not_none(self):
        self._test_start(self.default_start_options, terminate=True)

    def test_start_terminate_not_ignored_when_command_is_none(self):
        expected_options = self.default_start_options | set(['/terminate'])
        self._test_start(expected_options, command=None, terminate=True)

    def test_start_terminate_all_ignored_when_command_not_none(self):
        self._test_start(self.default_start_options, terminate_all=True)

    def test_start_terminate_all_not_ignored_when_command_is_none(self):
        expected_options = self.default_start_options | set(['/terminate_all'])
        self._test_start(expected_options, command=None, terminate_all=True)


class SandboxieStartCommandMatcher(object):
    def __init__(self, start_exe, command, options):
        self.start_exe = start_exe
        self.command = command
        self.options = options

    def __eq__(self, command_string):
        import re
        # "(/path/to/Start.exe)" (/option1 /option2 /option3 ...) (command)
        command_string_regex = r'"(.+)" ((?:/[^\s]+\s?)*) (.+)?'
        groups = re.match(command_string_regex, command_string).groups()
        start_exe, options, command = groups[0], groups[1].split(), groups[2]
        return (self.start_exe == start_exe
                and set(self.options) == set(options)
                and self.command == command)

    def __repr__(self):
        return '"{0}" {1} {2}'.format(self.start_exe, self.options,
                                      self.command)


if __name__ == '__main__':
    unittest.main()
