import os
from notion_client import Client
from dotenv import load_dotenv


class Notion:
    def __init__(self):
        load_dotenv()
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("NOTION_DATABASE_ID")

    def add_page(self, title, text, model, url):
        try:
            text_chunks = self.split_text(text, limit=2000)
            
            children = [
                {
                    "object": 'block',
                    "paragraph": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": chunk,
                                },
                            },
                        ],
                        "color": 'default',
                    }
                } for chunk in text_chunks
            ]
            
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": title,
                                },
                            },
                        ],
                    },
                    "URL": {
                        "url": url,
                    },
                    "Model": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": model,
                                },
                            },
                        ],
                    },
                    "Public": {
                        "checkbox": False,
                    },
                },
                children=children
            )
            print("新增成功！頁面ID:", response["id"])
        except Exception as e:
            print("發生錯誤:", e)
            
    def split_text(self, text, limit=2000):
        return [text[i:i + limit] for i in range(0, len(text), limit)]
