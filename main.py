import requests

# =========================================
# TELEGRAM
# =========================================
TOKEN = "8934744030:AAGNmNCCts2jtm0RsrPNzh0QxuZssU3emdY"
CHAT_ID = "6173949126"

# =========================================
# CONFIG
# =========================================
DESTINOS_NACIONAIS = [
    "GRU",
    "CGH",
    "GIG",
    "SDU"
]

PRECO_MAXIMO = {
    "nacional": 800,
    "internacional": 3500
}

# =========================================
# DADOS TESTE
# =========================================
url = "https://google-flights2.p.rapidapi.com/api/v1/searchFlights"

payload = {
    "departure_id": "GRU",
    "arrival_id": "MIA",
    "outbound_date": "2026-09-10",
    "return_date": "2026-09-20",
    "currency": "BRL",
    "hl": "pt-BR",
    "adults": 1
}

headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "apify_api_UGB6GRP8japAn2DYTFDftwhgwT4sef0HgppP",
    "X-RapidAPI-Host": "google-flights2.p.rapidapi.com"
}

# =========================================
# FUNÇÃO
# =========================================
def buscar_passagens():

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )

        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text[:500]}")

        data = response.json()

        if isinstance(data, str):
            print("Retornou string")
            return

        if isinstance(data, dict):
            print("Retornou dict")
            return

        for voo in data:

            preco = voo.get("bestPrice") or voo.get("price", 0)

            try:

                preco = float(
                    str(preco)
                    .replace("R$", "")
                    .replace("$", "")
                    .replace(".", "")
                    .replace(",", ".")
                    .strip()
                )

            except:
                continue

            companhia = (
                voo.get("airline")
                or voo.get("airlineName")
                or "N/A"
            )

            duracao = voo.get("duration", "N/A")

            link = (
                voo.get("bookingUrl")
                or voo.get("deepLink")
                or ""
            )

            bagagem = (
                voo.get("baggagePolicy")
                or "Bagagem de mão"
            )

            mensagem = f"""
✈️ PASSAGEM ENCONTRADA!

🛫 Origem: GRU
🛬 Destino: MIA

💰 Preço: R$ {preco:.2f}

🏢 Companhia: {companhia}
⏱️ Duração: {duracao}
🧳 Bagagem: {bagagem}

🔗 Comprar:
{link}
"""

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": mensagem
                },
                timeout=30
            )

            print(f"Telegram enviado: R$ {preco}")

    except Exception as e:

        print(f"Erro: {e}")

# =========================================
# EXECUÇÃO
# =========================================
buscar_passagens()
