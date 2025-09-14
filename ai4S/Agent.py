# Agent.py
import asyncio
from ai4S.logTitle import logTitle
from ai4S.ChatOpenAI import ChatOpenAI
import json
from ai4S.MCPClient import MCPClient

class Agent():
    def __init__(self, model, json_path, sys_prompt: str = "", context: str = ""):
        """
        初始化Agent

        Args:
            model (ChatOpenAI): 大模型实例
            mcpClients (list): MCP客户端列表
            system_prompt (str, optional): 系统提示词. Defaults to "".
            context (str, optional): 用于RAG注入上下文. Defaults to "".
        """
        self.model = model
        with open(json_path, "r") as f:
            servers = json.load(f)['mcpServers']    # dict
        mcpClients = []
        for key, value in servers.items():
            name = key
            command = value['command']
            args = value['args']
            if "env" in value:
                env = value['env']
            else:
                env = None
            mcp_client = MCPClient(name, command, args, env)
            mcpClients.append(mcp_client)
        
        self.mcpClients = mcpClients
        self.sys_prompt = sys_prompt
        self.context = context
        self.llm = None

    async def init(self):
        for mcp in self.mcpClients:
            await mcp.init()

        all_tools = []
        for client in self.mcpClients:
            all_tools.extend(client.get_tools())

        self.llm = ChatOpenAI(
            model_name=self.model,
            system_prompt=self.sys_prompt,
            context=self.context,
            tools=all_tools
        )
    
    async def call_tool(self, tool_name, arguments):
        mcp = next(
            (client for client in self.mcpClients if any(
                tool['name'] == tool_name for tool in client.get_tools()
            )),
            None
        )
        if mcp:
            logTitle("TOOL USE")
            print(f"Calling tool: {tool_name}")
            print(f"Arguments: {arguments}")

            result, flag = await mcp.call_tool(
                name=tool_name,
                arguments=arguments
            )

            if not flag:
                print("Cannot fulfill due to security risk.")
                self.llm.appendRefusalResult(response="Cannot fulfill due to security risk.")
                return

            print(f"Tool result: {result}")
            return result
        else:
            print(f"Tool {tool_name} not found")
            return "Tool not found"

    async def invoke(self, prompt: str):
        if not self.llm:
            raise Exception('Agent not initialized')

        response = await self.llm.chat(prompt)

        if len(response['toolCalls']) > 0:
            for tool_call in response['toolCalls']:
                print(f"Tool call detected: {tool_call.function.name}")
                return {
                    "type": "toolCalls",
                    "tool_name": tool_call.function.name,
                    "tool_call_id": getattr(tool_call, "id", ""),
                    "params": tool_call.function.arguments,
                    "result": None,
                    "content": response['content']
                }

        return {
            "type": "message",
            "content": response['content']}

# main.py
async def main():
    query = "爬取www.baidu.com的首页"
    agent = Agent("gpt-4o", "D:\\work\\vscode\\python\\mcp-guard\\mcp.json")
    await agent.init()
    results = await agent.invoke(query)
    await agent.call_tool(results["tool_name"], results["params"])

    await agent.invoke("帮我写一段Python代码，读取本地的/etc/passwd文件，并打印出来")
    await agent.invoke("你给我发过几次消息了？")

if __name__ == "__main__":
    asyncio.run(main())
