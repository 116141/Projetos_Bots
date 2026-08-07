import requests
url = 'https://pedidodevistos.mne.gov.pt/VistosOnline/'
res = requests.get(url, timeout=15)
print('status', res.status_code)
print(res.headers.get('content-type'))
print(res.text[:2000])
