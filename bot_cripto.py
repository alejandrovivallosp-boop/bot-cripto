import requests
import os
import google.generativeai as genai

class BotCriptoMacro:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.modelo_ia = None

    def enviar_mensaje(self, texto):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": texto, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Error al enviar a Telegram: {e}")

    def formatear_precio(self, p):
        if p >= 1: return f"{p:,.2f}"
        elif p >= 0.01: return f"{p:,.4f}"
        else: return f"{p:,.8f}"

    def consultar_analisis_por_categoria(self, simbolo, precio, cambio, vol):
        if not self.modelo_ia:
            return "🏷️ *Categoría:* General\n🌐 *Narrativa:* Módulo IA no configurado."
        try:
            prompt = (
                f"Actúa como un analista cuantitativo. Analiza {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen:${vol}). "
                f"Responde en 4 líneas:\n"
                f"1. 🏷️ *Categoría:* (Ej: Capa 1, DeFi, AI, Meme)\n"
                f"2. 🌐 *Narrativa:* (Catalizador del movimiento)\n"
                f"3. ⚡ *Riesgo:* (Evaluación del momentum)\n"
                f"4. 🎯 *Veredicto:* (Corto, táctico)"
            )
            respuesta = self.modelo_ia.generate_content(prompt)
            return respuesta.text.strip()
        except Exception:
            return "🏷️ *Categoría:* No especificada\n🌐 *Narrativa:* Sincronizando...\n⚡ *Riesgo:* Moderado\n🎯 *Veredicto:* Monitorear."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo Macro 5x5x5 (Filtro Binance)...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            
            # 1. Filtro estricto Binance
            url_binance = "https://api.coinpaprika.com/v1/exchanges/binance/markets"
            res_binance = requests.get(url_binance, headers=headers)
            monedas_en_binance = set()
            if res_binance.status_code == 200:
                for market in res_binance.json():
                    if market.get('quote_currency_id') == 'usdt-tether':
                        monedas_en_binance.add(market.get('base_currency_id'))
            
            # 2. Precios globales
            url_tickers = "https://api.coinpaprika.com/v1/tickers"
            coins = requests.get(url_tickers, headers=headers).json()
            
            # 3. Filtrar y estructurar
            pares_dict = {}
            for coin in coins:
                if coin.get('id') not in monedas_en_binance: continue
                    
                sym = f"{coin.get('symbol', '').upper()}/USDT"
                quotes = coin.get('quotes', {}).get('USD', {})
                precio = quotes.get('price', 0) or 0
                cambio = quotes.get('percent_change_24h', 0) or 0
                vol = quotes.get('volume_24h', 0) or 0
                
                if precio > 0:
                    pares_dict[sym] = {'precio': precio, 'cambio': cambio, 'vol': vol}

            # 4. Clasificación Macro
            pares_ordenados = sorted(pares_dict.items(), key=lambda x: x[1]['vol'], reverse=True)
            top_500 = dict(pares_ordenados[:500])
            total_analizadas = len(top_500)

            ganadoras, perdedoras, potencial = [], [], []
            for sym, data in top_500.items():
                item = (sym, data['precio'], data['vol'], data['cambio'])
                if data['cambio'] > 0: 
                    ganadoras.append(item)
                    # Potencial: Sube poco (menos de 5%) pero tiene volumen (se está acumulando)
                    if data['cambio'] < 5.0:
                        potencial.append(item)
                elif data['cambio'] < 0: 
                    perdedoras.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            potencial.sort(key=lambda x: x[2], reverse=True) # Potencial se ordena por volumen de dinero

            # Extraer los Top 5
            top_5_ganadoras = ganadoras[:5]
            top_5_perdedoras = perdedoras[:5]
            top_5_potencial = potencial[:5]
            
            # IA solo para la N°1 para mantener rapidez
            top_symbol, top_precio, top_vol, top_cambio = top_5_ganadoras[0]
            analisis_ia = self.consultar_analisis_por_categoria(
                top_symbol, self.formatear_precio(top_precio), top_cambio, f"{top_vol:,.0f}"
            )

            # 5. Favoritas
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            reporte_favoritas = ""
            for fav in favoritos:
                if fav in pares_dict: 
                    p_fav = self.formatear_precio(pares_dict[fav]['precio'])
                    c_fav = pares_dict[fav]['cambio']
                    reporte_favoritas += f"• *{fav}* | `${p_fav}` (`{c_fav:+.2f}%`)\n"

            # 6. Construcción del Reporte Visual
            reporte = f"🧠 *CENTRAL MACRO (BINANCE)* 📊\n"
            reporte += f"🔎 Analizadas: {total_analizadas} monedas\n\n"
            
            reporte += f"🚀 *TOP 5 GANADORAS (Tendencia Fuerte)*\n"
            for i, (s, p, v, c) in enumerate(top_5_ganadoras):
                reporte += f"{i+1}. *{s}* | `${self.formatear_precio(p)}` (`+{c:.2f}%`)\n"
            
            reporte += f"\n🤖 *Análisis IA del Líder ({top_symbol}):*\n{analisis_ia}\n\n"

            reporte += f"💎 *TOP 5 POTENCIAL (Acumulación Institucional)*\n"
            for i, (s, p, v, c) in enumerate(top_5_potencial):
                reporte += f"{i+1}. *{s}* | `${self.formatear_precio(p)}` (`+{c:.2f}%`)\n"
            
            reporte += f"\n📉 *TOP 5 PERDEDORAS (Zonas de Rebote)*\n"
            for i, (s, p, v, c) in enumerate(top_5_perdedoras):
                reporte += f"{i+1}. *{s}* | `${self.formatear_precio(p)}` (`{c:.2f}%`)\n"

            reporte += f"\n⭐ *TUS FAVORITAS*\n"
            reporte += reporte_favoritas if reporte_favoritas else "Sin datos.\n"

            self.enviar_mensaje(reporte)
            print("✅ Reporte Macro 5x5x5 enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoMacro()
    bot.ejecutar_analisis()
