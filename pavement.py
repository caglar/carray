########################################################################
#
#       License: BSD
#       Created: December 14, 2010
#       Author:  Francesc Alted - francesc@continuum.io
#
########################################################################

import sys, os, glob
import textwrap
import subprocess

from paver.easy import *
from paver.setuputils import setup, install_distutils_tasks
from distutils.core import Extension
from distutils.dep_util import newer

# Some functions for showing errors and warnings.
def _print_admonition(kind, head, body):
    tw = textwrap.TextWrapper(
        initial_indent='   ', subsequent_indent='   ')

    print(".. %s:: %s" % (kind.upper(), head))
    for line in tw.wrap(body):
        print line

def exit_with_error(head, body=''):
    _print_admonition('error', head, body)
    sys.exit(1)

def print_warning(head, body=''):
    _print_admonition('warning', head, body)

def check_import(pkgname, pkgver):
    try:
        mod = __import__(pkgname)
    except ImportError:
            exit_with_error(
                "You need %(pkgname)s %(pkgver)s or greater to run carray!"
                % {'pkgname': pkgname, 'pkgver': pkgver} )
    else:
        if mod.__version__ < pkgver:
            exit_with_error(
                "You need %(pkgname)s %(pkgver)s or greater to run carray!"
                % {'pkgname': pkgname, 'pkgver': pkgver} )

    print ( "* Found %(pkgname)s %(pkgver)s package installed."
            % {'pkgname': pkgname, 'pkgver': mod.__version__} )
    globals()[pkgname] = mod


########### Check versions ##########

# Check for Python
if not (sys.version_info[0] >= 2 and sys.version_info[1] >= 6):
    exit_with_error("You need Python 2.6 or greater to install carray!")

# The minimum version of Cython required for generating extensions
min_cython_version = '0.16'
# The minimum version of NumPy required
min_numpy_version = '1.5'
# The minimum version of Numexpr (optional)
min_numexpr_version = '1.4.1'

# Check for Cython
cython = False
try:
    from Cython.Compiler.Main import Version
    if Version.version < min_cython_version:
        cython = False
    else:
        cython = True
except:
    pass

# Check for NumPy
check_import('numpy', min_numpy_version)

# Check for Numexpr
numexpr_here = False
try:
    import numexpr
except ImportError:
    print_warning(
        "Numexpr is not installed.  For faster carray operation, "
        "please consider installing it.")
else:
    if numexpr.__version__ >= min_numexpr_version:
        numexpr_here = True
        print ( "* Found %(pkgname)s %(pkgver)s package installed."
                % {'pkgname': 'numexpr', 'pkgver': numexpr.__version__} )
    else:
        print_warning(
            "Numexpr %s installed, but version is not >= %s.  "
            "Disabling support for it." % (
            numexpr.__version__, min_numexpr_version))

########### End of version checks ##########

# carray version
VERSION = open('VERSION').read().strip()
# Create the version.py file
open('carray/version.py', 'w').write('__version__ = "%s"\n' % VERSION)


# Global variables
CFLAGS = os.environ.get('CFLAGS', '').split()
LFLAGS = os.environ.get('LFLAGS', '').split()
lib_dirs = []
libs = []
inc_dirs = ['carray', 'blosc']
# Include NumPy header dirs
from numpy.distutils.misc_util import get_numpy_include_dirs
inc_dirs.extend(get_numpy_include_dirs())
cython_pyxfiles = glob.glob('carray/*.pyx')
cython_cfiles = [fn.split('.')[0] + '.c' for fn in cython_pyxfiles]
blosc_files = glob.glob('blosc/*.c')

# Handle --lflags=[FLAGS] --cflags=[FLAGS]
args = sys.argv[:]
for arg in args:
    if arg.find('--lflags=') == 0:
        LFLAGS = arg.split('=')[1].split()
        sys.argv.remove(arg)
    elif arg.find('--cflags=') == 0:
        CFLAGS = arg.split('=')[1].split()
        sys.argv.remove(arg)

# Add -msse2 flag for optimizing shuffle in Blosc
if os.name == 'posix':
    CFLAGS.append("-msse2")


# Paver tasks
@task
def cythonize():
    for fn in glob.glob('carray/*.pyx'):
         dest = fn.split('.')[0] + '.c'
         if newer(fn, dest):
             if not cython:
                 exit_with_error(
                     "Need Cython >= %s to generate extensions."
                     % min_cython_version)
             sh("cython " + fn)

@task
@needs('html', 'setuptools.command.sdist')
def sdist():
    """Generate a source distribution for the package."""
    pass

@task
@needs(['cythonize', 'setuptools.command.build'])
def build():
     pass

@task
@needs(['cythonize', 'setuptools.command.build_ext'])
def build_ext():
     pass

@task
@needs('paver.doctools.html')
def html(options):
    """Build the docs in HTML format."""
    destdir = path("doc/html")
    destdir.rmtree()
    builtdocs = path("doc") / options.builddir / "html"
    builtdocs.move(destdir)

@task
def pdf(options):
    """Build the docs in PDF format."""
    dest = path("doc") / "carray-manual.pdf"
    sh("cd doc; make latexpdf")
    builtdocs = path("doc") / options.builddir / "latex" / "carray.pdf"
    builtdocs.move(dest)


# Options for Paver tasks
options(

    sphinx = Bunch(
        docroot = "doc",
        builddir = "_build"
    ),

)


classifiers = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
Intended Audience :: Information Technology
Intended Audience :: Science/Research
License :: OSI Approved :: BSD License
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""

# Package options
setup(
    name = 'carray',
    version = VERSION,
    description = "A chunked data container that can be compressed in-memory.",
    long_description = """\
carray is a chunked container for numerical data.  Chunking allows for
efficient enlarging/shrinking of data container.  In addition, it can
also be compressed for reducing memory needs.  The compression process
is carried out internally by Blosc, a high-performance compressor that
is optimized for binary data.""",
    classifiers = filter(None, classifiers.split("\n")),
    author = 'Francesc Alted',
    author_email = 'francesc@continuum.io',
    url = "https://github.com/FrancescAlted/carray",
    license = 'http://www.opensource.org/licenses/bsd-license.php',
    download_url = "http://carray.pytables.org/download/carray-%s/carray-%s.tar.gz" % (VERSION, VERSION),
    platforms = ['any'],
    ext_modules = [
    Extension( "carray.carrayExtension",
               include_dirs=inc_dirs,
               sources = cython_cfiles + blosc_files,
               depends = ["carray/definitions.pxd"] + blosc_files,
               library_dirs=lib_dirs,
               libraries=libs,
               extra_link_args=LFLAGS,
               extra_compile_args=CFLAGS ),
    ],
    packages = ['carray', 'carray.tests'],
    include_package_data = True,

)

