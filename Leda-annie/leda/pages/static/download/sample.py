import pprint
import requests

response = requests.post(
    url = "http://localhost:5000/leda/uploading",
    headers = {"Accept": "application/json"},
    data = {"api_key": "000000000000"},
    files = {"image": open("test.jpg", "rb").read()}
)
pprint.pprint(response.json())

