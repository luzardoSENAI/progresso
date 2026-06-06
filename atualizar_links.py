import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def extrair_dados_notion(url):
    async with async_playwright() as p:
        # Lança o navegador com argumentos ideais para ambientes de CI (como o GitHub)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("A carregar a página do Notion...")
        await page.goto(url, wait_until="networkidle")
        
        # Aguarda que o conteúdo principal do Notion seja renderizado
        try:
            await page.wait_for_selector(".notion-page-content", timeout=15000)
        except Exception:
            print("Aviso: Tempo limite esgotado, tentando processar o HTML parcial.")

        html_content = await page.content()
        await browser.close()
        return html_content

def processar_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    titulo_pagina = soup.find("h1") or soup.find(class_="notion-page-block")
    titulo_texto = titulo_pagina.get_text().strip() if titulo_pagina else "Material de Apoio"
    print(f"Título identificado: {titulo_texto}")

    links_encontrados = []
    
    # Captura os links estruturados do Notion
    for a_tag in soup.find_all("a", href=True):
        href = a_tag['href']
        texto_link = a_tag.get_text().strip()
        
        if texto_link and not href.startswith(("/login", "/signup", "https://www.notion.so/product")):
            if href.startswith("/"):
                href = f"https://notion.so{href}"
            
            links_encontrados.append({
                "titulo": texto_link,
                "link": href
            })
            
    return titulo_texto, links_encontrados

def gerar_pagina_estatica(titulo_projeto, itens):
    html_template = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo_projeto}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container my-5">
        <div class="card shadow-sm mb-4">
            <div class="card-body">
                <h1 class="card-title h3 mb-4 text-primary">{titulo_projeto}</h1>
                <p class="text-muted">Links atualizados automaticamente via GitHub Actions:</p>
                <div class="list-group">"""
    
    for item in itens:
        html_template += f"""
                    <a href="{item['link']}" target="_blank" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        {item['titulo']}
                        <span class="badge bg-secondary rounded-pill">→</span>
                    </a>"""
                    
    html_template += """
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Ficheiro 'index.html' atualizado!")

# Execução principal
if __name__ == "__main__":
    url_notion = "https://app.notion.com/p/Material-de-Apoio-3e8e3775cf2e46d0a7515f7cf3f7b53f"
    html_renderizado = asyncio.run(extrair_dados_notion(url_notion))
    titulo, lista_links = processar_html(html_renderizado)

    if lista_links:
        gerar_pagina_estatica(titulo, lista_links)
    else:
        print("Erro: Nenhum link extraído. Certifica-te de que a página está partilhada publicamente.")