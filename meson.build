project('FabIO',
  'c', 'cython',
  license: 'MIT',
  meson_version: '>= 0.60',
  version: run_command('version.py',
  			           check:true).stdout().strip(),
)

cc = meson.get_compiler('c')

m_dep = cc.find_library('m', required : false)
if m_dep.found()
  add_project_link_arguments('-lm', language : 'c')
endif

# https://mesonbuild.com/Python-module.html
py_mod = import('python')
py = py_mod.find_installation()
py_dep = py.dependency()

py.install_sources(
  ['version.py'],
  #rename: ['_version.py'],
  pure: false,    # Will be installed next to binaries
  subdir: 'fabio'  # Folder relative to site-packages to install to
)

subdir('fabio')
