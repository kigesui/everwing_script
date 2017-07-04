#!/bin/bash

rm -rf temp_img
mkdir temp_img
cd temp_img

DRAGONS=('FC' 'LC' 'NC' 'SC' 'WC')

for d in ${DRAGONS[*]}
do
  for i in {0..30}
  do
    index=`printf %02d $i`
    wget 'https://apps-141184676316522.apps.fbsbx.com/instant-bundle/1174389249249108/1338201689612563/resources/images/game/sidekicks/icons/'$d$index'_T1_icon.png'
  done
done
