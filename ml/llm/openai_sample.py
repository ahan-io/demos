from openai import OpenAI

client = OpenAI(
	base_url="https://ai.gitee.com/v1",
	api_key="7XLKXRQOXEODVYKOYHWVR9AJ3HOJBKMW6WCL4ELX",
	default_headers={"X-Failover-Enabled":"true"},
)

# 发送聊天补全请求
# messages: 对话历史，包含系统角色指令和用户查询
# model: 指定使用的模型（DeepSeek-R1-Distill-Qwen-14B）
# stream: 启用流式响应模式，实时接收结果
# max_tokens: 限制生成内容的最大令牌数
# temperature/top_p: 控制输出随机性的参数
# extra_body: 额外的模型参数（如top_k采样）
response = client.chat.completions.create(
	messages=[
		{
			"role": "system",
			"content": "You are a helpful and harmless assistant. You should think step-by-step."
		},
		{
			"role": "user",
			"content": "Can you please let us know more details about your "
		}
	],
	model="DeepSeek-R1-Distill-Qwen-14B",
	stream=True,
	max_tokens=1024,
	temperature=0.6,
	top_p=0.7,
	extra_body={
		"top_k": 50,
	},
	frequency_penalty=0,
)

fullResponse = ""
print("Response:")
# Print streaming response
for chunk in response:
	# 跳过空选择项的chunk
	if len(chunk.choices) == 0:
		continue
	# 获取当前chunk的内容增量
	delta = chunk.choices[0].delta
	
	# 处理思考过程内容（如存在），使用灰色文本打印
	if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
		fullResponse += delta.reasoning_content
		print(f"\033[90m{delta.reasoning_content}\033[0m", end="", flush=True)
	# 处理普通响应内容，直接打印
	elif delta.content:
		fullResponse += delta.content
		print(delta.content, end="", flush=True)