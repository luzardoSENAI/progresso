import os
import json
import requests

# Puxa o token secreto configurado no GitHub Actions
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
# O ID extraído da sua URL pública do Notion
PAGE_ID = "39a33f83b4dd80a3a4e3f91ae52e4562" 

def fetch_notion_links():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erro na API do Notion: {response.text}")
        return []
        
    data = response.json()
    links = []
    
    # Processa os blocos da página
    for block in data.get('results', []):
        if block['type'] == 'bookmark':
            url = block['bookmark']['url']
            caption_list = block['bookmark'].get('caption', [])
            titulo = caption_list[0]['plain_text'] if caption_list else url
            links.append({'url': url, 'titulo': titulo})
            
        elif block['type'] == 'paragraph':
            # Captura links embutidos no meio de parágrafos normais
            for text_obj in block['paragraph']['rich_text']:
                if text_obj.get('href'):
                    links.append({
                        'url': text_obj['href'],
                        'titulo': text_obj['plain_text']
                    })
                    
    return links

if __name__ == "__main__":
    links_extraidos = fetch_notion_links()
    
    # Salva os dados no formato esperado pelo seu frontend
    with open("links.json", "w", encoding="utf-8") as f:
        json.dump(links_extraidos, f, ensure_ascii=False, indent=4)
        
    print(f"Sucesso: links.json atualizado com {len(links_extraidos)} links.")
