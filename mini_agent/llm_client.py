import os


from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key=os.getenv("LLM_API_KEY")
        self.model=os.getenv("LLM_MODEL")
        self.url=os.getenv("LLM_BASE_URL")
        if not self.api_key:
            raise ValueError("缺少 LLM_API_KEY 环境变量，请在 .env 文件中设置。")
        if not self.model:
            raise ValueError("缺少 LLM_MODEL 环境变量，请在 .env 文件中设置。")
        if not self.url:
            raise ValueError("缺少 LLM_BASE_URL 环境变量，请在 .env 文件中设置。")


    def generate(self,prompt:str) -> str:
        """接受用户输入，返回模型生成的响应"""

        if not prompt.strip():
            raise ValueError("输入提示不能为空。")
        self.client=OpenAI(api_key=self.api_key,base_url=self.url)
        # 使用初始化阶段创建的 SDK Client 发送请求。
        response=self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": prompt,
            }
            ],
        )
        content=response.choices[0].message.content

        return content
    

    
