#!/bin/sh


#
wget "http://teamsites.risoe.dk/totalcryst/File exchange/fabio_testimages.zip"
# --http-user=username
# --http-password=password

cd testimages

unzip ../fabio_testimages.zip

for name in $(ls *.bz2 ) ; do
    bunzip2 -k $name
    gzip ${name%.bz2}
    bunzip2 -k $name
done

fit2d_12_081_i686_linux2.4.20 -nogr <<EOF
3072
3072
NO
INPUT
ADSC
mb_LP_1_001.img
OUTPUT
"KLORA" 
mb_LP_1_001.edf
QUIT
YES
EOF