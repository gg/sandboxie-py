# coding: utf-8

from __future__ import unicode_literals

import sandboxie
import subprocess
import time
import unittest


class SandboxieIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.sbie = sandboxie.Sandboxie()
        self.sbie.create_sandbox(box='foo', options={'Enabled': 'yes'})

    def tearDown(self):
        try:
            self.sbie.delete_contents(box='foo')
            self.sbie.destroy_sandbox(box='foo')
        except subprocess.CalledProcessError:
            pass

    def test_start_command_fails_due_to_non_existent_sandbox(self):
        try:
            self.sbie.start('notepad.exe', box='DOES_NOT_EXIST', wait=False)
        except subprocess.CalledProcessError:
            pass
        else:
            self.fail()

    def test_start_command_fails_due_to_invalid_command(self):
        try:
            self.sbie.start('asdaklwjWLAL.asjd', box='foo', wait=False)
        except subprocess.CalledProcessError:
            pass
        else:
            self.fail()

    def test_launch_notepad(self):
        self.sbie.start('notepad.exe', box='foo', wait=False)
        assert(len(list(self.sbie.running_processes(box='foo'))) > 0)
        self.sbie.terminate_processes(box='foo')


if __name__ == '__main__':
    unittest.main()
