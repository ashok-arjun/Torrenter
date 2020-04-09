
import requests
try:
    response = requests.get('http://www.asfafafasfa.com.',timeout = 2)
except requests.exceptions.Timeout as e:
    print(e)

print(response)
