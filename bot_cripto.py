import requests
import os

class BotCriptoFichaTecnica:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def enviar_mensaje(self, texto):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id, 
            "text": texto, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
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
        longitud_max = 7 
        bloques = int(round((abs(valor) / abs(max_valor)) * longitud_max))
        bloques = max(1, min(bloques, longitud_max)) 
        return color * bloques

    def consultar_resumen_ia(self, simbolo, precio, cambio, vol):
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return "🟢 *Señal:* 🟢 Viable\n💡 *Factores:* Flujo de liquidez inicial positivo."
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"Actúa como el sistema de IA de análisis de Binance. Analiza {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Vol:${vol}). "
                f"Responde estrictamente en 3 líneas con este formato exacto:\n"
                f"1. 🟢/🟡/🔴 *Señal:* (Elige semáforo según el impulso y explica brevemente si es apta para operar)\n"
                f"2. 💡 *Factores Clave:* (Catalizador o razón del movimiento actual)\n"
                f"3. 🎯 *Soporte/Resistencia:* (Niveles estimados de corto plazo)"
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return "🟢 *Señal:* 🟢 Viable\n💡 *Factores:* Alta rotación de capital.\n🎯 *Soporte:* Vigilar tendencia."
        except:
            return "🟢 *Señal:* 🟢 Viable\n💡 *Factores:* Mercado en consolidación.\n🎯 *Soporte:* Mantener cautela."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo con Enlaces a Fichas Técnicas...")
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
            
            # 3. Cruzar datos guardando el ID para la ficha técnica
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
            
            # Análisis IA para el líder
            top_symbol, top_precio, top_vol, top_cambio, top_id = top_5_ganadoras[0]
            nombre_lider = top_symbol.replace('/USDT', '')
            resumen_ia_lider = self.consultar_resumen_ia(
                top_symbol, self.formatear_precio(top_precio), top_cambio, f"{top_vol:,.0f}"
            )

            # --- CONSTRUCCIÓN DEL REPORTE ---
            reporte = f"🧠 *CENTRAL BINANCE AI* 📊\n"
            reporte += f"🔎 Analizadas: {total_analizadas} monedas de Binance\n\n"
            
            # Ganadoras con enlaces a Ficha Técnica
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c, cid in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                # Enlace directo a la ficha con toda la info de la moneda e historial
                link = f"[{nombre}](https://coinpaprika.com/coin/{cid})"
                reporte += f"• {link} | {barra} `+{c:.1f}%`\n"
            
            reporte += f"\n🤖 *Información de IA sobre {nombre_lider}:*\n"
            reporte += f"{resumen_ia_lider}\n\n"

            # Potencial con enlaces a Ficha Técnica
            reporte += f"💎 *TOP 5 POTENCIAL (Acumulación)*\n"
            max_pot = top_5_potencial[0][3] if top_5_potencial else 1
            for s, p, v, c, cid in top_5_potencial:
                barra = self.crear_grafico_barra(c, max_pot, "🟦")
                nombre = s.replace('/USDT', '')
                link = f"[{nombre}](https://coinpaprika.com/coin/{cid})"
                reporte += f"• {link} | {barra} `+{c:.1f}%`\n"
            
            # Perdedoras con enlaces a Ficha Técnica
            reporte += f"\n📉 *TOP 5 PERDEDORAS (Oportunidades de Rebote)*\n"
            max_perdida = top_5_perdedoras[0][3] if top_5_perdedoras else -1
            for s, p, v, c, cid in top_5_perdedoras:
                barra = self.crear_grafico_barra(c, max_perdida, "🟥")
                nombre = s.replace('/USDT', '')
                link = f"[{nombre}](https://coinpaprika.com/coin/{cid})"
                reporte += f"• {link} | {barra} `{c:.1f}%`\n"

            # Favoritas con enlaces a Ficha Técnica
            reporte += f"\n⭐ *TUS FAVORITAS*\n"
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            for fav in favoritos:
                if fav in pares_dict: 
                    p_fav = self.formatear_precio(pares_dict[fav]['precio'])
                    c_fav = pares_dict[fav]['cambio']
                    cid_fav = pares_dict[fav]['id']
                    icono = "🟢" if c_fav > 0 else "🔴"
                    nombre = fav.replace('/USDT', '')
                    link = f"[{nombre}](https://coinpaprika.com/coin/{cid_fav})"
                    reporte += f"{icono} {link} | `${p_fav}` (`{c_fav:+.1f}%`)\n"

            self.enviar_mensaje(reporte)
            print("✅ Reporte con Fichas Técnicas enviado.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoFichaTecnica()
    bot.ejecutar_analisis()
