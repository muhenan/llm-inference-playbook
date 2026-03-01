from openai import OpenAI
import gradio as gr

client = OpenAI(base_url="http://localhost:30000/v1", api_key="None")
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

def chat(message, history):
    messages = [{"role": "system", "content": "你是一个helpful的AI助手。"}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content

gr.ChatInterface(fn=chat, title="My Local AI").launch()
