import nose
import os
import sys
import os.path
import subprocess

if __name__ == '__main__':
    print("Running PhantomJS Tests")
    gamma_directory = os.path.dirname(os.path.realpath(__file__))
    returncode = subprocess.call(['casperjs', 'test', os.path.join(gamma_directory, 'app/test/')])

    print
    print("Running Python Unittests")
    result = nose.run(config=nose.config.Config(verbosity=2))

    if returncode != 0 or not result:
        print("Tests failed.")
        if returncode != 0:
            print("\tPhantomJS: FAIL")
        if not result:
            print("\tPython: FAIL")
        sys.exit(1)
    else:
        print("Tests succeeded.")
