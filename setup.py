# Copyright 2010 The Fatiando a Terra Development Team
#
# This file is part of Fatiando a Terra.
#
# Fatiando a Terra is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fatiando a Terra is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Fatiando a Terra.  If not, see <http://www.gnu.org/licenses/>.
"""
Build extention modules, package and install Fatiando.
Uses the numpy's extension of distutils to build the f2py extension modules
"""
from os.path import join
import subprocess
from numpy.distutils.core import setup, Extension

# Base paths for extention modules
potdir = join('src', 'potential')
seisdir = join('src', 'seismic')
heatdir = join('src', 'heat')

extmods = [
    Extension('fatiando.potential._prism', sources=[join(potdir, 'prism.c'),
        join(potdir, 'prism.pyf')]),
    Extension('fatiando.potential._talwani', sources=[join(potdir, 'talwani.c'),
        join(potdir, 'talwani.pyf')]),
    Extension('fatiando.potential._polyprism',
        sources=[join(potdir, 'polyprism.c'), join(potdir, 'polyprism.pyf')]),
    Extension('fatiando.potential._transform',
        sources=[join(potdir, 'transform.c'), join(potdir, 'transform.pyf')]),
    Extension('fatiando.seismic._traveltime',
        sources=[join(seisdir, 'traveltime.c'),
                 join(seisdir, 'traveltime.pyf')]),
    Extension('fatiando.heat._climatesignal',
        sources=[join(heatdir, 'climatesignal.c'),
                 join(heatdir, 'climatesignal.pyf')])
    ]

packages = ['fatiando',
            'fatiando.potential',
            'fatiando.seismic',
            'fatiando.heat',
            'fatiando.vis',
            'fatiando.ui',
            'fatiando.mesher',
            'fatiando.inversion']

with open("README.txt") as f:
    long_description = ''.join(f.readlines())

def setrevison(version):
    with open(join('fatiando','version.py'), 'w') as versionfile:
        proc = subprocess.Popen('hg tip', shell=True,
                                stdout=subprocess.PIPE)
        csline, bline = [l.strip() for l in proc.stdout.readlines()[0:2]]
        changeset = csline.split(':')[-1].strip()
        branch = bline.split(':')[-1].strip()
        if branch == 'tip':
            branch = 'default'
        versionfile.write(''.join([
            '"""\n',
            "Version, changeset, and branch information for the current build.",
            '\n"""\n']))
        versionfile.write("version = '%s'\n" % (version))
        versionfile.write("changeset = '%s'\n" % (changeset))
        versionfile.write("branch = '%s'" % (branch))

if __name__ == '__main__':

    version = '0.0.1'
    setrevison(version)
    setup(name='fatiando',
          fullname="Fatiando a Terra",
          description="Geophysical direct and inverse modeling",
          long_description=long_description,
          version=version,
          author="Leonardo Uieda",
          author_email='leouieda at gmail dot com',
          license='GNU LGPL',
          url="www.fatiando.org",
          platforms="Linux",
          scripts=[],
          packages=packages,
          ext_modules=extmods
         )
