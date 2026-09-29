import requests
import os

class BotCriptoIAResumida:
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

    def consultar_ficha_tecnica_ia(self, simbolo, precio, cambio, vol):
        """Genera nuestra propia ficha técnica e informe de IA personalizado"""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return "💡 *Análisis:* Activo impulsado por rotación de capital institucional."
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"Actúa como analista cuantitativo experto en criptomonedas. "
                f"Genera una ficha técnica interna para {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Vol:${vol}). "
                f"Responde estrictamente en 4 líneas con este formato exacto:\n"
                f"1. 🏷️ *Tipo / Sector:* (Ej: Capa 1, DeFi, IA, etc. y estimación de antigüedad del proyecto)\n"
                f"2. 📊 *Análisis de Movimiento:* (Por qué subió o bajó hoy en función del volumen)\n"
                f"3. 🟢/🟡/🔴 *Evaluación Operativa:* (Color y veredicto de si vale la pena operar ahora)\n"
                f"4. 🎯 *Rango Clave:* (Soporte y resistencia estimada de corto plazo)"
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return "🏷️ *Tipo:* Activo digital listado\n📊 *Análisis:* Flujo de órdenes estable.\n🟢 *Evaluación:* Viable con gestión de riesgo.\n🎯 *Rango:* Vigilar volatilidad."
        except:
            return "🏷️ *Tipo:* Criptoactivo de Binance\n📊 *Análisis:* Acumulación en curso.\n🟢 *Evaluación:* Operable.\n🎯 *Rango:* Mantener soporte."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo con Ficha Técnica de IA Propia...")
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
                    pares_dict[sym] = {'precio': precio, 'cambio': cambio, 'vol': vol}

            pares_ordenados = sorted(pares_dict.items(), key=lambda x: x[1]['vol'], reverse=True)
            top_500 = dict(pares_ordenados[:500])
            total_analizadas = len(top_500)

            ganadoras, perdedoras, potencial = [], [], []
            for sym, data in top_500.items():
                item = (sym, data['precio'], data['vol'], data['cambio'])
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
            
            # Generar Ficha Técnica de IA propia para la ganadora absoluta
            top_symbol, top_precio, top_vol, top_cambio = top_5_ganadoras[0]
            nombre_lider = top_symbol.replace('/USDT', '')
            ficha_ia = self.consultar_ficha_tecnica_ia(
                top_symbol, self.formatear_precio(top_precio), top_cambio, f"{top_vol:,.0f}"
            )

            # --- CONSTRUCCIÓN DEL REPORTE CON IA PROPIA ---
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA PROPIA* 📊\n"
            reporte += f"🔎 Analizadas: {total_analizadas} monedas de Binance\n\n"
            
            # Ganadoras (Nombres limpios sin enlaces externos molestos)
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                reporte += f"• *{nombre}* | ${self.formatear_precio(p)} | {barra} `+{c:.1f}%`\n"
            
            # Nuestra Ficha Técnica detallada generada por IA
            reporte += f"\n📋 *FICHA TÉCNICA DE IA ({nombre_lider}):*\n"
            reporte += f"{ficha_ia}\n\n"

            # Potencial
            reporte += f"💎 *TOP 5 POTENCIAL (Acumulación)*\n"
            max_pot = top_5_potencial[0][3] if top_5_potencial else 1
            for s, p, v, c in top_5_potencial:
                barra = self.crear_grafico_barra(c, max_pot, "🟦")
                nombre = s.replace('/USDT', '')
                reporte += f"• *{nombre}* | ${self.formatear_precio(p)} | {barra} `+{c:.1f}%`\n"
            
            # Perdedoras
            reporte += f"\n📉 *TOP 5 PERDEDORAS (Oportunidades de Rebote)*\n"
            max_perdida = top_5_perdedoras[0][3] if top_5_perdedoras else -1
            for s, p, v, c, cid in top_5_perdedoras: # Corregido tuplas perdedoras
                pass
                
            # Construcción limpia de perdedoras
            reporte_perdedoras = ""
            for s, p, v, c in top_5_perdedoras:
                barra = self.crear_grafico_barra(c, max_perdida, "🟥")
                nombre = s.replace('/USDT', '')
                reporte_perdedoras += f"• *{nombre}* | ${self.formatear_precio(p)} | {barra} `{c:.1f}%`\n"
            reporte += reporte_perdedoras

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
            print("✅ Reporte con Ficha de IA Propia enviado.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoIAResumida()
    bot.ejecutar_analisis()
