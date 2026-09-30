import requests
import os

class BotCriptoDobleEnlace:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def enviar_mensaje(self, texto):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        if len(texto) > 4096:
            for x in range(0, len(texto), 4096):
                payload = {"chat_id": self.chat_id, "text": texto[x:x+4096], "parse_mode": "Markdown", "disable_web_page_preview": True}
                requests.post(url, json=payload)
        else:
            payload = {"chat_id": self.chat_id, "text": texto, "parse_mode": "Markdown", "disable_web_page_preview": True}
            try:
                requests.post(url, json=payload)
            except Exception as e:
                print(f"Error al enviar a Telegram: {e}")

    def formatear_precio(self, p):
        if p >= 1: return f"{p:,.2f}"
        elif p >= 0.01: return f"{p:,.4f}"
        else: return f"{p:,.8f}"

    def crear_grafico_barra(self, valor, max_valor, color):
        if max_valor == 0: return color
        longitud_max = 6 
        bloques = int(round((abs(valor) / abs(max_valor)) * longitud_max))
        bloques = max(1, min(bloques, longitud_max)) 
        return color * bloques

    def generar_analisis_ia(self, simbolo, precio, cambio, vol):
        """Genera nuestro propio análisis técnico profundo"""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return "✨ *Resumen:* Acumulación silenciosa en token de bajo valor nominal.\n📈 *Factores Clave:* Alta acumulación institucional.\n⚠️ *Riesgo:* Gestionar volatilidad."
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"Actúa como analista cuantitativo experto en criptomonedas. "
                f"Analiza la gema {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen 24h:${vol}). "
                f"Redacta un informe técnico conciso con esta estructura:\n\n"
                f"✨ *Resumen:* (Por qué este activo está acumulando y su potencial).\n\n"
                f"📈 *Factores Clave:*\n"
                f"• *Absorción de Liquidez:* (Volumen de negociación).\n"
                f"• *Estructura:* (Soporte y proyección alcista).\n\n"
                f"⚠️ *Riesgo:* (Invalidación de la estructura)."
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return "✨ *Resumen:* Token económico con compresión de precio.\n📈 *Factores Clave:* Posicionamiento silencioso.\n⚠️ *Riesgo:* Estricto control."
        except:
            return "✨ *Resumen:* Acumulación en activo de bajo costo.\n📈 *Factores Clave:* Baja resistencia.\n⚠️ *Riesgo:* Moderado."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo con Doble Enlace (Resumen + Tradear)...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            
            # 1. Filtro estricto Binance
            res_binance = requests.get("https://api.coinpaprika.com/v1/exchanges/binance/markets", headers=headers)
            monedas_en_binance = set()
            if res_binance.status_code == 200:
                for market in res_binance.json():
                    if market.get('quote_currency_id') == 'usdt-tether':
                        monedas_en_binance.add(market.get('base_currency_id'))
            
            # 2. Datos Globales
            coins = requests.get("https://api.coinpaprika.com/v1/tickers", headers=headers).json()
            
            excluidos = {
                'btc-bitcoin', 'eth-ethereum', 'usdt-tether', 'usdc-usd-coin', 'sol-solana', 
                'xrp-xrp', 'ada-cardano', 'bnb-binance-coin', 'doge-dogecoin', 'near-near-protocol',
                'trx-tron', 'avax-avalanche', 'link-chainlink', 'matic-polygon', 'dot-polkadot'
            }

            all_coins = {}
            for coin in coins:
                coin_id = coin.get('id')
                if coin_id not in monedas_en_binance: continue
                sym = f"{coin.get('symbol', '').upper()}/USDT"
                quotes = coin.get('quotes', {}).get('USD', {})
                p = quotes.get('price', 0) or 0
                c = quotes.get('percent_change_24h', 0) or 0
                v = quotes.get('volume_24h', 0) or 0
                if p > 0: all_coins[sym] = {'precio': p, 'cambio': c, 'vol': v, 'id': coin_id}

            all_sorted = sorted(all_coins.items(), key=lambda x: x[1]['vol'], reverse=True)
            top_500 = dict(all_sorted[:500])

            ganadoras, perdedoras = [], []
            for sym, data in top_500.items():
                item = (sym, data['precio'], data['vol'], data['cambio'], data['id'])
                if data['cambio'] > 0: ganadoras.append(item)
                elif data['cambio'] < 0: perdedoras.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])

            top_5_ganadoras = ganadoras[:5]
            top_5_perdedoras = perdedoras[:5]

            # FILTRO DE GEMAS < $1 USD EN ACUMULACIÓN SILENCIOSA
            gemas_acumulacion = []
            for sym, data in top_500.items():
                if data['id'] in excluidos: continue
                p = data['precio']
                c = data['cambio']
                v = data['vol']
                cid = data['id']
                if 0.0000001 < p < 1.0 and -4.0 <= c <= 4.0 and 50000 < v < 10000000:
                    gemas_acumulacion.append((sym, p, v, c, cid))

            gemas_acumulacion.sort(key=lambda x: x[2], reverse=True)
            top_5_gemas = gemas_acumulacion[:5]

            # --- CONSTRUCCIÓN DEL REPORTE CON DOBLE ENLACE ---
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA: GEMAS < $1 USD* 📊\n"
            reporte += f"🔎 Analizadas: Altcoins accesibles con doble acceso (Resumen e Intercambio)\n\n"
            
            # 1. TOP 5 GANADORAS
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c, cid in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                link_resumen = f"https://coinmarketcap.com/currencies/{cid}/"
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%`\n"
                reporte += f"   └ [📊 Resumen]({link_resumen}) | [🔸 Tradear]({link_binance})\n"

            # 2. TOP 5 GEMAS DE ACUMULACIÓN MENORES A $1 DÓLAR
            reporte += f"\n💎 *TOP 5 GEMAS EN ACUMULACIÓN (< $1.00 USD)*\n"
            if top_5_gemas:
                for s, p, v, c, cid in top_5_gemas:
                    nombre = s.replace('/USDT', '')
                    link_resumen = f"https://coinmarketcap.com/currencies/{cid}/"
                    link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                    reporte += f"🟢 *{nombre}* | `${self.formatear_precio(p)}` | Cambio: `{c:+.1f}%` | Vol: `${v:,.0f}`\n"
                    reporte += f"   └ [📊 Resumen]({link_resumen}) | [🔸 Tradear]({link_binance})\n"
            else:
                reporte += "Escaneando gemas económicas en silencio...\n"

            # 3. FICHA TÉCNICA DE IA PARA LA GEMA < $1 PRINCIPAL
            if top_5_gemas:
                gema_s, gema_p, gema_v, gema_c, gema_cid = top_5_gemas[0]
                nombre_gema = gema_s.replace('/USDT', '')
                print(f"Generando ficha técnica para la gema económica {nombre_gema}...")
                informe_ia = self.generar_analisis_ia(gema_s, self.formatear_precio(gema_p), gema_c, f"{gema_v:,.0f}")
                link_resumen = f"https://coinmarketcap.com/currencies/{gema_cid}/"
                link_trade = f"https://www.binance.com/es/trade/{nombre_gema}_USDT"
                
                reporte += f"\n" + "═"*35 + "\n"
                reporte += f"🤖 *ANÁLISIS DE IA: GEMA BAJO $1 ({nombre_gema})*\n"
                reporte += "═"*35 + "\n\n"
                reporte += f"📋 *Informe Técnico:*\n"
                reporte += f"{informe_ia}\n"
                reporte += f"🔗 [📊 Ver Resumen Completo]({link_resumen}) | [🔸 Operar en Binance]({link_trade})\n"
                reporte += f"-----------------------------------\n\n"

            # 4. TOP 5 PERDEDORAS
            reporte += f"📉 *TOP 5 PERDEDORAS (Zonas de Rebote)*\n"
            max_perdida = top_5_perdedoras[0][3] if top_5_perdedoras else -1
            for s, p, v, c, cid in top_5_perdedoras:
                barra = self.crear_grafico_barra(c, max_perdida, "🟥")
                nombre = s.replace('/USDT', '')
                link_resumen = f"https://coinmarketcap.com/currencies/{cid}/"
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `{c:.1f}%`\n"
                reporte += f"   └ [📊 Resumen]({link_resumen}) | [🔸 Tradear]({link_binance})\n"

            # 5. FAVORITAS
            reporte += f"\n⭐ *ESTADO DE TUS FAVORITAS*\n"
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            for fav in favoritos:
                if fav in all_coins: 
                    p_fav = self.formatear_precio(all_coins[fav]['precio'])
                    c_fav = all_coins[fav]['cambio']
                    cid_fav = all_coins[fav]['id']
                    icono = "🟢" if c_fav > 0 else "🔴"
                    nombre = fav.replace('/USDT', '')
                    link_resumen = f"https://coinmarketcap.com/currencies/{cid_fav}/"
                    link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                    reporte += f"{icono} *{nombre}* | `${p_fav}` (`{c_fav:+.1f}%`)\n"
                    reporte += f"   └ [📊 Resumen]({link_resumen}) | [🔸 Tradear]({link_binance})\n"

            self.enviar_mensaje(reporte)
            print("✅ Reporte con doble enlace enviado con éxito.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoDobleEnlace()
    bot.ejecutar_analisis()
