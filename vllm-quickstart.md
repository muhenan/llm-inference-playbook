# vLLM 部署快速参考

## 环境信息

| 项目 | 值 |
|---|---|
| 云机器 IP | 194.68.245.129 |
| SSH 端口 | 22025 |
| vLLM 端口 | 30000 |
| 模型 | Qwen/Qwen2.5-1.5B-Instruct |
| SSH Key | ~/.ssh/id_rsa |

---

## Terminal 1 — 启动 vLLM 服务（在云机器上）

```bash
# 1. SSH 进入云机器
ssh root@194.68.245.129 -p 22025 -i ~/.ssh/id_rsa

# 2. 启动 vLLM（首次运行会自动下载模型，约 3GB）
vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 30000 --host 0.0.0.0
```

看到以下输出说明服务启动成功：
```
INFO: Application startup complete.
INFO: Starting vLLM API server on http://0.0.0.0:30000
```

**这个窗口必须保持开着，关掉模型就停了。**

---

## Terminal 2 — 建立端口转发（在本机 Mac 上）

```bash
# 把本机 30000 端口转发到云机器的 30000 端口
ssh root@194.68.245.129 -p 22025 -i ~/.ssh/id_rsa -L 30000:localhost:30000 -N
```

命令执行后没有任何输出，光标停住不动是正常的，说明隧道建立成功。

**这个窗口也必须保持开着，关掉就无法从本机访问了。**

> 如果不想占用一个终端窗口，加 `-f` 参数让隧道在后台运行：
> ```bash
> ssh root@194.68.245.129 -p 22025 -i ~/.ssh/id_rsa -L 30000:localhost:30000 -N -f
> ```

---

## Terminal 3 — 测试调用（在本机 Mac 上）

```bash
curl http://localhost:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

收到 JSON 格式的回复说明一切正常。

---

## 用完记得关机

在 RunPod 控制台点 **Stop** 停止 Pod，否则持续计费。
