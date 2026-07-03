import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://localhost:8000/bookings/21/request-cancel',
    method='POST',
    data=b'{"reason":"test"}',
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    print("Success:", resp.read())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
