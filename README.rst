SymPy Gamma
===========

.. image:: https://travis-ci.org/sympy/sympy_gamma.svg?branch=master
    :target: https://travis-ci.org/sympy/sympy_gamma

`SymPy Gamma <https://www.sympygamma.com>`_ is a simple web application based
on Google App Engine that executes and displays the results of SymPy
expressions as well as additional related computations, in a fashion similar
to that of Wolfram|Alpha. For instance, entering an integer will display
prime factors, digits in the base-10 expansion, and a factorization
diagram. Entering a function will give its docstring; in general, entering
an arbitrary expression will provide the derivative, integral, series
expansion, plot, and roots.

Google App Engine has intrinsic 30 second request handling limit, so each
evaluation request is a subject to this limit. There are also other limits
related to memory consumption, output size, etc. (see Google App Engine
documentation for details). Each result is evaluated in a separate request,
so (for instance) an integral that takes too long will not prevent the other
information from loading.

Installation
------------

Clone sympy_gamma repository::

    $ git clone git://github.com/sympy/sympy_gamma.git
    $ cd sympy_gamma

Development Server
------------------

To setup the development environment and run the app locally, you
need ``docker`` and ``docker-compose``:

* https://docs.docker.com/get-docker/
* https://docs.docker.com/compose/install/

Now you are ready to run development web server::

    $ docker-compose up

This will build and run the image for app and datastore emulator.

This will spin up a local server that runs on port ``8080``.
Open a web browser and go to http://localhost:8080.
You should see GUI of SymPy Gamma

Note: Make sure to set ``DEBUG = True`` in `settings.py` for serving staticfiles
locally.


Deploying to GAE
----------------

Travis-CI is used to deploy automatically to the official server via Github Releases.
Go to https://github.com/sympy/sympy_gamma/releases and click on create a release and
name the release as version-NN where NN is the release version. After this travis will
automatically release the version NN.

To upload the application manually, you need to do a few things. First, tag the
current commit with the App Engine application version (this is not
necessary unless you are deploying to the official server)::

  $ git tag -a version-42


Then install the Google Cloud SDK for your OS from here:
https://cloud.google.com/sdk/install

This will let you use the "gcloud" CLI. After this configure the CLI to access
the google cloud console for the project::

    $ gcloud init


Assuming that sympy_gamma works properly (also across different mainstream web
browsers), you can upload your changes to Google App Engine, replacing the
<TAGGED_VERSION> with actual version we tagged with::

    $ gcloud app deploy --project sympy-gamma-hrd --no-promote --version <TAGGED_VERSION>

This requires admin privileges to https://sympy-gamma-hrd.appspot.com. If you
don't have access to this App Engine application, but want to test it, see
the instructions in the `Testing on the App Engine`_ section below.

Finally, go to https://NN-dot-sympy-gamma-hrd.appspot.com, where ``NN`` is the
version you just uploaded, and make sure that it works.  If it does, go to
the ``Versions`` section of the sympy_gamma dashboard, and set this as the
new default version.  If there are any issues, you can roll back to the
previous version from this same screen.


Creating Deployment Credentials
-------------------------------

Travis-CI deploys the application using service account credentials. To create a
service account for deployment with suitable permissions, follow these steps:

https://cloud.google.com/solutions/continuous-delivery-with-travis-ci#creating_credentials

These are stored encrypted in the ``client-secret.json.enc`` file in the repository, and are generated
using the Travis command-line tools (client-secret.json is the credentials file for the service account
created int the step above) ::


  travis encrypt-file client-secret.json --add

This also adds the encrypted keys in travis environment variables, which you can
check from here: https://travis-ci.org/github/aktech/sympy_gamma/settings in the
"Environment Variables" section.


Testing on the App Engine
-------------------------

It's usually a good idea to test big changes on the App Engine itself before
deploying, as local environment can only simulate the App Engine.
Currently, there is no testing server set up as there is for SymPy
Live. However, you can set up your own testing server (it's free, though it
requires a cell phone to set up).

Either way, to test, you will need to edit the Project ID in the deploy command
mentioned above with your Project ID and the version you want to deploy to::

    gcloud app deploy --project <your-project-name> --no-promote --version <TAGGED_VERSION>


If you have a test app online, remember to update it every time you update a
pull request, so that others can easily review your work, without even having
to use ``dev_appserver.py``.

Branch builds are automatically deployed by Travis to
`https://<BRANCH-NAME>-dot-sympy-gamma-hrd.appspot.com/`.
Note that the pull request has to be from a branch on this repository, as
forks do not have access to the key to deploy to the app engine.

Development notes
-----------------

Make sure SymPy Gamma works in major mainstream web browsers. This includes
Chrome, Firefox, Safari and Internet Explorer. Be extra cautious about
trailing commas in JavaScript object and arrays. IE doesn't allow them, so
you have to remove them, if any were introduced. Also test on mobile
browsers, such as Safari for iOS and Chrome for Android, on both smartphones
and tablets; Gamma has layouts for phones, tablets, and desktop
browsers. The viewport emulation built into the developer tools of desktop
browsers can help with this testing, but there may be differences that need
to be checked with an actual device. (In Google Chrome, for instance, open
up the developer console, click the gear icon in the lower right, then
select Overrides.)


Running Tests
-------------

To run tests you need to spinup the container as mentioned above
via ``docker-compose`` and run the following command::

    $ docker-compose exec app nosetests app/test -vv
    $ docker-compose exec app casperjs test app/test


Updating SymPy
--------------

Update the version in requirements.txt file.

Original info
-------------

Originally realized by Ondřej Čertík (a core SymPy developer) as an online
Python notebook and Wolfram|Alpha clone for the Google App Engine that would
showcase SymPy. The notebook was eventually removed in favor of using SymPy
Live.
