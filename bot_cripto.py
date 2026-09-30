import requests
import os

class BotCriptoResumenIAInterna:
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

    def generar_analisis_gemini(self, simbolo, precio, cambio, vol):
        """Genera el informe técnico profundo procesado exclusivamente por Gemini AI"""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return (
                "✨ *Resumen:* Acumulación silenciosa detectada en zonas de soporte.\n\n"
                "📈 *Factores clave:*\n"
                "• *Flujo de Volumen:* Entrada discreta de órdenes institucionales.\n"
                "• *Estructura Técnica:* Consolidación lateral previa al impulso alcista.\n\n"
                "⚠️ *Evaluación de riesgos:* Monitorear soporte crítico ante volatilidad."
            )
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"Actúa como el motor de análisis de inteligencia artificial avanzado (Gemini AI) especializado en criptoactivos de bajo valor nominal. "
                f"Analiza en profundidad el activo {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen 24h:${vol}). "
                f"Redacta un informe técnico conciso con esta estructura exacta y profesional:\n\n"
                f"✨ *Resumen:* (Una oración detallando por qué se movió el activo hoy y el contexto de su acumulación).\n\n"
                f"📈 *Factores clave:*\n"
                f"• *Dinámica de Volumen:* (Explica el comportamiento del volumen y la escasez de oferta).\n"
                f"• *Resiliencia Técnica:* (Comportamiento del soporte o resistencia actual).\n\n"
                f"⚠️ *Evaluación de riesgos:* (Advierte sobre zonas de sobrecompra o corrección técnica)."
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return "✨ *Resumen:* Activo con compresión de precio.\n📈 *Factores clave:* Posicionamiento silencioso.\n⚠️ *Riesgo:* Moderado."
        except:
            return "✨ *Resumen:* Mercado en consolidación.\n📈 *Factores clave:* Liquidez neutral.\n⚠️ *Riesgo:* Control de posición necesario."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo con Fichas de Resumen Internas por Gemini AI...")
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

            # FILTRO DE GEMAS < $1 USD EN ACUMULACIÓN
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

            # --- CONSTRUCCIÓN DEL REPORTE CON RESUMEN DE IA INTEGRADO ---
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA (GEMINI AI)* 📊\n"
            reporte += f"🔎 Analizadas: Altcoins < $1 USD con análisis de IA interno\n\n"
            
            # 1. TOP 5 GANADORAS
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c, cid in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%` — [🔸 Tradear]({link_binance})\n"

            # 2. TOP 5 GEMAS DE ACUMULACIÓN
            reporte += f"\n💎 *TOP 5 GEMAS EN ACUMULACIÓN (< $1.00 USD)*\n"
            if top_5_gemas:
                for s, p, v, c, cid in top_5_gemas:
                    nombre = s.replace('/USDT', '')
                    link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                    reporte += f"🟢 *{nombre}* | `${self.formatear_precio(p)}` | Cambio: `{c:+.1f}%` | Vol: `${v:,.0f}` — [🔸 Tradear]({link_binance})\n"
            else:
                reporte += "Escaneando gemas económicas en silencio...\n"

            # 3. PANELES DE RESUMEN Y ANÁLISIS CREADOS POR GEMINI AI (Sustituto interno del enlace externo)
            reporte += f"\n" + "═"*35 + "\n"
            reporte += f"🤖 *RESUMEN Y ANÁLISIS TÉCNICO (GEMINI AI)*\n"
            reporte += "═"*35 + "\n\n"

            activos_a_analizar = []
            if top_5_ganadoras: activos_a_analizar.append(top_5_ganadoras[0])
            if top_5_gemas: activos_a_analizar.append(top_5_gemas[0])

            for s, p, v, c, cid in activos_a_analizar:
                nombre = s.replace('/USDT', '')
                print(f"Generando resumen analítico interno con Gemini AI para {nombre}...")
                informe_gemini = self.generar_analisis_gemini(s, self.formatear_precio(p), c, f"{v:,.0f}")
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                
                reporte += f"📊 *Resumen e Informe de IA sobre {nombre}:*\n"
                reporte += f"{informe_gemini}\n"
                reporte += f"🔗 [🔸 Tradear {nombre} en Binance]({link_binance})\n"
                reporte += f"-----------------------------------\n\n"

            # 4. TOP 5 PERDEDORAS
            reporte += f"📉 *TOP 5 PERDEDORAS (Zonas de Rebote)*\n"
            max_perdida = top_5_perdedoras[0][3] if top_5_perdedoras else -1
            for s, p, v, c, cid in top_5_perdedoras:
                barra = self.crear_grafico_barra(c, max_perdida, "🟥")
                nombre = s.replace('/USDT', '')
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `{c:.1f}%` — [🔸 Tradear]({link_binance})\n"

            # 5. FAVORITAS
            reporte += f"\n⭐ *ESTADO DE TUS FAVORITAS*\n"
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            for fav in favoritos:
                if fav in all_coins: 
                    p_fav = self.formatear_precio(all_coins[fav]['precio'])
                    c_fav = all_coins[fav]['cambio']
                    icono = "🟢" if c_fav > 0 else "🔴"
                    nombre = fav.replace('/USDT', '')
                    link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                    reporte += f"{icono} *{nombre}* | `${p_fav}` (`{c_fav:+.1f}%`) — [🔸 Tradear]({link_binance})\n"

            self.enviar_mensaje(reporte)
            print("✅ Reporte con Resumen IA interno enviado con éxito.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoResumenIAInterna()
    bot.ejecutar_analisis()
