import os
import json
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
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
    itens_lista = []
    
    for block in data.get('results', []):
        
        # Procura em listas de tarefas (to_do)
        if block['type'] == 'to_do':
            titulo_completo = ""
            url_extraida = None
            
            # Junta todo o texto daquela linha (com ou sem link)
            for text_obj in block['to_do']['rich_text']:
                titulo_completo += text_obj['plain_text']
                # Se esse pedacinho de texto tiver um link, ele guarda
                if text_obj.get('href') and not url_extraida:
                    url_extraida = text_obj['href']
                    
            if titulo_completo.strip():
                if url_extraida and url_extraida.startswith('/'):
                    url_extraida = f"https://www.notion.so{url_extraida}"
                    
                itens_lista.append({
                    'url': url_extraida, # Será "null" se não tiver link
                    'titulo': titulo_completo.strip()
                })
                    
    return itens_lista

if __name__ == "__main__":
    itens_extraidos = fetch_notion_links()
    
    with open("links.json", "w", encoding="utf-8") as f:
        json.dump(itens_extraidos, f, ensure_ascii=False, indent=4)
        
    print(f"Sucesso: links.json atualizado com {len(itens_extraidos)} itens.")
