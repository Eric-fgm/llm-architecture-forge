import os

from dotenv import load_dotenv
from prompt_chain import GeminiClient, PromptChain

load_dotenv()
client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY", ""), model="gemini-2.5-flash")

chain = PromptChain(client)
chain.add_step(prompt_template="Summarize: {text}", output_key="summary")
chain.add_step(prompt_template="Key takeaways from: {summary}", output_key="takeaways")

result = chain.run({"text": "Your long text here..."})
print(result.outputs["takeaways"])
