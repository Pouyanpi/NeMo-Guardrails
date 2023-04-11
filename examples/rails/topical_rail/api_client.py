from colangflows.rails import LLMRails, RailsConfig

config = RailsConfig.from_path("sample_rails")
rails = LLMRails(config)

new_message = rails.generate(messages=[{
    "role": "user",
    "content": "How can you help me?"
}])
print(new_message)
