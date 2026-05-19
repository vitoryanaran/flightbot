try:
    response = requests.post(url, json=payload, headers=headers, timeout=60)

    # DEBUG
    print(f"    Status: {response.status_code}")
    print(f"    Resposta: {response.text[:500]}")

    data = response.json()

    # =========================
    # VALIDAÇÃO DA RESPOSTA
    # =========================
    if isinstance(data, str):
        print(f"    ⚠️ Retornou string: {data}")
        return []

    if isinstance(data, dict):
        print(f"    ⚠️ Retornou dict: {data}")
        return []

    resultados = []

    for voo in data:

        # =========================
        # TRATAMENTO DE PREÇO
        # =========================
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

        # =========================
        # DADOS DO VOO
        # =========================
        companhia = (
            voo.get("airline")
            or voo.get("airlineName")
            or voo.get("cheapestSource")
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
            or voo.get("baggage")
            or "Somente bagagem de mão"
        )

        escalas = (
            voo.get("stops")
            or voo.get("scale")
            or "Direto"
        )

        aeroporto_saida = (
            voo.get("originAirport")
            or origem
        )

        aeroporto_chegada = (
            voo.get("destinationAirport")
            or destino_codigo
        )

        horario_saida = (
            voo.get("departureTime")
            or "N/A"
        )

        horario_chegada = (
            voo.get("arrivalTime")
            or "N/A"
        )

        # =========================
        # FILTRO DE PREÇO
        # =========================
        nacional = destino_codigo in DESTINOS_NACIONAIS

        limite = (
            PRECO_MAXIMO["nacional"]
            if nacional
            else PRECO_MAXIMO["internacional"]
        )

        if preco <= limite:

            resultado = {
                "origem": origem,
                "destino": destino_cidade,
                "codigo": destino_codigo,
                "preco": preco,
                "companhia": companhia,
                "duracao": duracao,
                "link": link,
                "bagagem": bagagem,
                "escalas": escalas,
                "aeroporto_saida": aeroporto_saida,
                "aeroporto_chegada": aeroporto_chegada,
                "horario_saida": horario_saida,
                "horario_chegada": horario_chegada,
                "data_ida": data_ida,
                "data_volta": data_volta,
            }

            resultados.append(resultado)

            # =========================
            # MENSAGEM TELEGRAM
            # =========================
            mensagem = f"""
<b>✈️ PASSAGEM ENCONTRADA!</b>

<b>🛫 Origem:</b> {resultado['origem']}
<b>🛬 Destino:</b> {resultado['destino']} ({resultado['codigo']})

<b>💰 Preço:</b> R$ {resultado['preco']:.2f}

<b>🏢 Companhia:</b> {resultado['companhia']}
<b>⏱️ Duração:</b> {resultado['duracao']}
<b>🔁 Escalas:</b> {resultado['escalas']}
<b>🧳 Bagagem:</b> {resultado['bagagem']}

<b>🛫 Aeroporto saída:</b> {resultado['aeroporto_saida']}
<b>🛬 Aeroporto chegada:</b> {resultado['aeroporto_chegada']}

<b>🕐 Saída:</b> {resultado['horario_saida']}
<b>🕐 Chegada:</b> {resultado['horario_chegada']}

<b>📅 Ida:</b> {resultado['data_ida']}
<b>📅 Volta:</b> {resultado['data_volta']}

<a href="{resultado['link']}">🔗 Comprar passagem</a>
"""

            # =========================
            # ENVIO TELEGRAM
            # =========================
            try:

                requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={
                        "chat_id": CHAT_ID,
                        "text": mensagem,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    },
                    timeout=30
                )

                print(f"    ✅ Telegram enviado: R$ {preco}")

            except Exception as erro_telegram:
                print(f"    ❌ Erro Telegram: {erro_telegram}")

    return resultados

except Exception as e:
    print(f"    ❌ Erro buscando {origem} -> {destino_codigo}: {e}")
    return []
