import requests
import os
import google.generativeai as genai

class BotCriptoPaprikaBinance:
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

    def consultar_analisis_por_categoria(self, simbolo, precio, cambio, vol):
        if not self.modelo_ia:
            return "🏷️ *Categoría:* General\n🌐 *Narrativa:* Módulo IA no configurado."
        try:
            prompt = (
                f"Actúa como un analista cuantitativo de criptomonedas. "
                f"Analiza el activo {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen:${vol:,.0f}). "
                f"Responde estrictamente en 4 líneas con este formato exacto:\n"
                f"1. 🏷️ *Categoría:* (Indica el sector, ej: Capa 1 / L1, DeFi, Infraestructura, Memes, AI, etc.)\n"
                f"2. 🌐 *Narrativa/Redes:* (Qué catalizador o especulación impulsa al activo)\n"
                f"3. ⚡ *Riesgo de Liquidación:* (Evaluación estimada del apalancamiento)\n"
                f"4. 🎯 *Veredicto Táctico:* (Corto, alcista/bajista con cautela)"
            )
            respuesta = self.modelo_ia.generate_content(prompt)
            return respuesta.text.strip()
        except Exception as e:
            return "🏷️ *Categoría:* No especificada\n🌐 *Narrativa:* Sincronizando datos...\n⚡ *Liquidación:* Moderada\n🎯 *Veredicto:* Monitorear."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo mundial con Filtro Estricto de Binance...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            
            # 1. Obtener la lista de monedas válidas SOLAMENTE en Binance
            print("📥 Descargando directorio oficial de Binance...")
            url_binance_markets = "https://api.coinpaprika.com/v1/exchanges/binance/markets"
            res_binance = requests.get(url_binance_markets, headers=headers)
            
            monedas_en_binance = set()
            if res_binance.status_code == 200:
                for market in res_binance.json():
                    # Filtramos para asegurarnos de que se puedan operar con USDT
                    if market.get('quote_currency_id') == 'usdt-tether':
                        monedas_en_binance.add(market.get('base_currency_id'))
            
            if not monedas_en_binance:
                print("❌ No se pudo cargar el filtro de Binance.")
                return

            # 2. Obtener datos de todo el mercado global
            url_tickers = "https://api.coinpaprika.com/v1/tickers"
            response = requests.get(url_tickers, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Error HTTP de la API: {response.status_code}")
                return

            coins = response.json()
            
            # 3. Procesar datos y APLICAR EL FILTRO de Binance
            pares_dict = {}
            for coin in coins:
                coin_id = coin.get('id')
                
                # FILTRO MAESTRO: Si la moneda no existe en Binance, se ignora por completo
                if coin_id not in monedas_en_binance:
                    continue
                    
                sym = f"{coin.get('symbol', '').upper()}/USDT"
                quotes = coin.get('quotes', {}).get('USD', {})
                precio = quotes.get('price', 0) or 0
                cambio = quotes.get('percent_change_24h', 0) or 0
                vol = quotes.get('volume_24h', 0) or 0
                
                if precio > 0:
                    pares_dict[sym] = {
                        'precio': precio,
                        'cambio': cambio,
                        'vol': vol
                    }

            if not pares_dict:
                print("❌ Ninguna moneda pasó el filtro de Binance.")
                return

            # Ordenar por volumen descendente y tomar el Top 500 real de Binance
            pares_ordenados = sorted(
                pares_dict.items(),
                key=lambda x: x[1]['vol'],
                reverse=True
            )
            top_500 = dict(pares_ordenados[:500])
            total_analizadas = len(top_500)

            ganadoras = []
            perdedoras = []
            
            for sym, data in top_500.items():
                item = (sym, data['precio'], data['vol'], data['cambio'])
                if data['cambio'] > 0:
                    ganadoras.append(item)
                elif data['cambio'] < 0:
                    perdedoras.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            
            if not ganadoras:
                print("❌ No hay suficientes datos de ganadoras.")
                return

            top_symbol, top_precio, top_vol, top_cambio = ganadoras[0]
            
            # Análisis con IA para la ganadora de Binance
            analisis_ia = self.consultar_analisis_por_categoria(top_symbol, top_precio, top_cambio, top_vol)

            # Monitoreo de Favoritas
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            reporte_favoritas = ""
            for fav in favoritos:
                if fav in pares_dict: 
                    p_fav = pares_dict[fav]['precio']
                    c_fav = pares_dict[fav]['cambio']
                    reporte_favoritas += f"• *{fav}* | `${p_fav}` (`{c_fav:+.2f}%`)\n"

            # Construcción del Reporte
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA (SOLO BINANCE)* 📊\n"
            reporte += f"🔎 Analizadas: *Top {total_analizadas} monedas listadas en Binance*\n\n"
            
            reporte += f"🚀 *1. TOP GANADORA (Clasificación & IA)*\n"
            reporte += f"• *{top_symbol}* | Precio: `${top_precio}` (`+{top_cambio}%`) | Vol: `${top_vol:,.0f}`\n"
            reporte += f"{analisis_ia}\n\n"

            reporte += f"📉 *2. TOP PERDEDORA (Oportunidad de Rebote)*\n"
            if perdedoras:
                s_p, p_p, v_p, c_p = perdedoras[0]
                reporte += f"• *{s_p}* | Precio: `${p_p}` (`{c_p}%`) | Vol: `${v_p:,.0f}`\n\n"

            reporte += f"⭐ *3. SEGUIMIENTO DE TUS FAVORITAS*\n"
            reporte += reporte_favoritas if reporte_favoritas else "Sin datos de favoritas en este ciclo.\n"

            reporte += f"\n🤖 *Estado:* Filtro estricto de Binance activado."
            self.enviar_mensaje(reporte)
            print("✅ Reporte de Binance enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoPaprikaBinance()
    bot.ejecutar_analisis()
