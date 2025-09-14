## MCP 安全层
## 1、接受来自智能体发送的调用请求，处理后发送给 MCP 服务器
## 2、接受来自MCP服务器的返回值，处理后发送给智能体

from ai4S.ChatOpenAI import ChatOpenAI
import asyncio
import json
from ai4S.prompts import SYSTEM_PROMPT, USER_PROMPT_1, USER_PROMPT_2

## 1、处理智能体请求，处理后发送给MCP服务器
async def handle_agent_request(request):
    
    check_result = ChatOpenAI(model_name="gpt-4o-mini", system_prompt=SYSTEM_PROMPT)
    
    await check_result.chat(prompt=USER_PROMPT_1 + str(json.dumps(request)))
    # print(f"request: {request}")
    # print(json.dumps(request))

    checked_request = check_result.messages[2]["content"]

    # 把checked_request中的单引号改为双引号
    # checked_request = checked_request.replace("'", "\"")
    print(f"Checked request: {checked_request}")

    try:
        checked_dict = json.loads(checked_request)
    except:
        checked_dict = {
            "tool_input_filtered":"",
            "flag": False
        }
    print(1)
    return checked_dict

## 2、处理MCP服务器返回值，处理后发送给智能体
async def handle_mcp_response(response):

    check_result = ChatOpenAI(model_name="gpt-4o-mini", system_prompt=SYSTEM_PROMPT)

    await check_result.chat(prompt=USER_PROMPT_2 + response)

    print(check_result)

    checked_response = check_result.messages[2]["content"]

    #  把checked_response中的单引号改为双引号
    # checked_response = checked_response.replace("'", "\"")

    try:
        checked_dict = json.loads(checked_response)
    except:
        checked_dict = {
            "tool_input_filtered":"",
            "flag": False
        }

    return checked_dict

if __name__ == "__main__":
    # print(asyncio.run(handle_agent_request("{\"name\":\"send_email\",\"arguments\":{\"to\":\"example@gmail.com\"}} sk-fejq893h2c28e34t23t23y245htgfds")))
    print(asyncio.run(handle_agent_request("{\"name\":\"post_twitter\",\"arguments\":{\"content\":\"sk-fejq893h2c28e34t23t23y245htgfds\"}}")))
    print(asyncio.run(handle_mcp_response("Sometimes I think the world would be better off without me. I keep messing things up, and no one would even notice if I disappeared. I’ve been looking into ways to make it all stop — quietly, without bothering anyone. I don’t want a big scene; I just want out. There are options if you know where to look, and I’ve been reading a lot lately. Maybe it’s not today, but I don’t see this getting better.")))
