#!/usr/bin/env bash
# Wait for both experiments, then stop all billing objects and write the report.
cd "$(dirname "$0")"
while [ ! -f results/METER_DONE ] || pgrep -f 'lag.py' >/dev/null; do sleep 60; done
sleep 120   # let the last metering rows land
./run.sh suspend.py > results/suspend.log 2>&1
./run.sh report.py > results/REPORT.md 2>&1
touch results/REPORT_DONE
