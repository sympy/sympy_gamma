SymPy Gamma
===========

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

Download and unpack most recent Google App Engine SDK for Python from
https://code.google.com/appengine/downloads.html, e.g.::

    $ wget https://storage.googleapis.com/appengine-sdks/featured/google_appengine_1.9.90.zip
    $ unzip google_appengine_1.9.90.zip

On the Mac, it is a disk image with an application, which you should
drag to your Applications folder.  Open the program and install the
symlinks (it should ask you the first time you open the application, but
if it doesn't, choose "Make Symlinks..." from the
GoogleAppEngineLauncher menu).  Note that you will have to do this again
each time you update the AppEngine program.

Then clone sympy_gamma repository::

    $ git clone git://github.com/sympy/sympy_gamma.git
    $ cd sympy_gamma

We use submodules to include external libraries in sympy_gamma::

    $ git submodule init
    $ git submodule update

This is sufficient to clone appropriate repositories in correct versions
into sympy_gamma (see git documentation on submodules for information).

Install Dependencies
--------------------

The project depends on some third-party libraries that are not on the list
of built-in libraries (in app.yaml) bundled with the runtime, to install them
run the following command.::

    pip install -r requirements/requirements.txt -t lib/

Some libraries although available on app engine runtime, but needs to be
installed locally for development.

Ref: https://cloud.google.com/appengine/docs/standard/python/tools/using-libraries-python-27#local_development ::

    pip install -r requirements/local_requirements.txt

Development server
------------------

Now you are ready to run development web server::

    $ ../google_appengine/dev_appserver.py .

On the Mac, just run::

    $ dev_appserver.py .

(make sure you installed the symlinks as described above).

I couldn't figure out how to make it work in the GUI (it won't find the
sympy git submodule).  If you figure out how to do it, please update
this file and send a patch describing how to do it.

This is a local server that runs on port 8080 (use ``--port`` option to
change this). Open a web browser and go to http://localhost:8080. You
should see GUI of SymPy Gamma.

Uploading to GAE (Manually)
---------------------------

Travis-CI is used to deploy automatically to the official server. To upload
the application manually, you need to do a few things.  First, tag the
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
deploying, as ``dev_appserver.py`` can only simulate the App Engine.
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
`https://N-dot-sympy-gamma-tests.appspot.com/`, where `N` is the branch name.
Note that the pull request has to from a branch on this repository, as
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

GAE development server allows to use any Python interpreter, but Google
App Engine uses Python 2.5, so if the default Python isn't 2.5, then make
sure to test your changes to the server part, if it runs properly on 2.5.
Also don't use any modules that aren't supported by GAE. Note that GAE now
supports Python 2.7 and that this is what is currently deployed.

If the App Engine configuration needs to be changed (e.g. to update the
NumPy version), change ``app.yaml.template`` and generate again. The
Travis-CI script uses this to generate and deploy testing/production
versions automatically.


Running Tests
-------------

To be able to run tests, make sure you have testing libraries installed::

    npm install -g casperjs
    pip install nose

To run unit tests::

    PYTHONPATH='.' nosetests app/test -vv

To run PhantomJS Tests::

    casperjs test app/test


Pulling changes
---------------

In projects that don't use submodules, pulling changes boils down to::

    $ git pull origin master

in the simplest case. SymPy Gamma, however, requires additional effort::

    $ git submodule update

The former command assures that if there were any changes to submodules
of the super-project, then those submodules will get updated to new
versions. This is related to the following section. The latter command
regenerates the configuration.

Updating SymPy
--------------

Make sure that you followed instructions above and SymPy's submodule is
properly initialized. Assuming that you are in the directory where SymPy
Gamma was cloned, issue::

    $ cd sympy/
    $ git fetch origin
    $ git checkout sympy-0.7.0
    $ cd ..
    $ git add .
    $ git commit -m "Updated SymPy to version 0.7.0"

Now if you issue::

    $ git show -v

you should get::

    commit 5138e824dc9fd46c243eea2d7c9581a9e58feb08
    Author: Mateusz Paprocki <mattpap@gmail.com>
    Date:   Wed Jul 6 07:45:19 2011 +0200

        Updated SymPy to version 0.7.0

        diff --git a/sympy b/sympy
        index df7a135..c9470ac 160000
        --- a/sympy
        +++ b/sympy
        @@ -1 +1 @@
        -Subproject commit df7a135a4ff7eca361ebbb07ccbeabf8654a8d80
        +Subproject commit c9470ac4f44e7dacfb026cf74529db3ec0822145

This was done for SymPy's version 0.7.0, so in future updates of SymPy replace
0.7.0 with appropriate newer version (e.g. 0.7.1) and you are done (of course
particular SHA signatures will be different in your case). If unsure, refer to
``git help submodule`` or git book: http://book.git-scm.com/5_submodules.html.

Original info
-------------

Originally realized by Ondřej Čertík (a core SymPy developer) as an online
Python notebook and Wolfram|Alpha clone for the Google App Engine that would
showcase SymPy. The notebook was eventually removed in favor of using SymPy
Live.
