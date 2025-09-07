import unittest

from url_validator import (
    extract_video_id,
    is_valid_youtube_url,
    normalize_youtube_url,
)


class TestURLValidator(unittest.TestCase):
    def test_extract_video_id_variants(self):
        vid = "dQw4w9WgXcQ"
        cases = [
            f"https://www.youtube.com/watch?v={vid}",
            f"http://youtube.com/watch?v={vid}",
            f"https://youtu.be/{vid}",
            f"https://www.youtube.com/embed/{vid}",
            f"  https://youtu.be/{vid}  ",
        ]
        for url in cases:
            self.assertEqual(extract_video_id(url), vid)

    def test_invalid_urls(self):
        for url in [
            "",
            "https://example.com/watch?v=abcdefghi",
            "https://www.youtube.com/watch?v=short",
            "https://youtu.be/too_long_video_id_123",
        ]:
            self.assertFalse(is_valid_youtube_url(url))
            self.assertIsNone(extract_video_id(url))

    def test_normalize(self):
        vid = "dQw4w9WgXcQ"
        self.assertEqual(
            normalize_youtube_url(f"https://youtu.be/{vid}"),
            f"https://www.youtube.com/watch?v={vid}",
        )
        self.assertIsNone(normalize_youtube_url("not a url"))


if __name__ == "__main__":
    unittest.main()

