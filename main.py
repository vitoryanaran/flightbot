import os
import requests
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ORIGENS = ["GRU", "CGH"]

DESTINOS = [
    {"codigo": "LIS", "cidade": "Lisboa"},
    {"codigo": "MIA", "cidade": "Miami"},
    {"codigo": "EZE", "cidade": "Buenos Aires"},
    {"codigo": "SCL", "cidade": "Santiago"},
    {"codigo": "BOG", "cidade": "Bogotá"},
    {"codigo": "MAD", "cidade": "Madri"},
    {"codigo": "FCO", "cidade": "Roma"},
    {"codigo": "CDG", "cidade": "Paris"},
    {"codigo": "FLN", "cidade": "Florianópolis"},
    {"codigo": "SSA", "cidade": "Salvador"},
    {"codigo": "REC", "cidade": "Recife"},
    {"codigo": "FOR", "cidade": "Fortaleza"},
]

PRECO_MAXIMO = {
    "nacional": 600,
    "internacional": 3000
}

DESTINOS_NACIONAIS = ["FLN", "SSA", "REC", "FOR"]

def buscar_voos(origem, destino_codigo, destino_cidade):
    data_ida = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    data_volta = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")

    params = {
        "engine": "google_flights",
        "departure_id": origem,
        "arrival_id": destino_codigo,
        "outbound_date": data_ida,
        "return_date": data_volta,
        "currency": "BRL",
        "hl": "pt",
        "api_key": SERPAPI_KEY,
        "bags": 0,
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        melhores = data.get("best_flights", []) or data.get("other_flights", [])

        resultados = []
        for voo in melhores[:3]:
            preco = voo.get("price", 0)
            companhia = voo.get("flights", [{}])[0].get("airline", "N/A")
            duracao = voo.get("total_duration", 0)

            nacional = destino_codigo in DESTINOS_NACIONAIS
            limite = PRECO_MAXIMO["nacional"] if nacional else PRECO_MAXIMO["internacional"]

            if preco and preco <= limite:
                resultados.append({
                    "origem": origem,
                    "destino": destino_cidade,
                    "codigo": destino_codigo,
                    "preco": preco,
                    "companhia": companhia,
                    "duracao": duracao,
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

    msg = "✈️ *FlightBot — Ofertas do dia*\n"
    msg += f"_Saindo de São Paulo \\(GRU/CGH\\)_\n"
    msg += f"_Somente bagagem de mão_\n\n"

    for o in ofertas:
        duracao_h = o['duracao'] // 60
        duracao_m = o['duracao'] % 60
        msg += f"🟢 *{o['origem']} → {o['destino']}* — R$ {o['preco']:,.0f}\n"
        msg += f"   {o['companhia']} · {duracao_h}h{duracao_m}m\n"
        msg += f"   📅 Ida: {o['data\\_ida']} · Volta: {o['data\\_volta']}\n\n"

    msg += "👉 Acesse Google Flights para reservar\n"
    msg += f"_Atualizado às {datetime.now().strftime('%H:%M')} · FlightBot_"
    return msg

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado.")
        print("\n--- MENSAGEM ---")
        print(mensagem)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "MarkdownV2"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada no Telegram com sucesso!")
        else:
            print(f"Erro Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def executar_busca():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Iniciando busca de voos...")
    todas_ofertas = []

    for origem in ORIGENS:
        for destino in DESTINOS:
            print(f"  Buscando {origem} → {destino['codigo']}...")
            resultado = buscar_voos(origem, destino["codigo"], destino["cidade"])
            todas_ofertas.extend(resultado)
            time.sleep(2)

    todas_ofertas.sort(key=lambda x: x["preco"])
    melhores = todas_ofertas[:8]

    print(f"\nOfertas encontradas: {len(melhores)}")

    if melhores:
        mensagem = formatar_mensagem(melhores)
        enviar_telegram(mensagem)
    else:
        print("Nenhuma oferta abaixo do limite hoje.")
        enviar_telegram("✈️ *FlightBot* — Nenhuma oferta abaixo do limite hoje\\. Até amanhã\\!")

def main():
    print("FlightBot iniciado!")
    executar_busca()

    schedule.every().day.at("07:00").do(executar_busca)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
