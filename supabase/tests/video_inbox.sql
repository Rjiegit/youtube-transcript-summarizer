-- Run in an isolated database after migration; fake test tokens only. Always roll back.
BEGIN;
INSERT INTO video_inbox_private.credentials VALUES
 ('submit', sha256(convert_to(repeat('s', 43), 'UTF8'))),
 ('receiver', sha256(convert_to(repeat('r', 43), 'UTF8')));
SET LOCAL ROLE anon;
DO $$ BEGIN
  BEGIN
    PERFORM public.video_inbox_read(60);
    RAISE EXCEPTION 'missing token unexpectedly accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;
SELECT set_config('request.headers', jsonb_build_object('x-video-inbox-key', repeat('s',43))::text, true);
DO $$ BEGIN
  BEGIN
    PERFORM public.video_inbox_read(60);
    RAISE EXCEPTION 'submitter unexpectedly read queue';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    PERFORM public.video_inbox_delete(1);
    RAISE EXCEPTION 'submitter unexpectedly deleted queue';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    PERFORM public.video_inbox_submit('b1cdf760-37af-4b70-95ac-64484a97da91',
                                     'https://wwwXyoutubeYcom/watch?v=dQw4w9WgXcQ');
    RAISE EXCEPTION 'lookalike hostname accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'invalid submission' THEN RAISE; END IF;
  END;
END $$;
SELECT public.video_inbox_submit('b1cdf760-37af-4b70-95ac-64484a97da91',
                                'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
SELECT set_config('request.headers', jsonb_build_object('x-video-inbox-key', repeat('r',43))::text, true);
DO $$ DECLARE delivery record;
BEGIN
  BEGIN
    PERFORM public.video_inbox_submit('b1cdf760-37af-4b70-95ac-64484a97da91',
                                     'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    RAISE EXCEPTION 'receiver unexpectedly submitted';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  SELECT * INTO delivery FROM public.video_inbox_read(60);
  ASSERT delivery.message->>'version' = '1', 'payload version';
  ASSERT NOT EXISTS (SELECT FROM public.video_inbox_read(60)), 'read must hide message';
  ASSERT public.video_inbox_delete(delivery.msg_id), 'delete delivered message';
  ASSERT NOT EXISTS (SELECT FROM public.video_inbox_read(60)), 'queue must be empty';
  ASSERT NOT has_schema_privilege('anon', 'video_inbox_private', 'USAGE'), 'private credentials';
  ASSERT NOT has_schema_privilege('anon', 'pgmq', 'USAGE'), 'private queue';
END $$;
RESET ROLE;
UPDATE video_inbox_private.credentials SET token_hash = sha256(convert_to(repeat('n',43),'UTF8'))
WHERE purpose = 'receiver';
SET LOCAL ROLE authenticated;
DO $$ BEGIN
  BEGIN
    PERFORM public.video_inbox_read(60);
    RAISE EXCEPTION 'revoked token accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;
SELECT set_config('request.headers', jsonb_build_object('x-video-inbox-key',repeat('n',43))::text,true);
DO $$ BEGIN
  ASSERT NOT EXISTS (SELECT FROM public.video_inbox_read(60)), 'replacement token works';
END $$;
ROLLBACK;
