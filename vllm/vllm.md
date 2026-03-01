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

---

## 核心原理与关键参数

### 核心原理

#### PagedAttention
vLLM 的核心发明。传统推理框架会为每个请求预分配一块连续的显存来存 KV Cache，导致大量显存碎片浪费。PagedAttention 借鉴操作系统虚拟内存的思路，把 KV Cache 切成固定大小的 page 动态分配，显存利用率大幅提升，支持更多并发请求。

#### Prefill 与 Decode 分离
一次推理分两个阶段：

- **Prefill**：处理用户输入，一次性计算所有 input token 的 KV Cache，计算密集，决定 TTFT
- **Decode**：逐个生成 output token，每次只算一个 token，内存带宽密集，决定 TPOT

两个阶段计算特征完全不同，是理解延迟指标和性能瓶颈的基础。大规模部署时可以将两个阶段拆到不同机器上分别优化。

#### Continuous Batching
传统 batching 要等一批请求全部完成才处理下一批，GPU 利用率低。Continuous Batching 让新请求随时插入正在进行的 batch，GPU 始终满载，是 vLLM 高吞吐的关键机制。

#### 量化（Quantization）
将模型权重从 FP16 压缩到更低精度（INT8、INT4、FP8），显存占用减半，推理速度提升，精度略有损失。常见方案：

- **FP8**：精度损失最小，需要较新的 GPU（A100/H100）
- **AWQ / GPTQ**：INT4 量化，显存减少 75%，适合在小卡上跑大模型

---

### 关键启动参数

```bash
vllm serve <model> \
  --max-model-len 8192 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --tensor-parallel-size 1 \
  --quantization fp8
```

| 参数 | 作用 | 调优建议 |
|---|---|---|
| `--max-model-len` | 最大上下文长度（input + output） | 按业务需求设置，越小越省显存 |
| `--max-num-seqs` | 最大并发请求数 | 显存够的情况下尽量调高 |
| `--gpu-memory-utilization` | 显存使用比例，默认 0.9 | 可调到 0.95 榨干显存，留余量防 OOM |
| `--tensor-parallel-size` | 多卡张量并行，几张卡写几 | 单卡写 1，多卡按实际数量 |
| `--quantization` | 量化方式（fp8 / awq / gptq） | 显存不够时开启，优先选 fp8 |

---

### 调参思路

**显存不够跑不起来** → 开启量化（`--quantization fp8`）或缩短 `--max-model-len`

**TTFT 太高** → 减少 `--max-num-seqs`，降低并发，让 prefill 更快完成

**吞吐量不够** → 调高 `--gpu-memory-utilization`，增大 KV Cache，支持更多并发

**多卡部署** → 设置 `--tensor-parallel-size` 等于 GPU 数量
