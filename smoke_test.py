from mini_agent.llm_client import LLMClient

llm=LLMClient()
reply=llm.generate("xiehaotian")
print(reply)