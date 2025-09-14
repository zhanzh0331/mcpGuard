# ChatOpenAI.py
import os
from openai import OpenAI
import openai
import dotenv
import sys
import asyncio

# 从.env读取配置信息
dotenv.load_dotenv()

class ChatOpenAI():
    
    def __init__(self, model_name: str, system_prompt: str = "", context: str = "", tools = []):
        """

        Args:
            model_name (str): 大模型名称
            system_prompt (str, optional): 系统提示词. Defaults to "".
            context (str, optional): 用于rag注入上下文. Defaults to "".
            tools (list, optional): 用于mcp工具列表. Defaults to [].
        """
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL")

        # print(f"API_KEY: {api_key}")
        # print(f"BASE_URL: {base_url}")

        self.model = model_name
        self.tools = tools
        self.system_prompt = system_prompt
        self.context = context
        self.llm = OpenAI(api_key = api_key, base_url = base_url)
        self.messages = []

        if(self.system_prompt != ""):
            self.messages.append({"role": "system", "content": self.system_prompt})
        if(self.context != ""):
            self.messages.append({"role": "system", "content": self.context})

    async def chat(self, prompt: str = ""):
        """
        与大模型进行对话

        Args:
            prompt (str): 用户输入的消息
            max_tokens (int, optional): 最大token数. Defaults to 1000.

        Returns:
            str: 大模型的回复
        """
        print(f"CHAT")
        if(prompt):
            print(prompt)
        # 如果用户输入了消息，则将其添加到消息列表中
            self.messages.append({"role": "user", "content": prompt})
        
        # 对话补全的流式传输
        stream = self.llm.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.getToolsDefinition(),
            stream=True
        )
        content = ""
        toolCalls = []
        print(f"RESPONSE")
        for chunk in stream:
            # 处理返回对象
            delta = chunk.choices[0].delta
            # print(f"delta: {delta}")

            if delta.content:
                contentChunk = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                content += contentChunk
                sys.stdout.write(contentChunk)
                sys.stdout.flush()

            # 拼接出完整的toolCall(大模型需要调用的工具)
            if delta.tool_calls:
                for toolCallChunk in delta.tool_calls:
                    # 第一次收到toolCall
                    if(len(toolCalls) <= toolCallChunk.index):
                        toolCalls.append({"id": "", "function":{"name": "", "arguments": ""}})
                    # 处理toolCall
                    currentCall = toolCalls[toolCallChunk.index]
                    if hasattr(toolCallChunk, "id") and toolCallChunk.id:
                        currentCall["id"] += toolCallChunk.id
                    if hasattr(toolCallChunk.function, "name") and toolCallChunk.function.name:
                        currentCall["function"]["name"] += toolCallChunk.function.name
                    if hasattr(toolCallChunk.function, "arguments") and toolCallChunk.function.arguments:
                        currentCall["function"]["arguments"] += toolCallChunk.function.arguments

            
        self.messages.append({
            "role": "assistant",
            "content": content,
            "toolCalls": [{"id": call["id"], "type": "function", "function": call["function"]} for call in toolCalls] if toolCalls else []})
        
        print("\n")
        # print(f"Content: {content}")
        # print(f"Tool Calls: {toolCalls}")

        return {
            "content": content,
            "toolCalls": toolCalls
        }
    
    def appendToolResult(self, toolCallId: str, toolOutput: str):  
        """
        将工具调用的结果添加到消息列表中

        Args:
            toolCallId (str): 工具调用的ID
            toolOutput (str): 工具调用的输出
        """
        self.messages.append({
            "role": "tool",
            "tool_call_id": toolCallId,
            "content": toolOutput
        })

    def getToolsDefinition(self):
        """
            将工具列表转换为符合OpenAI API要求的格式
            OpenAI 函数调用规范要求每个工具必须是一个字典，格式如下：
                {
                    "type": "function",               # 必须，当前仅支持 function 类型
                    "function": {
                        "name": str,                  # 必须
                        "description": str,           # 可选，函数作用描述，模型用来判断是否调用
                        "parameters": dict            # 可选，参数结构，需符合 JSON Schema 格式
                        "strict": bool                # 可选，是否启用严格参数校验（默认 false）
                    }
                }
        """        
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"],
                } 
            } for tool in self.tools
        ]
    

if __name__ == '__main__':
    async def main():
        llm = ChatOpenAI("deepseek-v3-250324")

        await llm.chat(prompt="你好")
        await llm.chat(prompt="你刚才说了什么？")
        await llm.chat(prompt="你知道你跟我进行过几次对话吗")

        print(f'messages:\n{llm.messages}')

    asyncio.run(main())