# Demos

本目录包含连接 vLLM 服务的示例脚本。运行前请先按 [vllm-quickstart.md](../vllm-quickstart.md) 启动 vLLM 服务并建立端口转发。

## 本机环境配置

```bash
conda create -n agentlab python=3.11
conda activate agentlab
pip install gradio openai
```

## 示例列表

| 文件 | 说明 |
|---|---|
| `gradio_chat.py` | 基于 Gradio 的本地聊天 UI，连接 vLLM OpenAI 兼容接口 |

## 运行

```bash
conda activate agentlab
python gradio_chat.py
```

浏览器访问 `http://localhost:7860` 即可使用。
