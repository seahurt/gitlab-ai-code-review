import httpx
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("GITLAB_URL")
token = os.getenv("GITLAB_TOKEN")

try:
    r = httpx.get(f"{url}/api/v4/user", headers={"PRIVATE-TOKEN": token}, verify=False)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print(e)
