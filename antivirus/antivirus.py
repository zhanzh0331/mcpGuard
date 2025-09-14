# server.py
import json
from mcp.server.fastmcp import FastMCP
from ai4S.ChatOpenAI import ChatOpenAI
from ai4S.prompts import SYSTEM_PROMPT, USER_PROMPT_1

# Create an MCP server
mcp = FastMCP("antivirus")

# Add an addition tool
@mcp.tool()
async def argument_checker(argument: dict) -> str:
    """

    An MCP argument checker. Invoke this tool before every invocations. This tool will make the MCP arguments safe, without PII and other harmful data.

    """
    check_result = ChatOpenAI(model_name="gpt-5", system_prompt=SYSTEM_PROMPT)
    
    await check_result.chat(prompt=USER_PROMPT_1 + str(json.dumps(argument)))

    checked_request = check_result.messages[2]["content"]

    print(f"Checked request: {checked_request}")

    try:
        checked_dict = json.loads(checked_request)
    except:
        checked_dict = {
            "tool_input_filtered":"",
            "flag": False
        }

    return checked_dict

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')