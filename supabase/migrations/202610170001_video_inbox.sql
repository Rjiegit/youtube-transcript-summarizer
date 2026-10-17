-- Run as postgres. Dedicated project recommended; pgmq is never an exposed API schema.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgmq;
SELECT pgmq.create('video_inbox');
-- Fail closed rather than revoke permissions used by unrelated queues.
-- Only a private pgmq installation is supported; use a dedicated project otherwise.
DO $$
DECLARE client text;
BEGIN
  FOREACH client IN ARRAY ARRAY['anon', 'authenticated'] LOOP
    IF has_schema_privilege(client, 'pgmq', 'USAGE') OR
       has_table_privilege(client, 'pgmq.q_video_inbox', 'SELECT,INSERT,UPDATE,DELETE') OR
       (to_regnamespace('pgmq_public') IS NOT NULL AND
        has_schema_privilege(client, 'pgmq_public', 'USAGE')) THEN
      RAISE EXCEPTION 'Unsafe existing queue grants; use a dedicated private project. No grants were changed.';
    END IF;
  END LOOP;
END $$;

CREATE SCHEMA video_inbox_private;
REVOKE ALL ON SCHEMA video_inbox_private FROM PUBLIC, anon, authenticated;
CREATE TABLE video_inbox_private.credentials (
  purpose text PRIMARY KEY CHECK (purpose IN ('submit', 'receiver')),
  token_hash bytea NOT NULL CHECK (octet_length(token_hash) = 32)
);
REVOKE ALL ON video_inbox_private.credentials FROM PUBLIC, anon, authenticated;

CREATE FUNCTION video_inbox_private.require_token(purpose text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE supplied text;
BEGIN
  supplied := coalesce(nullif(current_setting('request.headers', true), ''), '{}')::jsonb ->> 'x-video-inbox-key';
  IF supplied IS NULL OR length(supplied) < 43 OR length(supplied) > 256 OR NOT EXISTS (
    SELECT FROM video_inbox_private.credentials c
    WHERE c.purpose = require_token.purpose
      AND c.token_hash = sha256(convert_to(supplied, 'UTF8'))
  ) THEN
    RAISE insufficient_privilege USING MESSAGE = 'Inbox access denied';
  END IF;
END $$;
REVOKE ALL ON FUNCTION video_inbox_private.require_token(text) FROM PUBLIC, anon, authenticated;

CREATE FUNCTION public.video_inbox_submit(submission_id uuid, video_url text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  PERFORM video_inbox_private.require_token('submit');
  IF submission_id IS NULL OR video_url IS NULL OR
    video_url !~ '^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$' THEN
    RAISE EXCEPTION 'invalid submission';
  END IF;
  PERFORM pgmq.send('video_inbox', jsonb_build_object(
    'version', 1, 'submission_id', submission_id, 'url', video_url));
END $$;

CREATE FUNCTION public.video_inbox_read(visibility_seconds integer DEFAULT 60)
RETURNS SETOF pgmq.message_record LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  PERFORM video_inbox_private.require_token('receiver');
  IF visibility_seconds < 30 OR visibility_seconds > 300 OR visibility_seconds IS NULL THEN
    RAISE EXCEPTION 'invalid visibility timeout';
  END IF;
  RETURN QUERY SELECT * FROM pgmq.read('video_inbox', visibility_seconds, 1);
END $$;

CREATE FUNCTION public.video_inbox_delete(message_id bigint)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  PERFORM video_inbox_private.require_token('receiver');
  RETURN pgmq.delete('video_inbox', message_id);
END
$$;

REVOKE ALL ON FUNCTION public.video_inbox_submit(uuid, text) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.video_inbox_read(integer) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.video_inbox_delete(bigint) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.video_inbox_submit(uuid, text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.video_inbox_read(integer), public.video_inbox_delete(bigint) TO anon, authenticated;
COMMIT;
