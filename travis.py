import nose
import os
import os.path
import subprocess

if __name__ == '__main__':
    print("Running PhantomJS Tests")
    gamma_directory = os.path.dirname(os.path.realpath(__file__))
    subprocess.call(['casperjs', 'test', os.path.join(gamma_directory, 'app/test/')])

    print
    print("Running Python Unittests")
    nose.main(config=nose.config.Config(verbosity=2))
