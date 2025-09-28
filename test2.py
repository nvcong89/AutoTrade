import requests
import json

url = "https://api.dnse.com.vn/auth-service/login"

payload = json.dumps({
  "username": "nvcong89@live.com",
  "password": "Th@nhcong89"
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)


