from __future__ import print_function
import os
import sys
import platform
from setuptools import setup
from distutils.extension import Extension
from Cython.Build import cythonize

try:
    import numpy  # NOQA
except ImportError:
    print('numpy is required during installation')
    sys.exit(1)

try:
    import scipy  # NOQA
except ImportError:
    print('scipy is required during installation')
    sys.exit(1)

try:
    import Cython  # NOQA
except ImportError:
    print('Cython is required during installation')
    sys.exit(1)

import numpy as np

system = platform.system()
machine = platform.machine().lower()
is_x86 = any(x in machine for x in ("x86_64", "amd64", "x86-64"))

want_avx2 = os.environ.get("SKGGM_AVX2", "").strip() == "1"
want_native = os.environ.get("SKGGM_NATIVE", "").strip() == "1"

include_dirs = [np.get_include()]
extra_compile_args = []
extra_link_args = []
libraries = []
library_dirs = []

if system == 'Darwin':
    # macOS: Accelerate
    extra_compile_args += ['-I/System/Library/Frameworks/vecLib.framework/Headers']
    if 'ppc' in platform.machine():
        extra_compile_args.append('-faltivec')
    extra_link_args += ['-Wl,-framework', '-Wl,Accelerate']

elif system == 'Windows':
    # Windows (MSVC): link MKL via libraries/library_dirs
    extra_compile_args += ['/O2']
    conda_prefix = os.environ.get('CONDA_PREFIX') or os.environ.get('MAMBA_PREFIX')
    if conda_prefix:
        include_dirs += [os.path.join(conda_prefix, 'Library', 'include')]
        library_dirs += [os.path.join(conda_prefix, 'Library', 'lib')]
    libraries += ['mkl_rt']
else:
    # Linux and other Unix
    include_dirs += ['/usr/local/include']
    extra_compile_args += ['-msse2', '-O2', '-fPIC', '-w']
    extra_link_args += ['-llapack']

# Architecture-specific tuning (opt-in via env vars)
if system == 'Windows':
    # MSVC uses /arch:...
    if want_avx2 and is_x86:
        extra_compile_args += ['/arch:AVX2']
else:
    # GCC/Clang flags
    if want_avx2 and is_x86:
        extra_compile_args += ['-mavx2']
    if want_native and is_x86:
        extra_compile_args += ['-march=native']

# Build kwargs depending on platform
ext_kwargs = dict(
    include_dirs=include_dirs,
    extra_compile_args=extra_compile_args,
    language="c++"
)

if system == 'Windows':
    ext_kwargs.update(
        libraries=libraries,
        library_dirs=library_dirs
    )
else:
    ext_kwargs.update(
        extra_link_args=extra_link_args
    )

# pyquic extension
ext_module = Extension(
    name="pyquic.pyquic",  # note: we use ext_package= below
    sources=[
        "inverse_covariance/pyquic/QUIC.cpp",   # renamed from QUIC.C
        "inverse_covariance/pyquic/pyquic.pyx",
    ],
    **ext_kwargs
)

with open('requirements.txt') as f:
    INSTALL_REQUIRES = [l.strip() for l in f.readlines() if l]


setup(
    name='skggm',
    version='0.2.8',
    description='Gaussian graphical models for scikit-learn.',
    author='Jason Laska and Manjari Narayan',
    license='MIT',
    packages=[
        'inverse_covariance',
        'inverse_covariance.profiling',
        'inverse_covariance.pyquic'],
    install_requires=INSTALL_REQUIRES,
    url='https://github.com/skggm/skggm',
    author_email='jlaska@gmail.com',
    ext_package='inverse_covariance',
    ext_modules=cythonize(ext_module),
)
