# web_agent_display.py
import streamlit as st
import asyncio
import threading
from scan import scan  # 假设 scan 函数返回风险工具信息
from ai4S.Agent import Agent
import textwrap


# ========== 后台事件循环 ========== 
def ensure_bg_loop():
    """启动后台事件循环，只启动一次"""
    if "bg_loop" not in st.session_state:
        st.session_state["bg_loop"] = asyncio.new_event_loop()
        threading.Thread(
            target=st.session_state["bg_loop"].run_forever, daemon=True
        ).start()
    return st.session_state["bg_loop"]


def run_async(coro):
    """把异步任务丢到后台事件循环跑，并同步返回结果"""
    loop = ensure_bg_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


# ========== 页面配置 ==========
st.set_page_config(page_title="Agent Web", page_icon="🤖")
st.title("🤖 网页 Agent")


# ========== Agent 初始化 ==========
async def init_agent():
    ai = Agent("gpt-4o-mini", "mcp.json", sys_prompt="You are a helpful assistant.")
    await ai.init()
    return ai


if "ai" not in st.session_state:
    st.session_state["ai"] = run_async(init_agent())

if "history" not in st.session_state:
    st.session_state["history"] = []


# ========== 工具展示接口 ==========
if "high_risk_tools" not in st.session_state:
    with st.spinner("正在扫描风险工具，请稍候..."):
        st.session_state["high_risk_tools"] = run_async(scan())

# ========== 工具展示 ==========
def display_tools():
    high_risk_tools = st.session_state.get("high_risk_tools", {})
    if high_risk_tools:
        with st.expander("⚠️ 以下工具可能存在风险", expanded=False):
            for t, info in high_risk_tools.items():
                # 提取主要字段
                description = info.get("description", "").strip()
                schema = info.get("inputSchema", {})

                # 美化描述：去掉过长的缩进
                description = textwrap.dedent(description).strip()

                st.subheader(f"🔧 工具：{t}")
                st.markdown(f"**描述：**\n\n{description}")

                if schema:
                    st.markdown("**输入参数：**")
                    st.json(schema)

                st.markdown("---")
    else:
        st.success("✅ 未发现风险工具")

display_tools()  # 如果需要展示工具信息，取消注释


# ========== 对话逻辑 ==========
user_input = st.chat_input("请输入消息...")

if user_input:
    reply = run_async(st.session_state["ai"].invoke(user_input))

    # 保存用户输入
    st.session_state["history"].append({
        "role": "user",
        "type": "message",
        "content": user_input
    })

    # 保存 Agent 输出
    st.session_state["history"].append({
        "role": "agent",
        **reply
    })


# ========== 展示历史对话 ==========
for i, msg in enumerate(st.session_state["history"]):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            if msg["type"] == "toolCalls":
                st.markdown(f"🤖 想调用工具 **{msg['tool_name']}**，参数: {msg['params']}")
                st.markdown(msg["content"])
                cols = st.columns([1, 1])

                with cols[0]:
                    if st.button("✅ 允许调用", key=f"accept_{i}"):
                        # 1) 调用工具
                        result = run_async(
                            st.session_state["ai"].call_tool(msg["tool_name"], msg["params"])
                        )
                        # 2) 反馈工具结果给 LLM
                        st.session_state["ai"].llm.appendToolResult(
                            msg.get("tool_call_id", ""), result
                        )
                        # 3) 继续生成后续回复
                        follow = run_async(st.session_state["ai"].invoke(""))

                        # 4) 更新当前消息
                        st.session_state["history"][i] = {
                            "role": "agent",
                            "type": "tool",
                            "tool_name": msg["tool_name"],
                            "params": msg["params"],
                            "result": result,
                            "content": f"已调用工具 {msg['tool_name']}，结果如下："
                        }

                        # 5) 追加后续回复
                        st.session_state["history"].append({
                            "role": "agent",
                            **follow
                        })

                        st.rerun()

                with cols[1]:
                    if st.button("❌ 拒绝调用", key=f"reject_{i}"):
                        # 1) 明确拒绝
                        st.session_state["ai"].llm.appendRefusalResult(
                            response=f"用户拒绝调用工具 {msg['tool_name']}"
                        )
                        # 2) 继续生成后续回复
                        follow = run_async(st.session_state["ai"].invoke(""))

                        # 3) 更新当前消息
                        st.session_state["history"][i] = {
                            "role": "agent",
                            "type": "final",
                            "content": f"用户拒绝调用工具 {msg['tool_name']}。"
                        }

                        # 4) 追加后续回复
                        st.session_state["history"].append({
                            "role": "agent",
                            **follow
                        })

                        st.rerun()

            elif msg["type"] == "tool":
                st.markdown(f"🔧 {msg['tool_name']} 调用参数: {msg['params']}")
                st.markdown(f"结果: {msg['result']}")

            elif msg["type"] == "message":
                st.markdown(
                    f"<span style='color: black; font-size: 1em'>{msg['content']}</span>",
                    unsafe_allow_html=True
                )
