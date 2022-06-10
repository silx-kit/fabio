project('FabIO',
  'c', 'cpp', 'cython',
  version: '0.14.0',
  license: 'MIT',
  meson_version: '>= 0.60',
)

cc = meson.get_compiler('c')
cpp = meson.get_compiler('cpp')

m_dep = cc.find_library('m', required : false)
if m_dep.found()
  add_project_link_arguments('-lm', language : 'c')
endif

cython = find_program('cython')

# https://mesonbuild.com/Python-module.html
py_mod = import('python')
py = py_mod.find_installation()
py_dep = py.dependency()


#generate_version = custom_target(
#  'generate-version',
#  input: 'version.py',
#  command: [py3, '@INPUT@'],
#)

subdir('fabio')
