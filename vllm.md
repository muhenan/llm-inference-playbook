# vLLM

## 部署快速参考

### 环境信息

| 项目 | 值 |
|---|---|
| 云机器 IP | 194.68.245.129 |
| SSH 端口 | 22025 |
| vLLM 端口 | 30000 |
| 模型 | Qwen/Qwen2.5-1.5B-Instruct |
| SSH Key | ~/.ssh/id_rsa |

---

### Terminal 1 — 启动 vLLM 服务（在云机器上）

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

### Terminal 2 — 建立端口转发（在本机 Mac 上）

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

### Terminal 3 — 测试调用（在本机 Mac 上）

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

### 用完记得关机

在 RunPod 控制台点 **Stop** 停止 Pod，否则持续计费。

---

## 压力测试

### 压测命令

```bash
vllm bench serve \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --base-url http://localhost:30000 \
  --num-prompts 500 \
  --request-rate 50 \
  --random-input-len 128 \
  --random-output-len 256
```

**参数说明：**

- `--num-prompts`：总请求数，压测结束条件
- `--request-rate`：每秒发送的请求数（RPS）
- `--random-input-len`：每个请求的输入 token 数
- `--random-output-len`：每个请求的输出 token 数

> 注意：压测工具使用随机生成的 token 而非真实问题，目的是控制变量，确保结果可比。

---

### 核心指标

#### 吞吐量指标

**输出 Token 吞吐量（Output Token Throughput，OTT）**

每秒生成的 output token 数量，是衡量推理性能最核心的指标。数字越高说明 GPU 利用率越好。

**总 Token 吞吐量（Total Token Throughput，TTT）**

每秒处理的 input + output token 总数。

**请求吞吐量（Request Throughput）**

每秒实际完成的请求数，单位 req/s。当系统过载时，这个数字会明显低于配置的 RPS。

---

#### 延迟指标

**首 Token 延迟（Time To First Token，TTFT）**

从用户发送请求到收到第一个 token 的时间，直接影响用户感知的响应速度。生产环境一般要求均值 < 500ms。

**单 Token 生成时间（Time Per Output Token，TPOT）**

生成每一个 output token 所需的平均时间（不含第一个 token）。TPOT 越低，流式输出越流畅。

**Token 间隔延迟（Inter-token Latency，ITL）**

相邻两个 token 之间的时间间隔，与 TPOT 含义相近，反映流式输出的稳定性。

---

#### 并发指标

**峰值并发请求数（Peak Concurrent Requests）**

压测过程中同时处于处理中的最大请求数。这个数字过高说明请求开始积压，系统已经过载。

---

### 性能规律

**input 长度对性能影响极大。** 相同硬件下，短输入能承载的 QPS 远高于长输入。原因是 input 越短，prefill 阶段越快，GPU 更多时间用于生成 token。

| input/output | RPS | 实际 req/s | Output tok/s | TTFT 中位数 |
|---|---|---|---|---|
| 1024 / 128 | 10 | 9.36 | 1197 | 97ms |
| 1024 / 128 | 50 | 14.60 | 1868 | 5362ms |
| 128 / 256 | 50 | 20.26 | 5187 | 237ms |

**判断系统是否过载的信号：**

- 实际 req/s 明显低于配置的 RPS
- TTFT 均值远大于中位数（说明部分请求等待时间极长）
- Peak concurrent requests 持续攀升

---

### 压测技巧

**1. 找甜蜜点（Sweet Spot）**

从低 RPS 开始，逐步加压（10 → 20 → 50 → 100），观察 TTFT 和 TPOT 的变化曲线。TTFT 开始急剧上升的临界点就是该配置下的性能上限。

**2. 用接近真实场景的 token 长度**

根据实际业务场景设置 `--random-input-len` 和 `--random-output-len`，不要用默认值（1024/128），否则结果参考价值不大。

**3. 关注 P99 而不只是均值**

均值好看不代表用户体验好。P99 TTFT 代表 99% 的请求都在这个时间内收到第一个 token，是更真实的用户体验指标。

**4. 对比不同参数配置**

调整 `--gpu-memory-utilization`、`--max-num-seqs` 等 vLLM 启动参数，用相同的压测条件对比结果，找到最优配置。

**5. 多次压测取平均**

单次结果受随机性影响，建议同一配置跑 3 次取平均值。
