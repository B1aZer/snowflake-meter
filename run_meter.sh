#!/usr/bin/env bash
cd "$(dirname "$0")"; mkdir -p results
for p in batched tight spread warm; do ./run.sh meter.py --pattern $p --n 40 > results/meter_$p.log 2>&1; done
touch results/METER_DONE
