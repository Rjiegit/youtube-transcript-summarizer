#!/usr/bin/env bash

set -eu

CRON_SCHEDULE="${RSS_MONITOR_CRON_SCHEDULE:-0 * * * *}"
JITTER_SECONDS="${RSS_MONITOR_JITTER_SECONDS:-0}"
CONTAINER_TZ="${TZ:-Asia/Taipei}"
LOG_TAG="[rss-monitor-cron]"

mkdir -p /var/log

if [ "${RSS_MONITOR_ENABLED:-false}" != "true" ]; then
  echo "$LOG_TAG RSS_MONITOR_ENABLED is not true; cron job will not be registered."
  exec tail -f /dev/null
fi

while IFS= read -r line; do
  key="${line%%=*}"
  value="${line#*=}"
  printf 'export %s=%q\n' "$key" "$value"
done <<EOF >/etc/profile.d/container_env.sh
$(printenv)
EOF

chmod 600 /etc/profile.d/container_env.sh

cat > /etc/cron.d/rss-monitor <<EOF
SHELL=/bin/bash
PATH=/opt/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=${CONTAINER_TZ}

${CRON_SCHEDULE} root . /etc/profile.d/container_env.sh && JITTER_SECONDS="${JITTER_SECONDS}" && if [ "\$JITTER_SECONDS" -gt 0 ]; then sleep \$((RANDOM % (JITTER_SECONDS + 1))); fi && cd /usr/src/app && uv run python -m src.apps.workers.rss_monitor --once >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

chmod 0644 /etc/cron.d/rss-monitor

echo "$LOG_TAG registered schedule: ${CRON_SCHEDULE} (jitter=${JITTER_SECONDS}s, tz=${CONTAINER_TZ})"
exec cron -f
