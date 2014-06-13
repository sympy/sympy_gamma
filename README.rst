SymPy Gamma
===========

`SymPy Gamma <http://www.sympygamma.com>`_ is a simple web application based
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
http://code.google.com/appengine/downloads.html, e.g.::

    $ wget http://googleappengine.googlecode.com/files/google_appengine_1.5.1.zip
    $ unzip google_appengine_1.5.1.zip

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

Generate a configuration file for App Engine (needed to run the development
web server)::

  $ python deploy.py --generate-only --generate-test 1000

(the number does not matter unless you are deploying, see below). **DO not**
commit the generated ``app.yaml`` file.

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

Second, you need to generate an ``app.yaml`` (App Engine configuration) file
using ``deploy.py``::

  $ python deploy.py --generate-only --generate-production

The script will determine the version from the tag; it can also be manually
specified (``--generate-production VERSION_NUMBER``). You will also want to
change the application name if you are not deploying to the test
application. **DO not** commit the generated ``app.yaml`` file.

Second, you need to go to the ``Versions`` section of the
sympy_gamma dashboard at appspot.com and delete the oldest version, as we
can only upload ten versions at a time.

Assuming that sympy_gamma works properly (also across different mainstream web
browsers), you can upload your changes to Google App Engine::

    $ ../appcfg.py update .

Or, in Mac OS X, just open the GoogleAppEngineLauncher program, add the
project if you haven't already, and click "Deploy" in the toolbar.  And then
it should just work (follow the log that comes up to see.

This requires admin privileges to http://sympy-gamma-hrd.appspot.com. If you
don't have access to this App Engine application, but want to test it, see
the instructions in the `Testing on the App Engine`_ section below.

The deploy script can generate the configuration and deploy in one step if
given the App Engine SDK location::

  $ SDK_LOCATION=/path/to/sdk python deploy.py --generate-production

Finally, go to http://NN.sympy-gamma-hrd.appspot.com, where ``NN`` is the
version you just uploaded, and make sure that it works.  If it does, go to
the ``Versions`` section of the sympy_gamma dashboard, and set this as the
new default version.  If there are any issues, you can roll back to the
previous version from this same screen.

Generating a Deployment Key
---------------------------

Travis-CI deploys the application using OAuth credentials. These are stored
encrypted in the ``env`` section of ``.travis.yml``, and are generated using
the Travis command-line tools::

  travis encrypt 'OAUTH_REFRESH_TOKEN=TOKEN' -r sympy/sympy_gamma

The token is found in the JSON file ``$HOME/.appcfg_oauth2_tokens`` under
the key ``"refresh_token"``. This file is created after manually deploying
(or running any other command) using OAuth authorization::

  $ ../appcfg.py update --oauth2 .

Testing on the App Engine
-------------------------

It's usually a good idea to test big changes on the App Engine itself before
deploying, as ``dev_appserver.py`` can only simulate the App Engine.
Currently, there is no testing server set up as there is for SymPy
Live. However, you can set up your own testing server (it's free, though it
requires a cell phone to set up).

Either way, to test, you will need to edit the ``app.yaml`` file.  You should
edit the first line, ``application``, to the name of the testing application
(like ``sympy-gamma-tests``), and the second line to the version number you
want to use.

You should not actually commit ``app.yaml``, as it is generated by the
deploy script.  If you later want to commit an actual change to the
generated ``app.yaml`` (e.g., to modify some metadata), you should edit and
commit changes to ``app.yaml.template``.

If you have a test app online, remember to update it every time you update a
pull request, so that others can easily review your work, without even having
to use ``dev_appserver.py``.

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

Pulling changes
---------------

In projects that don't use submodules, pulling changes boils down to::

    $ git pull origin master

in the simplest case. SymPy Gamma, however, requires additional effort::

    $ git submodule update
    $ python deploy.py --generate-only --generate-test 1000

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
