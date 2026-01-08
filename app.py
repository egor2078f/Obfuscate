from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def parse_website(url):
    try:
        if not url.startswith('http'):
            url = 'https://' + url
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')

        # Удаляем мусор
        for tag in soup(["script", "style", "nav", "footer", "iframe"]):
            tag.decompose()

        page_data = []
        
        # Собираем элементы по порядку
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'a']):
            text = element.get_text().strip()
            if len(text) < 2: continue
            
            item = {
                "type": "Text",
                "content": text[:200], # Ограничение, чтобы не забить память Roblox
                "color": [255, 255, 255]
            }

            if element.name.startswith('h'):
                item["type"] = "Header"
                item["color"] = [255, 255, 100]
            elif element.name == 'a':
                item["type"] = "Link"
                item["link"] = element.get('href', '')
                item["color"] = [50, 150, 255]
            
            page_data.append(item)

        return {"title": soup.title.string if soup.title else url, "elements": page_data[:40]}
    except Exception as e:
        return {"title": "Error", "elements": [{"type": "Text", "content": f"Ошибка: {str(e)}", "color": [255, 50, 50]}]}

@app.route('/browse', methods=['POST'])
def browse():
    data = request.json
    url = data.get('url', 'google.com')
    print(f"[*] Запрос на сайт: {url}")
    result = parse_website(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
