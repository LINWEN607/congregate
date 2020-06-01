import os

data = ""

with open("docker/bitbucket/bitbucket.properties", "r") as f:
    for d in f.readlines():
        d = d.replace('#BITBUCKET_LICENSE', os.getenv("BITBUCKET_LICENSE"))
        d = d.replace('#BITBUCKET_PASSWORD', os.getenv("BITBUCKET_PASSWORD"))
        data += d

with open("docker/bitbucket/bitbucket.properties-populated", "w") as f:
    f.write(data)