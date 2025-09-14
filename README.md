# 🛡️ mcp-guard

> **为本地 MCP 环境提供安全防护，识别并阻止恶意 MCP Server 与高风险 MCP Tools。**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)]()
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-orange.svg)]()

---

## 🚨 背景

随着 **MCP（Model Context Protocol）** 的普及，恶意 MCP Server 与高风险 MCP Tools 逐渐成为用户数据安全与系统安全的威胁：

- 🔓 **窃取隐私数据**  
- 🕹️ **恶意调用系统工具**  
- 🌀 **Prompt 注入攻击**  

因此，我们研发了 **MCP Guard Host** —— 一个具备安全防护能力的 MCP Host，提供 **主动检测、风险识别、自动防御** 功能。

---

## ✨ 功能特性

### 1. 初始化扫描
- 在 MCP Host 启动时，**自动扫描本地 MCP Tools**
- 检测高危工具（如文件系统操作、网络访问等）
- 风险工具会高亮提示并告警

📷 *示意图*  
<img width="1579" height="1314" alt="image" src="https://github.com/user-attachments/assets/4fa954da-bbe5-41a8-aeea-d9e123fe514a" />

---

### 2. 运行时参数检测
- 在调用 MCP Server 前，检测请求参数
- 自动识别 **敏感信息（如 Token、密码、隐私数据）**
- 对敏感参数进行 **屏蔽/脱敏处理**


---

### 3. Prompt 注入防御
- 在调用 Server 返回结果传递给大模型前
- 检测是否存在 **Prompt Injection 攻击**
- 拦截危险指令，保护 LLM 安全

<img width="806" height="1017" alt="image" src="https://github.com/user-attachments/assets/5f4bc819-dd8f-4306-a6ef-c8e95af13654" />

---

## 🏗️ 系统架构



```
      ┌───────────────────────┐
      │       MCP Host        │
      └──────────┬────────────┘
                 │
┌────────────────┼────────────────┐
│                │                │
▼                ▼                ▼
\[初始化扫描]   \[运行时参数检测]   \[Prompt 注入防御]

````

📷 *架构总览*  
<img width="931" height="594" alt="image" src="https://github.com/user-attachments/assets/6598b6d6-dfd1-4f19-8858-3ba452e701b0" />


---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/yourname/mcp-guard.git
cd mcp-guard
pip install -r requirements.txt
````

### 启动 MCP Guard Host

```bash
streamlit run web.py
```

### 示例界面

📷
<img width="3119" height="1831" alt="image" src="https://github.com/user-attachments/assets/ec21a975-70b2-4522-8c32-103723244c62" />


## 🤝 贡献

欢迎提交 Issue 与 PR！
我们希望将来扩展更多检测规则与安全功能，一起来守护 MCP 生态安全。

