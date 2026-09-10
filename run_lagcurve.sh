#!/usr/bin/env bash
cd "$(dirname "$0")"
date -u +%FT%TZ > results/lagcurve_b_start
( ./run.sh lag.py --minutes 45 --lag-minutes 1  --suffix b > results/lagb.log 2>&1 ) &
( ./run.sh lag.py --minutes 45 --lag-minutes 5  --suffix b > results/lag5b.log 2>&1 ) &
( ./run.sh lag.py --minutes 45 --lag-minutes 15 --suffix b > results/lag15b.log 2>&1 ) &
wait
date -u +%FT%TZ > results/lagcurve_b_end
sleep 150
./run.sh suspend.py > results/suspend3.log 2>&1
touch results/LAG_DONE
