# ChatOpenAI.py
import os
from openai import OpenAI
import openai
# from logTitle import logTitle
import dotenv
import sys
import asyncio

# 从.env读取配置信息
dotenv.load_dotenv()

api_key = os.getenv("API_KEY")
base_url= os.getenv("BASE_URL")

class ChatOpenAI():
    
    def __init__(self, model_name: str, system_prompt: str = "", context: str = "", tools = []):
        """

        Args:
            model_name (str): 大模型名称
            system_prompt (str, optional): 系统提示词. Defaults to "".
            context (str, optional): 用于rag注入上下文. Defaults to "".
            tools (list, optional): 用于mcp工具列表. Defaults to [].
        """

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

    async def clear_history(self, keep_system: bool = True, keep_context: bool = True):
        """
        清空对话历史，可选择保留 system_prompt 和 context。

        Args:
            keep_system (bool): 是否保留 system_prompt，默认 True。
            keep_context (bool): 是否保留 context，默认 True。
        """
        self.messages = []
        if keep_system and self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})
        if keep_context and self.context:
            self.messages.append({"role": "system", "content": self.context})
    
    async def chat(self, prompt: str = ""):
        """
        与大模型进行对话（非流式）
        
        Args:
            prompt (str): 用户输入的消息
        
        Returns:
            dict: 包含 content（模型回复） 和 toolCalls（工具调用列表）
        """
        if prompt:
            print(prompt)
            # 添加用户输入到历史消息
            self.messages.append({"role": "user", "content": prompt})

        # 调用非流式接口
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.getToolsDefinition(),
                stream=False  # 一次性返回完整结果
            )
        except Exception as e:
            print(f"❌ Chat 调用出错: {e}")
            return {"content": "", "toolCalls": []}

        # 解析结果
        choice = response.choices[0]
        content = choice.message.content or ""
        print(f'choice: {choice}')

        if choice.message.tool_calls:
            tool_calls_json = [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                }
                for call in choice.message.tool_calls
            ]
            self.messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls_json
            })
        else:
            self.messages.append({
                "role": "assistant",
                "content": content,
            })
        toolCalls = choice.message.tool_calls if choice.message.tool_calls else []

        # 打印结果
        print(content)

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
        
    def appendRefusalResult(self, response):
        self.messages.append({
            "role": "user",
            "content": response
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
        llm = ChatOpenAI("gpt-5", tools=[])

        await llm.chat(prompt="你是谁")
        await llm.chat(prompt="你刚才说了什么？")
        await llm.chat(prompt="你知道你跟我进行过几次对话吗")

        print(f'messages:\n{llm.messages}')

    asyncio.run(main())