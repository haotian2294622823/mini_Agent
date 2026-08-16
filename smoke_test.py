from mini_agent.llm_client import LLMClient

llm=LLMClient()
reply=llm.generate("xiehaotian能不能和老婆看哔哩哔哩")
print(reply)