from mini_agent.llm_client import LLMClient

llm=LLMClient()
reply=llm.generate("你好，谢浩添有被陈超喜欢吗？还是他喜欢bilibli？")
print(reply)