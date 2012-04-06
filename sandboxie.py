# coding: utf-8

# Copyright (c) 2012 Gregg Gajic <gregg.gajic@gmail.com> and contributors. See
# AUTHORS.rst for more details.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals

import configparser
import contextlib
import io
import os
import subprocess

import _meta


__version__ = _meta.__version__


class SandboxieError(Exception):
    pass


class Sandboxie(object):
    """An interface to `Sandboxie <http://sandboxie.com>`_."""

    def __init__(self, defaultbox='DefaultBox', install_dir=None):
        """
        :param defaultbox: The default sandbox in which sandboxed commands are
                           executed.
        :param install_dir: The absolute path to the Sandboxie installation
                            directory. If ``None``, it will be set to the
                            value of the ``SANDBOXIE_INSTALL_DIR`` environment
                            variable, or ``C:\Program Files\Sandboxie``,
                            if the environment variable is not set.

        Raises :class:`SandboxieError` if the Sandboxie.ini config file could
        not be located in the following directories:

            #. In the Windows folder: ``C:\WINDOWS`` on most Windows
               installations; ``C:\WINNT`` on Windows 2000
            #. In the Sandboxie installation folder, typically
               ``C:\Program Files\Sandboxie``.
        """
        self.install_dir = install_dir
        if install_dir is None:
            self.install_dir = os.environ.get('SANDBOXIE_INSTALL_DIR',
                                              r'C:\Program Files\Sandboxie')
        self.defaultbox = defaultbox
        self.config_path = self._find_config_path()
        if self.config_path is None:
            raise SandboxieError(('Could not find Sandboxie.ini config. Is '
                                  'Sandboxie installed?'))

    def _find_config_path(self):
        """Returns the absolute path to the Sandboxie.ini config, or ``None``
            if it could not be found.
        """
        for _dir in (os.environ['WinDir'], self.install_dir):
            path = os.path.join(_dir, 'Sandboxie.ini')
            if os.path.exists(path):
                return path
        return None

    def _open_config_file(self, mode='r', encoding='utf-16-le'):
        return io.open(self.config_path, mode, encoding=encoding)

    def _shell_output(self, *args, **kwargs):
        return subprocess.check_output(*args, **kwargs)

    def _write_config(self, config):
        """Writes *config* to ``self.config_path``.

        :param config: a :class:`configparser.ConfigParser` instance of a
            Sandboxie.ini config.
        """
        with self._open_config_file(mode='w') as config_file:
            config.write(config_file)

    @contextlib.contextmanager
    def _modify_config(self):
        """A context manager that yields a :class:`configparser.ConfigParser`
        instance of the parsed Sandboxie.ini config (to allow for
        modifications), then writes the config to ``self.config_path`` upon
        completion of the block.
        """
        config = self.get_config()
        yield config
        self._write_config(config)

    def get_config(self):
        """Returns a :class:`configparser.ConfigParser` instance of the parsed
            Sandboxie.ini config."""
        config = configparser.ConfigParser(strict=False)
        with self._open_config_file(mode='r') as config_file:
            config.read_file(config_file)
        return config

    def create_sandbox(self, box, options):
        """Creates a sandbox named *box*, with a ``dict`` of sandbox
        *options*."""
        with self._modify_config() as config:
            config[box] = options
        self.reload_config()

    def destroy_sandbox(self, box):
        """Destroys the sandbox named *box*. Counterpart to
        :func:`create_sandbox`."""
        with self._modify_config() as config:
            config.remove_section(box)
        self.reload_config()

    def start(self, command=None, box=None, silent=True, wait=False,
              nosbiectrl=True, elevate=False, disable_forced=False,
              reload=False, terminate=False, terminate_all=False,
              listpids=False):
        """Executes *command* under the supervision of Sandboxie by invoking
        `Sandboxie's Start Command Line`_.

        Returns the output of Start.exe on success. Raises
        :class:`subprocess.CalledProcessError` or :class:`WindowsError` on
        failure.

        :param box: The name of the sandbox sandbox to execute the command in.
            If ``None``, the command will be executed in the default sandbox,
            ``self.defaultbox``.
        :param silent: If ``True``, eliminates some pop-up error messages.
        :param wait: If ``True``, wait for the command to finish executing
            before returning.
        :param nosbiectrl: If ``True``, ensures that Sandboxie Control is not
            run before executing *command*.
        :param elevate: If ``True``, allows you to run a program with
            Administrator privileges on a system where User Account Control
            (UAC) is enabled.
        :param disable_forced: If ``True``, runs a program outside the sandbox,
            even if the program is forced.
        :param reload: If ``True``, reloads the Sandboxie config. Only applies
            when *command* is ``None``.
        :param terminate: If ``True``, terminates all sandboxed processes in
            *box*. Only applies when *command* is ``None``.
        :param terminate_all: If ``True``, terminates all processes in **all**
            sandboxes. Only applies when *command* is ``None``.
        :param listpids: If ``True``, return string containing line-separated
            process ids of all sandboxed processes in sandbox *box* Only
            applies when *command* is ``None``.

        .. _Sandboxie's Start Command Line:
            http://www.sandboxie.com/index.php?StartCommandLine
        """
        if box is None:
            box = self.defaultbox
        options = ['/box:{0}'.format(box)]
        if silent:
            options.append('/silent')
        if wait:
            options.append('/wait')
        if nosbiectrl:
            options.append('/nosbiectrl')
        if elevate:
            options.append('/elevate')
        if disable_forced:
            options.append('/dfp')

        if command is None:
            if reload:
                options.append('/reload')
            if terminate:
                options.append('/terminate')
            if terminate_all:
                options.append('/terminate_all')
            if listpids:
                options.append('/listpids')
                # Since Start.exe is not a command-line application, its output
                # does not appear on the command-line unless it is piped into
                # more.
                command = '| more'

        start_exe = os.path.join(self.install_dir, 'Start.exe')
        command = command or ''
        return self._shell_output([start_exe] + options + [command])

    def reload_config(self, **kwargs):
        """Reloads the Sandboxie.ini config."""
        self.start(reload=True, **kwargs)

    def delete_contents(self, box=None, **kwargs):
        """Deletes the contents of sandbox *box*. If *box* is ``None``,
        ``self.defaultbox`` is used.
        """
        self.start('delete_sandbox_silent', box=None, **kwargs)

    def terminate_processes(self, box=None, **kwargs):
        """Terminates all processes running in sandbox *box* If *box* is
        ``None``, ``self.defaultbox`` is used."""
        self.start(terminate=True, box=box, **kwargs)

    def terminate_all_processes(self, **kwargs):
        """Terminates all processes running in **all** sandboxes."""
        self.start(terminate_all=True, **kwargs)

    def running_processes(self, box=None, **kwargs):
        """Returns a generator of integer process ids for each process running
        in sandbox *box*. If *box* is ``None``, ``self.defaultbox`` is used.
        """
        output = self.start(listpids=True, box=box, wait=True, **kwargs)
        return (int(pid) for pid in output.split())
