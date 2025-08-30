import unittest
import streamlit as st
from queue_state import init_dynamic_queue_state, get_queue_state
from dynamic_queue_manager import DynamicQueueManager, configure_providers

# Fake providers for isolated deterministic tests
class FakeDownloader:
    def __init__(self, url):
        self.url = url
    def download(self):
        return {"path": f"data/{self.url.split('=')[-1]}.mp4"}

class FakeTranscriber:
    def __init__(self, model_size="tiny"):
        self.model_size = model_size
    def transcribe(self, file_path):
        return f"TRANSCRIPT of {file_path}"

class FakeSummarizer:
    def summarize(self, title, text):
        return f"SUMMARY:{title}"    

class TestDynamicQueue(unittest.TestCase):
    def setUp(self):
        # Reset state for each test
        if 'dynamic_queue' in st.session_state:
            del st.session_state['dynamic_queue']
        init_dynamic_queue_state()
        configure_providers(downloader=FakeDownloader, transcriber=FakeTranscriber, summarizer=FakeSummarizer)

    def test_add_url_and_no_duplicate(self):
        ok, msg = DynamicQueueManager.add_url('https://youtu.be/ABCDEFGHIJK')
        self.assertTrue(ok)
        ok2, msg2 = DynamicQueueManager.add_url('https://youtu.be/ABCDEFGHIJK')
        self.assertFalse(ok2)
        dq = get_queue_state()
        self.assertEqual(len(dq['task_queue']), 1)

    def test_processing_loop_success(self):
        DynamicQueueManager.add_url('https://youtu.be/ABCDEFGHIJK')
        dq = get_queue_state()
        DynamicQueueManager.start_processing()
        # call loop manually (simulate reruns)
        for _ in range(3):
            DynamicQueueManager.processing_loop()
        self.assertEqual(dq['stats']['completed'], 1)
        self.assertFalse(dq['is_processing'])

    def test_retry_failed_task(self):
        # Inject a failing summarizer
        class FailingSummarizer:
            def summarize(self, title, text):
                raise RuntimeError('boom')
        configure_providers(summarizer=FailingSummarizer)
        DynamicQueueManager.add_url('https://youtu.be/ABCDEFGHIJK')
        dq = get_queue_state()
        DynamicQueueManager.start_processing()
        DynamicQueueManager.processing_loop()
        self.assertEqual(dq['stats']['failed'], 1)
        tid = dq['task_queue'][0]['id']
        self.assertTrue(DynamicQueueManager.retry_task(tid))
        self.assertEqual(dq['task_queue'][0]['status'], 'waiting')

if __name__ == '__main__':
    unittest.main()
