from docker import from_env
client = from_env()
client.login(username="source_user_name",password="unobfuscated_token",registry="https://registry.gitlab.com")