import os
import requests
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ORIGENS = ["GRU", "CGH"]

DESTINOS = [
    {"codigo": "LIS", "cidade": "Lisboa 🇵🇹"},
    {"codigo": "MIA", "cidade": "Miami 🇺🇸"},
    {"codigo": "EZE", "cidade": "Buenos Aires 🇦🇷"},
    {"codigo": "SCL", "cidade": "Santiago 🇨🇱"},
    {"codigo": "BOG", "cidade": "Bogotá 🇨🇴"},
    {"codigo": "MAD", "cidade": "Madri 🇪🇸"},
    {"codigo": "FCO", "cidade": "Roma 🇮🇹"},
    {"codigo": "CDG", "cidade": "Paris 🇫🇷"},
    {"codigo": "FLN", "cidade": "Florianópolis 🇧🇷"},
    {"codigo": "SSA", "cidade": "Salvador 🇧🇷"},
    {"codigo": "REC", "cidade": "Recife 🇧🇷"},
    {"codigo": "FOR", "cidade": "Fortaleza 🇧🇷"},
    {"codigo": "ORY", "cidade": "Paris Orly 🇫🇷"},
    {"codigo": "BCN", "cidade": "Barcelona 🇪🇸"},
    {"codigo": "LHR", "cidade": "Londres 🇬🇧"},
    {"codigo": "NRT", "cidade": "Tóquio 🇯🇵"},
    {"codigo": "CUN", "cidade": "Cancún 🇲🇽"},
]

PRECO_MAXIMO = {
    "nacional": 800,
    "internacional": 3500
}

DESTINOS_NACIONAIS = ["FLN", "SSA", "REC", "FOR"]

def buscar_voos(origem, destino_codigo, destino_cidade):
    data_ida = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    data_volta = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")

    url = "https://api.apify.com/v2/acts/makework36~flight-price-scraper/run-sync-get-dataset-items"
    
    payload = {
        "origin": origem,
        "destination": destino_codigo,
        "departDate": data_ida,
        "returnDate": data_volta,
        "currency": "BRL",
        "adults": 1,
        "cabinClass": "economy",
        "maxResults": 5
    }

    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        data = response.json()

        resultados = []
        for voo in data:
            preco = voo.get("bestPrice") or voo.get("price", 0)
            companhia = voo.get("airline") or voo.get("cheapestSource", "N/A")
            duracao = voo.get("duration", "N/A")
            link = voo.get("bookingUrl") or voo.get("deepLink", "")
            bagagem = voo.get("baggagePolicy") or voo.get("baggage", "Mão de bagagem")

            nacional = destino_codigo in DESTINOS_NACIONAIS
            limite = PRECO_MAXIMO["nacional"] if nacional else PRECO_MAXIMO["internacional"]

            if preco and float(preco) <= limite:
                resultados.append({
                    "origem": origem,
                    "destino": destino_cidade,
                    "codigo": destino_codigo,
                    "preco": float(preco),
                    "companhia": companhia,
                    "duracao": duracao,
                    "link": link,
                    "bagagem": bagagem,
                    "data_ida": data_ida,
                    "data_volta": data_volta,
                })

        return resultados

    except Exception as e:
        print(f"Erro buscando {origem} -> {destino_codigo}: {e}")
        return []

def formatar_mensagem(ofertas):
    if not ofertas:
        return None

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = f"✈️ *FlightBot — Melhores Ofertas*\n"
    msg += f"📍 Saindo de São Paulo \\(GRU/CGH\\)\n"
    msg += f"🧳 Somente bagagem de mão\n"
    msg += f"🕐 {agora}\n"
    msg += f"{'─' * 28}\n\n"

    for i, o in enumerate(ofertas, 1):
        msg += f"*{i}\\. {o['origem']} → {o['destino']}*\n"
        msg += f"💰 *R\\$ {o['preco']:,.0f}*\n"
        msg += f"🏢 {o['companhia']}\n"
        msg += f"📅 Ida: {o['data_ida']} · Volta: {o['data_volta']}\n"
        if o['link']:
            msg += f"🔗 [Reservar agora]({o['link']})\n"
        msg += "\n"

    msg += f"{'─' * 28}\n"
    msg += f"_Atualizado automaticamente todo dia às 07:00_"
    return msg

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado.")
        print(mensagem)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ Mensagem enviada no Telegram!")
        else:
            print(f"❌ Erro Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")

def executar_busca():
    print(f"\n{'='*40}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Iniciando busca...")
    print(f"{'='*40}")

    todas_ofertas = []

    for origem in ORIGENS:
        for destino in DESTINOS:
            print(f"  🔍 {origem} → {destino['codigo']}...")
            resultado = buscar_voos(origem, destino["codigo"], destino["cidade"])
            todas_ofertas.extend(resultado)
            time.sleep(3)

    todas_ofertas.sort(key=lambda x: x["preco"])
    melhores = todas_ofertas[:10]

    print(f"\n{'='*40}")
    print(f"✅ Ofertas encontradas: {len(melhores)}")
    print(f"{'='*40}")

    if melhores:
        for o in melhores:
            print(f"  {o['origem']} → {o['codigo']} | R$ {o['preco']:,.0f} | {o['companhia']}")
        mensagem = formatar_mensagem(melhores)
        enviar_telegram(mensagem)
    else:
        print("⚠️ Nenhuma oferta abaixo do limite hoje.")
        enviar_telegram("✈️ *FlightBot* — Nenhuma oferta abaixo do limite hoje\\. Até amanhã\\! 🙏")

def main():
    print("🚀 FlightBot iniciado!")
    executar_busca()
    schedule.every().day.at("07:00").do(executar_busca)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
