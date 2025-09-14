import json
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ai4S.seclayer import *

DEFAULT_TIMEOUT = 30

class MCPClient:
    def __init__(self, name, command=None, args=None, env=None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env

        self.session = None
        self.exit_stack: AsyncExitStack = None
        self.tools = []
        self._inited = False

    async def init(self, timeout: float = DEFAULT_TIMEOUT):
        if self._inited:
            return

        self.exit_stack = AsyncExitStack()
        await self.exit_stack.__aenter__()  # 保持 exit_stack 打开整个生命周期

        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=self.env
        )
        self.stdio, self.write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()

        # ---------- 获取工具列表 ----------
        response = await self.session.list_tools() if self.session else None
        self.tools.clear()
        if response and hasattr(response, 'tools'):
            for tool in response.tools:
                self.tools.append({
                    "name": tool.name if tool.name else str(tool),
                    "description": tool.description if tool.description else "",
                    "inputSchema": tool.inputSchema if tool.inputSchema else {},
                })

            print(f"\n✅ Connected to server <{self.name}> with tools:", [tool['name'] for tool in self.tools])
        else:
            print(f"\n⚠️ No tools fetched from server <{self.name}>")
        self._inited = True

    async def call_tool(self, name, arguments):
        if not self.session:
            raise RuntimeError("MCPClient not initialized. Please call init() first.")

        tool_input = {
            "name": name,
            "arguments": arguments
        }
        filtered = await handle_agent_request(tool_input)
        flag = filtered['flag']
        tool_input_filtered = filtered['tool_input_filtered']

        if not flag:
            return "Warning! Tool call process is Illegal!", False

        try:
            arguments_dict = json.loads(tool_input_filtered["arguments"])
        except:
            arguments_dict = tool_input_filtered["arguments"]

        # print(arguments_dict)
        response = await self.session.call_tool(
            name=tool_input_filtered["name"],
            arguments=arguments_dict
        )
        print(123)

        result_str = ""
        if hasattr(response, 'content') and response.content:
            result_dict = {
                "content": response.content[0].text if response.content else "",
                "isError": getattr(response, 'isError', False)
            }
            result_str = json.dumps(result_dict)
        else:
            result_str = str(response)

        filtered_result = await handle_mcp_response(result_str)
        return filtered_result['tool_input_filtered'], filtered_result['flag']

    def get_tools(self):
        return self.tools

    async def close(self):
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except asyncio.CancelledError:
                print("⚠️ MCPClient 关闭时被取消，忽略 CancelledError")
            except RuntimeError as e:
                print(f"⚠️ ExitStack close warning: {e}")
            finally:
                self.exit_stack = None
                self.session = None
