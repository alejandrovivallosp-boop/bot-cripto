import requests
import os

class BotCriptoPanelBinanceAI:
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
        """Genera nuestro propio análisis técnico profundo estilo Binance AI"""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return "✨ *Resumen:* Movimiento alcista impulsado por fuerte volumen.\n📈 *Factores Clave:* Rotación de liquidez en marcos temporales cortos.\n⚠️ *Evaluación de Riesgos:* Vigilar zonas de sobrecompra."
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"Actúa como el motor de análisis de IA institucional de Binance. "
                f"Analiza en profundidad el activo {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen 24h:${vol}). "
                f"Redacta un informe técnico conciso con esta estructura exacta:\n\n"
                f"✨ *Resumen:* (Por qué se disparó o cayó el activo hoy en base a volumen y mercado).\n\n"
                f"📈 *Factores Clave:*\n"
                f"• *Entradas de Capital y Volumen:* (Impacto del volumen reportado).\n"
                f"• *Ruptura Técnica:* (Presión compradora/vendedora y soportes).\n\n"
                f"⚠️ *Evaluación de Riesgos:* (Zonas de sobrecompra o corrección)."
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return "✨ *Resumen:* Activo con alta volatilidad.\n📈 *Factores Clave:* Repunte fuerte de órdenes.\n⚠️ *Riesgo:* Posible toma de ganancias."
        except:
            return "✨ *Resumen:* Mercado en consolidación.\n📈 *Factores Clave:* Estabilidad en libro de órdenes.\n⚠️ *Riesgo:* Moderado."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo con Reporte Macro + Panel IA Propio...")
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
            
            # 3. Cruzar datos
            pares_dict = {}
            for coin in coins:
                coin_id = coin.get('id')
                if coin_id not in monedas_en_binance: continue
                sym = f"{coin.get('symbol', '').upper()}/USDT"
                quotes = coin.get('quotes', {}).get('USD', {})
                precio = quotes.get('price', 0) or 0
                cambio = quotes.get('percent_change_24h', 0) or 0
                vol = quotes.get('volume_24h', 0) or 0
                if precio > 0:
                    pares_dict[sym] = {'precio': precio, 'cambio': cambio, 'vol': vol, 'id': coin_id}

            pares_ordenados = sorted(pares_dict.items(), key=lambda x: x[1]['vol'], reverse=True)
            top_500 = dict(pares_ordenados[:500])
            total_analizadas = len(top_500)

            ganadoras, perdedoras, potencial = [], [], []
            for sym, data in top_500.items():
                item = (sym, data['precio'], data['vol'], data['cambio'], data['id'])
                if data['cambio'] > 0: 
                    ganadoras.append(item)
                    if data['cambio'] <= 5.0: potencial.append(item)
                elif data['cambio'] < 0: 
                    perdedoras.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            potencial.sort(key=lambda x: x[2], reverse=True)

            top_5_ganadoras = ganadoras[:5]
            top_5_perdedoras = perdedoras[:5]
            top_5_potencial = potencial[:5]
            
            # --- CONSTRUCCIÓN DEL REPORTE COMPLETO ---
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA DE MERCADO* 📊\n"
            reporte += f"🔎 Analizadas: {total_analizadas} criptomonedas de Binance\n\n"
            
            # Listado Ganadoras
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c, cid in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%`\n"

            # Generar nuestro propio Panel de IA profundo para las 2 principales ganadoras
            reporte += f"\n" + "═"*30 + "\n"
            reporte += f"🤖 *PANEL DE ANÁLISIS DE IA PROPIO*\n"
            reporte += "═"*30 + "\n\n"

            for s, p, v, c, cid in top_5_ganadoras[:2]: # Analizamos las 2 primeras a fondo
                nombre = s.replace('/USDT', '')
                print(f"Generando análisis técnico de IA para {nombre}...")
                informe_ia = self.generar_analisis_ia(s, self.formatear_precio(p), c, f"{v:,.0f}")
                link_trade = f"https://www.binance.com/es/trade/{nombre}_USDT"
                
                reporte += f"📊 *Información detallada sobre {nombre}:*\n"
                reporte += f"{informe_ia}\n"
                reporte += f"🔗 [🔸 Ver o tradear {nombre} en Binance]({link_trade})\n"
                reporte += f"-----------------------------------\n\n"

            # Listado Potencial
            reporte += f"💎 *TOP 5 POTENCIAL (Acumulación)*\n"
            max_pot = top_5_potencial[0][3] if top_5_potencial else 1
            for s, p, v, c, cid in top_5_potencial:
                barra = self.crear_grafico_barra(c, max_pot, "🟦")
                nombre = s.replace('/USDT', '')
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%`\n"

            # Listado Perdedoras
            reporte += f"\n📉 *TOP 5 PERDEDORAS (Oportunidades de Rebote)*\n"
            max_perdida = top_5_perdedoras[0][3] if top_5_perdedoras else -1
            for s, p, v, c, cid in top_5_perdedoras:
                barra = self.crear_grafico_barra(c, max_perdida, "🟥")
                nombre = s.replace('/USDT', '')
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `{c:.1f}%`\n"

            # Favoritas
            reporte += f"\n⭐ *TUS FAVORITAS*\n"
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            for fav in favoritos:
                if fav in pares_dict: 
                    p_fav = self.formatear_precio(pares_dict[fav]['precio'])
                    c_fav = pares_dict[fav]['cambio']
                    icono = "🟢" if c_fav > 0 else "🔴"
                    nombre = fav.replace('/USDT', '')
                    reporte += f"{icono} *{nombre}* | `${p_fav}` (`{c_fav:+.1f}%`)\n"

            self.enviar_mensaje(reporte)
            print("✅ Reporte con Panel de IA Propio integrado enviado con éxito.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoPanelBinanceAI()
    bot.ejecutar_analisis()
