py = import('python').find_installation()
dep_py = py.dependency()

#py.extension_module(
#        "cf_io",
#        "cf_io.pyx", "src/columnfile.c",
#        include_dirs=["include", numpy.get_include()],

#py.extension_module(
#        "byte_offset",
#        sources=["byte_offset.pyx"],
#        include_dirs=[numpy.get_include()],

#py.extension_module(
#        "mar345_IO",
#        sources=["mar345_IO.pyx", os.path.join("src", "ccp4_pack.c")],
#        include_dirs=["include", numpy.get_include()],

py.extension_module(
        '_cif',
        '_cif.pyx',
        dependencies : dep_py
        )

py.extension_module(
        '_agi_bitfield',
        '_agi_bitfield.pyx',
        dependencies : dep_py
        )

#py.extension_module(
#        "dense",
#        "dense.pyx",
#        include_dirs=[numpy.get_include()],


