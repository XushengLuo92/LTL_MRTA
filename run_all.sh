#!/bin/bash

# ------------------------- case 1 ------------------------
#for ((n=1;n<50;n++))
#do
#    /usr/local/Cellar/python@3.8/3.8.6_2/Frameworks/Python.framework/Versions/3.8/bin/python3.8    ./case/case1.py 'f'
#done

# -------------------------- case 2 ------------------------
#for ((n=1;n<21;n++))
#do
#    echo "---------------------------n=${n}-------------------------"
#    /usr/local/Cellar/python@3.8/3.8.6_2/Frameworks/Python.framework/Versions/3.8/bin/python3.8 ./case/case2.py 'f'
#done
# -------------------------- case 3 ------------------------
 for N in 32
 do
     echo "---------------------------N=${N}-------------------------"
     for ((i=1; i<2; i++))
     do
         echo "---------------------------i=${i}-------------------------"
#         /Applications/Polyspace/R2021a/bin/matlab -nodesktop -nosplash -r "cd('/Users/chrislaw/Box Sync/Research/2020_LTL_MRTA_IJRR/cLTL-hierarchical-master/examples'); example_grid_random(${N}, 7, 35, 10);exit"
         for m in 'f'
         do
             echo "---------------------------m=${m}-------------------------"
             /usr/local/Cellar/python@3.8/3.8.6_2/Frameworks/Python.framework/Versions/3.8/bin/python3.8  ./case/case3_2.py ${m} ${N}
         done
     done
 done
