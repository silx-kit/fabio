py.install_sources(['__init__.py', ],
  pure: false,
  subdir: 'fabio/ext/'
)

py.extension_module('cf_io',
        'cf_io.pyx', 'src/columnfile.c',
        dependencies : py_dep,
        include_directories : ['include'],
        install: true,
        subdir: 'fabio/ext',
        )

py.extension_module('byte_offset',
        'byte_offset.pyx',
        dependencies : py_dep,
        install: true,
        subdir: 'fabio/ext',
        )

py.extension_module('mar345_IO',
        'mar345_IO.pyx', 
        'src/ccp4_pack.c',
        dependencies : py_dep,
        install: true,
        subdir: 'fabio/ext',
        include_directories : ['include'],
        )

py.extension_module('_cif',
        '_cif.pyx',
        dependencies : py_dep,
        install: true,
        subdir: 'fabio/ext',
        )

py.extension_module( '_agi_bitfield',
        '_agi_bitfield.pyx',
        dependencies : py_dep,
        install: true,
        subdir: 'fabio/ext',
        )

py.extension_module( 'dense',
        'dense.pyx',
        dependencies : py_dep,
        install: true,
        subdir: 'fabio/ext',
        )


