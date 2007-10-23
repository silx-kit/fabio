#!/usr/bin/env sh

#wget "http://teamsites.risoe.dk/totalcryst/File exchange/fabio_testimages.zip"
cd testimages
#unzip ../fabio_testimages.zip
for name in $(ls *.bz2 ) ; do
    bunzip2 -k $name
    gzip ${name%.bz2}
    bunzip2 -k $name
done
