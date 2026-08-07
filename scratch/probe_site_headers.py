import requests
url = 'https://pedidodevistos.mne.gov.pt/VistosOnline/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
    'Referer': 'https://pedidodevistos.mne.gov.pt/VistosOnline/',
    'Connection': 'keep-alive'
}
res = requests.get(url, headers=headers, timeout=20)
print('status', res.status_code)
print(res.headers.get('content-type'))
print(res.text[:3000])
