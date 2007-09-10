


import pydoc, os, fabio, inspect, shutil
pydoc.writedoc("fabio")
shutil.copyfile("fabio.html","index.html")
done=[None]
for file in os.listdir(fabio.__path__[0]):
    path = os.path.join(fabio.__path__[0], file)
    modname = inspect.getmodulename(file)
    if modname not in done: # and modname != '__init__':
        pydoc.writedoc("fabio."+modname)
        done.append(modname)
