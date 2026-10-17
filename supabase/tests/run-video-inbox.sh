#!/usr/bin/env bash
# Only creates/destroys its own isolated container; never connects to a hosted database.
set -euo pipefail
cd "$(dirname "$0")/../.."
container="video-inbox-test-$$"
trap 'docker rm -fv "$container" >/dev/null 2>&1 || true' EXIT
docker run -d --name "$container" --network none -e POSTGRES_HOST_AUTH_METHOD=trust ghcr.io/pgmq/pg18-pgmq:v1.10.0 >/dev/null
for attempt in {1..30}; do
  if docker exec "$container" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$container" psql -U postgres -v ON_ERROR_STOP=1 -c "CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE authenticator; CREATE EXTENSION pgmq; SELECT pgmq.create('existing_queue'); GRANT USAGE ON SCHEMA pgmq TO anon;"
# Existing client grants must reject the migration without any permission changes.
if docker exec -i "$container" psql -U postgres -v ON_ERROR_STOP=1 < supabase/migrations/202610170001_video_inbox.sql; then
  echo 'Expected unsafe existing grants to reject migration' >&2
  exit 1
fi
docker exec -i "$container" psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
DO $$ BEGIN
  ASSERT has_schema_privilege('anon','pgmq','USAGE');
  ASSERT to_regclass('pgmq.q_video_inbox') IS NULL;
  ASSERT to_regclass('pgmq.q_existing_queue') IS NOT NULL;
END $$;
SQL
# Remove only the fixture grant, then test the supported private configuration.
docker exec "$container" psql -U postgres -v ON_ERROR_STOP=1 -c 'REVOKE USAGE ON SCHEMA pgmq FROM anon;'
docker exec -i "$container" psql -U postgres -v ON_ERROR_STOP=1 < supabase/migrations/202610170001_video_inbox.sql
docker exec -i "$container" psql -U postgres -v ON_ERROR_STOP=1 < supabase/tests/video_inbox.sql
echo 'Migration, grant preservation, scoped tokens, revocation and queue delivery passed.'
