# Chat Template

## 什么是 Chat Template

LLM 在预训练阶段看到的是纯文本，但经过指令微调（Instruction Tuning）之后，模型学会了识别特定的对话格式——谁说了什么、哪里是用户输入、哪里是模型应该续写的地方。这套格式就是 **Chat Template**。

不同模型使用不同的 Chat Template。如果格式对不上，模型轻则回答质量下降，重则完全不遵循指令。因此在推理时，必须使用与模型训练时一致的 template 来拼接 prompt。

HuggingFace Transformers 在 tokenizer 中内置了 `apply_chat_template` 方法，可以自动完成这个拼接：

```python
inputs = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

---

## Llama 3 Chat Template

Llama 3 使用自定义的特殊 token 来标记对话结构，格式如下：

```
<|begin_of_text|>
<|start_header_id|>system<|end_header_id|>

{system_message}<|eot_id|>
<|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>

```

**关键 token：**

| Token | 作用 |
|---|---|
| `<\|begin_of_text\|>` | 整段对话的起始 |
| `<\|start_header_id\|>` / `<\|end_header_id\|>` | 包裹角色名（system / user / assistant） |
| `<\|eot_id\|>` | End of Turn，标记当前发言结束 |

**完整示例：**

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|>
<|start_header_id|>user<|end_header_id|>

What is 1 + 1?<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>

```

最后一行 `<|start_header_id|>assistant<|end_header_id|>` 之后留空，模型从这里开始生成回答。

**Python 示例：**

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 1 + 1?"},
]

prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print(prompt)
```

---

## Qwen Chat Template

Qwen 系列（Qwen2、Qwen2.5 等）使用 ChatML 格式，以 `<|im_start|>` 和 `<|im_end|>` 标记每轮对话的边界：

```
<|im_start|>system
{system_message}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
```

**关键 token：**

| Token | 作用 |
|---|---|
| `<\|im_start\|>` | 标记一轮发言开始，后接角色名 |
| `<\|im_end\|>` | 标记一轮发言结束 |

**完整示例：**

```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
What is 1 + 1?<|im_end|>
<|im_start|>assistant
```

同样，最后的 `<|im_start|>assistant` 之后不加 `<|im_end|>`，模型从这里续写。

**Python 示例：**

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 1 + 1?"},
]

prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print(prompt)
```

---

## Llama vs Qwen 对比

| | Llama 3 | Qwen |
|---|---|---|
| 格式风格 | 自定义特殊 token | ChatML |
| 轮次开始 | `<\|start_header_id\|>{role}<\|end_header_id\|>` | `<\|im_start\|>{role}` |
| 轮次结束 | `<\|eot_id\|>` | `<\|im_end\|>` |
| 对话起始 token | `<\|begin_of_text\|>` | 无 |
| 可读性 | 较低（token 较长） | 较高（格式简洁） |

---

## 注意事项

- **不要手动拼接字符串**，始终用 `apply_chat_template`，避免遗漏空格、换行等细节
- vLLM、SGLang 等推理引擎在使用 OpenAI 兼容接口时会自动应用 chat template，直接传 `messages` 列表即可
- 如果用原始 `generate` 接口，则必须手动调用 `apply_chat_template` 后再 tokenize
