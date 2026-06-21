import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def extrair_dados_notion(url):
    async with async_playwright() as p:
        # Argumentos cruciais para evitar bloqueios e funcionar perfeitamente em CI/CD
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gl-drawing-for-tests"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        print("A carregar a página do Notion...")
        
        # Alterado para 'networkidle' para garantir que todo o JavaScript do Notion terminou de rodar
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception:
            print("Aviso: Tempo limite de rede atingido, tentando processar o que foi carregado...")

        # Aguarda um seletor mais genérico de texto ou a própria página principal estabilizar
        try:
            await page.wait_for_selector(".notion-scroller", timeout=20000)
            # Pausa de segurança ligeiramente maior para o ecossistema pesado do Notion
            await page.wait_for_timeout(4000)
        except Exception as e:
            print(f"Aviso: Seletor não encontrado. O Notion pode ter mudado a classe interna. Detalhe: {e}")

        html_content = await page.content()
        await browser.close()
        return html_content

def processar_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Captura o título (seletor atualizado para os padrões do Notion)
    titulo_pagina = soup.find("h1") or soup.find(class_="notion-page-block") or soup.find(class_="notion-title")
    titulo_texto = titulo_pagina.get_text().strip() if titulo_pagina else "Material de Apoio"
    
    links_encontrados = []
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag['href']
        texto_link = " ".join(a_tag.get_text().split()).strip()
        
        # Ignora links do sistema, rodapés e políticas do Notion
        se_valido = (
            texto_link and 
            "Skip to content" not in texto_link and
            not any(x in href for x in ["/login", "/signup", "notion.so/product", "notion.so/desktop"])
        )
        
        if se_valido:
            # Normaliza links internos
            if href.startswith("/"):
                href = f"https://www.notion.so{href}"
            
            # Se o texto exibido for a própria URL, limpa para criar um título legível
            if texto_link.startswith(("http://", "https://")) or (len(texto_link) > 30 and "-" in texto_link):
                parte_limpa = href.split('/')[-1].split('?')[0]
            else:
                parte_limpa = texto_link

            # Remove o hash ID de 32 caracteres do Notion
            parte_limpa = re.sub(r'-?[a-f0-9]{32}', '', parte_limpa)
            
            # Limpa traços e espaços
            titulo_limpo = parte_limpa.replace('-', ' ').replace('_', ' ').strip()
            
            # Capitalização Inteligente
            titulo_limpo = " ".join([palavra.upper() if palabra.lower() in ['bd', 'it', 'ai', 'io', 'ui', 'ux'] else palabra.capitalize() for palabra in titulo_limpo.split()])
            
            if not titulo_limpo:
                titulo_limpo = "Subpágina de Conteúdo"

            if not any(item['link'] == href for item in links_encontrados):
                links_encontrados.append({
                    "titulo": titulo_limpo,
                    "link": href
                })
                
    return titulo_texto, links_encontrados

def gerar_pagina_estatica(titulo_projeto, itens):
    favicon_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2338bdf8'%3E%3Cpath d='M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM5 7h5v2H5V7zm0 4h5v2H5v-2zm14 6H5v-2h14v2zm0-4h-7v-2h7v2zm0-4h-7V7h7v2z'/%3E%3C/svg%3E"

    html_template = f"""<!DOCTYPE html>
<html lang="pt" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo_projeto} | Central de Conteúdos</title>
    <link rel="icon" type="image/svg+xml" href="{favicon_svg}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{
            --bg-principal: #0B0F19;
            --bg-card: #111827;
            --bg-item: #1F2937;
            --bg-item-hover: #374151;
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #F9FAFB;
            --text-secondary: #9CA3AF;
            --accent-color: #38BDF8;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-principal);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }}
        .dashboard-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
        }}
        .header-accent {{
            color: var(--accent-color);
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        .custom-list-item {{
            background-color: var(--bg-item);
            border: 1px solid var(--border-color);
            border-radius: 12px !important;
            color: var(--text-primary);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 12px;
        }}
        .custom-list-item:hover {{
            background-color: var(--bg-item-hover);
            color: #FFFFFF;
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.4);
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.1);
        }}
        .icon-box {{
            background-color: rgba(56, 189, 248, 0.1);
            padding: 8px;
            border-radius: 8px;
            color: var(--accent-color);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .custom-list-item:hover .icon-box {{
            background-color: var(--accent-color);
            color: var(--bg-principal);
        }}
        .badge-sync {{
            font-size: 0.75rem;
            background-color: rgba(16, 185, 129, 0.1);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.2);
            padding: 6px 12px;
            border-radius: 50px;
        }}
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-lg-7 col-md-9">
                <div class="dashboard-card p-4 p-md-5">
                    <div class="d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-3 mb-4">
                        <div>
                            <h1 class="h2 header-accent mb-1">{titulo_projeto}</h1>
                            <p class="text-muted small mb-0">Repositório de Recursos Estáticos</p>
                        </div>
                        <div class="align-self-start align-self-sm-center">
                            <span class="badge-sync d-inline-flex align-items-center gap-1.5">
                                <span class="spinner-grow spinner-grow-sm text-success" style="animation-duration: 3s;" role="status"></span>
                                Sincronizado via CI/CD
                            </span>
                        </div>
                    </div>
                    <p class="text-secondary small mb-4">Selecione o módulo de apoio abaixo para aceder diretamente à documentação estruturada no Notion:</p>
                    <div class="list-group list-group-flush">"""
    
    for item in itens:
        html_template += f"""
                        <a href="{item['link']}" target="_blank" class="list-group-item custom-list-item d-flex justify-content-between align-items-center p-3 text-decoration-none">
                            <div class="d-flex align-items-center gap-3">
                                <div class="text-muted small fw-semibold text-opacity-50 ps-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-text" viewBox="0 0 16 16">
                                        <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5m0 2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5"/>
                                        <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z"/>
                                    </svg>
                                </div>
                                <span class="fw-semibold text-light">{item['titulo']}</span>
                            </div>
                            <div class="icon-box">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" class="bi bi-arrow-up-right" viewBox="0 0 16 16">
                                    <path fill-rule="evenodd" d="M14 2.5a.5.5 0 0 0-.5-.5h-6a.5.5 0 0 0 0 1h4.793L2.146 13.146a.5.5 0 0 0 .708.708L13 3.707V8.5a.5.5 0 0 0 1 0z"/>
                                </svg>
                            </div>
                        </a>"""
                        
    html_template += """
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Sucesso! Painel Premium em modo Dark gerado em 'index.html'.")

if __name__ == "__main__":
    # IMPORTANTE: Alterada a URL de 'app.notion.com' para 'www.notion.so' para evitar a tela de Login obrigatório
    url_notion = "https://www.notion.so/Material-de-Apoio-3e8e3775cf2e46d0a7515f7cf3f7b53f"
    
    html_renderizado = asyncio.run(extrair_dados_notion(url_notion))
    titulo, lista_links = processar_html(html_renderizado)

    if lista_links:
        gerar_pagina_estatica(titulo, lista_links)
    else:
        print("Erro: Nenhum link extraído. Certifique-se de que a página está marcada como 'Share to Web' (Pública) no Notion.")
