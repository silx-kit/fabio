project('FabIO',
  'c', 'cython',
  license: 'MIT',
  meson_version: '>= 0.60',
  version: run_command(['version.py', '--wheel'],
  			           check:true).stdout().strip(),
)


# Seek the backend
if meson.backend() != 'ninja'
  error('Ninja backend required')
endif

# C-compiler
cc = meson.get_compiler('c')
m_dep = cc.find_library('m', required : false)
if m_dep.found()
  add_project_link_arguments('-lm', language : 'c')
endif

# Detect non-MSVC compilers on Windows for both C and C++
if host_machine.system() == 'windows'
  c_id     = cc.get_id()
  #cpp_id   = cpp.get_id()
  # List of ids we accept as “MSVC-compatible”
  acceptable = ['msvc', 'clang-cl']
  warning_msg = '''
    -----------------------------------------------------------------
    Detected @0@ compiler on Windows: @1@
    This project is primarily tested with Microsoft Visual C++.
    If you encounter problems, switch to MSVC or add the needed
    patches for your compiler.
    -----------------------------------------------------------------
  '''
  # C compiler check
  if c_id not in acceptable
    meson.message(warning_msg.format('C', c_id))
  endif
  # C++ compiler check
  #if cpp_id not in acceptable
  #  meson.message(warning_msg.format('C++', cpp_id))
  #endif
  # make it fatal:
  if c_id not in acceptable #or cpp_id not in acceptable
     meson.error('Unsupported compiler on Windows - aborting.')
  endif
endif


# Cython compiler
cy = meson.get_compiler('cython')
if cy.version().version_compare('>=3.1.0')
    add_project_arguments('-Xfreethreading_compatible=true', language : 'cython')
endif

# https://mesonbuild.com/Python-module.html
py_mod = import('python')
py = py_mod.find_installation()
py_dep = py.dependency()

py.install_sources([
    'version.py',
],
  pure: false,    # Will be installed next to binaries
  subdir: 'fabio'  # Folder relative to site-packages to install to
)

subdir('src/fabio')
