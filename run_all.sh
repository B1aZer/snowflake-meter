#!/usr/bin/env bash
# Both experiments, detached. Meter patterns run in sequence; the lag heartbeat runs alongside.
cd "$(dirname "$0")"; mkdir -p results
( ./run.sh lag.py --minutes 120 > results/lag.log 2>&1 ) &
( for p in batched tight spread warm; do ./run.sh meter.py --pattern $p --n 40 > results/meter_$p.log 2>&1; done; touch results/METER_DONE ) &
wait
touch results/ALL_DONE
