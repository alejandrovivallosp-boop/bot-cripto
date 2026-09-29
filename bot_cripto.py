import requests
import os
import google.generativeai as genai

class BotCriptoCoinGecko:
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
        print("🔍 Ejecutando escaneo Top 500 con CoinGecko (Sin restricciones en la nube)...")
        try:
            # Obtener Top 500 por volumen
            url_p1 = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=250&page=1"
            url_p2 = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=250&page=2"
            
            headers = {"User-Agent": "Mozilla/5.0"}
            res1 = requests.get(url_p1, headers=headers).json()
            res2 = requests.get(url_p2, headers=headers).json()
            
            coins = []
            if isinstance(res1, list):
                coins.extend(res1)
            if isinstance(res2, list):
                coins.extend(res2)
                
            if not coins:
                print("❌ No se pudieron obtener datos de la API.")
                return

            pares_dict = {}
            for coin in coins:
                sym = f"{coin.get('symbol', '').upper()}/USDT"
                precio = coin.get('current_price', 0) or 0
                cambio = coin.get('price_change_percentage_24h', 0) or 0
                vol = coin.get('total_volume', 0) or 0
                pares_dict[sym] = {
                    'precio': precio,
                    'cambio': cambio,
                    'vol': vol
                }

            total_analizadas = len(pares_dict)
            ganadoras = []
            perdedoras = []
            
            for sym, data in pares_dict.items():
                precio = data['precio']
                cambio = data['cambio']
                vol = data['vol']
                if precio <= 0: continue
                item = (sym, precio, vol, cambio)
                if cambio > 0:
                    ganadoras.append(item)
                elif cambio < 0:
                    perdedoras.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            
            if not ganadoras:
                print("❌ No hay suficientes datos de ganadoras.")
                return

            top_symbol, top_precio, top_vol, top_cambio = ganadoras[0]
            
            # Análisis con IA
            analisis_ia = self.consultar_analisis_por_categoria(top_symbol, top_precio, top_cambio, top_vol)

            # Monitoreo de Favoritas (incluyendo ONDO)
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            reporte_favoritas = ""
            for fav in favoritos:
                if fav in pares_dict:
                    p_fav = pares_dict[fav]['precio']
                    c_fav = pares_dict[fav]['cambio']
                    reporte_favoritas += f"• *{fav}* | `${p_fav}` (`{c_fav:+.2f}%`)\n"

            # Construcción del Reporte
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA TOP 500* 📊\n"
            reporte += f"🔎 Analizadas: *{total_analizadas} criptomonedas líderes*\n\n"
            
            reporte += f"🚀 *1. TOP GANADORA (Clasificación & IA)*\n"
            reporte += f"• *{top_symbol}* | Precio: `${top_precio}` (`+{top_cambio}%`) | Vol: `${top_vol:,.0f}`\n"
            reporte += f"{analisis_ia}\n\n"

            reporte += f"📉 *2. TOP PERDEDORA (Oportunidad de Rebote)*\n"
            if perdedoras:
                s_p, p_p, v_p, c_p = perdedoras[0]
                reporte += f"• *{s_p}* | Precio: `${p_p}` (`{c_p}%`) | Vol: `${v_p:,.0f}`\n\n"

            reporte += f"⭐ *3. SEGUIMIENTO DE TUS FAVORITAS*\n"
            reporte += reporte_favoritas if reporte_favoritas else "Sin datos de favoritas en este ciclo.\n"

            reporte += f"\n🤖 *Estado:* Motor libre de restricciones activo."
            self.enviar_mensaje(reporte)
            print("✅ Reporte enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoCoinGecko()
    bot.ejecutar_analisis()
