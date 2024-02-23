#!/bin/bash
for(( i=0; i<=2000; i++ ))
do
let start=$i*0x1000
echo "erase segment: $start"
sudo sunxi-fel -p clear $start 0x1000
done 
