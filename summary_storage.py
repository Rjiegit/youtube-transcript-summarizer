import os
from notion_client import Client
from dotenv import load_dotenv


class SummaryStorage:
    def __init__(self):
        pass

    def save(self, title, text, model, url):
        self.save_with_notion(title, text, model, url)
            
    def split_text(self, text, limit=2000):
        return [text[i:i + limit] for i in range(0, len(text), limit)]
    
    def get_notion_env(self):
        load_dotenv()
        
        return {
            "notion_client": Client(auth=os.getenv("NOTION_API_KEY")),
            "database_id": os.getenv("NOTION_DATABASE_ID")
        }
    
    def save_with_notion(self, title, text, model, url):
        notion_env = self.get_notion_env()
        notion = notion_env["notion_client"]
        database_id = notion_env["database_id"]
        
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
            
            response = notion.pages.create(
                parent={"database_id": database_id},
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
