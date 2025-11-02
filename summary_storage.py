import os
from notion_client import Client
from dotenv import load_dotenv
from logger import logger
import time
import random

from database.notion_utils import (
    NOTION_RICH_TEXT_LIMIT,
    build_rich_text_array,
    chunk_text,
)

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from test_sample_manager import TestSampleManager
except ImportError:
    TestSampleManager = None


class SummaryStorage:
    def __init__(self):
        pass

    def save(self, title, text, model, url):
        # 檢查是否為測試模式
        if self._is_test_mode(title, text, url):
            return self._mock_save(title, text, model, url)

        return self.save_with_notion(title, text, model, url)

    def _is_test_mode(self, title, text, url):
        """檢測是否為測試模式"""
        # 方法 1: 檢查 Streamlit session_state
        if (
            st
            and hasattr(st, "session_state")
            and st.session_state.get("test_mode", False)
        ):
            return True

        # 方法 2: 檢查 URL 中的測試標記
        if url and any(marker in url for marker in ["test_", "test/", "v=test"]):
            return True

        # 方法 3: 檢查文字內容中的測試標記
        if text and any(
            marker in text for marker in ["[測試模式]", "[mock]", "[test]"]
        ):
            return True

        # 方法 4: 檢查標題中的測試標記
        if title and any(marker in title for marker in ["測試", "test", "mock"]):
            return True

        return False

    def _mock_save(self, title, text, model, url):
        """模擬存儲過程"""
        logger.info("[測試模式] 模擬 Notion 存儲...")

        # 檢查 TestSampleManager 是否可用
        if TestSampleManager is None:
            logger.warning("[測試模式] TestSampleManager 不可用，使用基本模擬")
            time.sleep(random.uniform(0.3, 0.8))
            mock_page_id = f"mock_page_{random.randint(100000, 999999)}"
            logger.info(f"[測試模式] 模擬存儲完成！頁面ID: {mock_page_id}")
            return {"page_id": mock_page_id, "success": True}

        # 模擬處理時間
        time.sleep(random.uniform(0.3, 0.8))

        # 檢查是否要模擬錯誤
        sample_manager = TestSampleManager()
        if sample_manager.simulate_error():
            error_msg = sample_manager.get_random_error_message()
            logger.error(f"[測試模式] 模擬 Notion 存儲錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")

        # 模擬成功的存儲結果
        mock_page_id = f"mock_page_{random.randint(100000, 999999)}"
        text_chunks = len(self.split_text(text, limit=NOTION_RICH_TEXT_LIMIT))

        logger.info(f"[測試模式] 模擬 Notion 存儲完成")
        logger.info(f"[測試模式] 模擬頁面ID: {mock_page_id}")
        logger.info(f"[測試模式] 文字分塊數: {text_chunks}")
        logger.info(f"[測試模式] 標題: {title[:50]}{'...' if len(title) > 50 else ''}")
        logger.info(f"[測試模式] 模型: {model}")
        logger.info(f"[測試模式] URL: {url}")

        return {
            "page_id": mock_page_id,
            "success": True,
            "title": title,
            "model": model,
            "url": url,
            "text_length": len(text),
            "text_chunks": text_chunks,
        }

    def split_text(self, text, limit=NOTION_RICH_TEXT_LIMIT):
        return chunk_text(text, limit=limit)

    def get_notion_env(self):
        load_dotenv()

        return {
            "notion_client": Client(auth=os.getenv("NOTION_API_KEY")),
            "database_id": os.getenv("NOTION_DATABASE_ID"),
        }

    def save_with_notion(self, title, text, model, url):
        notion_env = self.get_notion_env()
        notion = notion_env["notion_client"]
        database_id = notion_env["database_id"]

        try:
            text_chunks = chunk_text(text, NOTION_RICH_TEXT_LIMIT)

            children = [
                {
                    "object": "block",
                    "paragraph": {
                        "rich_text": build_rich_text_array(chunk),
                        "color": "default",
                    },
                }
                for chunk in text_chunks
            ]

            response = notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Title": {
                        "title": build_rich_text_array(title)
                        or [{"type": "text", "text": {"content": ""}}],
                    },
                    "URL": {
                        "url": url,
                    },
                    "Model": {
                        "rich_text": build_rich_text_array(model)
                        or [{"type": "text", "text": {"content": ""}}],
                    },
                    "Public": {
                        "checkbox": False,
                    },
                },
                children=children,
            )
            logger.info(f"新增成功！頁面ID: {response['id']}")

            # 返回結果以保持一致性
            return {
                "page_id": response["id"],
                "success": True,
                "title": title,
                "model": model,
                "url": url,
                "text_length": len(text),
                "text_chunks": len(text_chunks),
            }

        except Exception as e:
            logger.error(f"發生錯誤: {e}")
            raise e
