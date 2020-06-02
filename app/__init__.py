from __future__ import absolute_import
import sys
import os.path

class FakeObject(object):
    def __getattr__(self, key):
        return None

sys.modules['subprocess'] = FakeObject()
sys.path.insert(0, os.path.join(os.getcwd(), 'sympy'))
sys.path.insert(0, os.path.join(os.getcwd(), 'docutils/docutils'))
