import os
from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:8082/v1", api_key="sk-no-key-required")

tools = [
    {
        "type": "function",
        "function": {
            "name": "draw_box",
            "description": "Draws a 3D box",
            "parameters": {
                "type": "object",
                "properties": {
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "depth": {"type": "number"}
                },
                "required": ["width", "height", "depth"]
            }
        }
    }
]

messages = [
    {"role": "system", "content": "You are a CAD agent. Use the tools provided to build the object."},
    {"role": "user", "content": "Draw a 5x5x5 box."}
]

response = client.chat.completions.create(
    model="gemma-2-2b-it",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

print(response.choices[0].message)
