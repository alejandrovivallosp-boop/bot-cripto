import ccxt
import pandas as pd
import requests
import os
import google.generativeai as genai

class BotCriptoIAOficial:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.token = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        # Configurar la API Key de Gemini desde los secretos de la nube
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            # Usamos Gemini Flash para respuestas rápidas y eficientes en la nube
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

    def consultar_sentimiento_ia(self, simbolo, precio, cambio, vol):
        """Consulta en tiempo real a Google Gemini sobre el sentimiento social y técnico."""
        if not self.modelo_ia:
            return "⚖️ IA: Módulo no configurado (Falta API Key)."
        
        try:
            prompt = (
                f"Actúa como un analista cuantitativo experto en criptomonedas y sentimiento de redes (X/Twitter). "
                f"Analiza el activo {simbolo} con precio ${precio}, cambio diario de {cambio}\% y volumen de${vol:,.0f}. "
                f"Dame un diagnóstico muy breve de máximo 2 líneas evaluando si hay hype social, riesgo de trampa o potencial de rebote."
            )
            respuesta = self.modelo_ia.generate_content(prompt)
            return f"🤖 *IA / Social:* {respuesta.text.strip()}"
        except Exception as e:
            return f"⚖️ IA: Sentimiento neutral (Error temporal al consultar IA)."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando análisis inteligente con Gemini en la nube...")
        try:
            tickers = self.exchange.fetch_tickers()
            pares_usdt = {
                symbol: data for symbol, data in tickers.items() 
                if '/USDT' in symbol and 'UP' not in symbol and 'DOWN' not in symbol
            }
            
            ganadoras, perdedoras, volumen_bajo, volumen_alto = [], [], [], []
            
            for symbol, data in pares_usdt.items():
                vol = data['quoteVolume'] or 0
                precio = data['last']
                cambio = data['percentage'] or 0
                if not precio or precio <= 0: continue
                
                item = (symbol, precio, vol, cambio)
                if cambio > 0: ganadoras.append(item)
                elif cambio < 0: perdedoras.append(item)
                
                if vol < 2_000_000: volumen_bajo.append(item)
                elif vol > 30_000_000: volumen_alto.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            volumen_bajo.sort(key=lambda x: x[2], reverse=True)

            # Analizar la top ganadora con Gemini para ver su pulso social
            top_symbol, top_precio, top_vol, top_cambio = ganadoras[0]
            analisis_ia = self.consultar_sentimiento_ia(top_symbol, top_precio, top_cambio, top_vol)

            # Armar reporte integral enriquecido con IA
            reporte = f"🧠 *REPORTE INTELIGENTE 24/7 + GEMINI* 📊\n"
            reporte += f"🔎 Analizadas: *{len(pares_usdt)} criptos*\n\n"
            
            reporte += "🚀 *1. TOP GANADORA (Análisis IA)*\n"
            reporte += f"• *{top_symbol}* | `${top_precio}` (`+{top_cambio}%`) | Vol: `${top_vol:,.0f}`\n"
            reporte += f"  {analisis_ia}\n\n"

            reporte += "📉 *2. TOP PERDEDORA (Oportunidad de Rebote)*\n"
            if perdedoras:
                s_p, p_p, v_p, c_p = perdedoras[0]
                reporte += f"• *{s_p}* | `${p_p}` (`{c_p}%`) | Vol: `${v_p:,.0f}`\n"

            reporte += "\n🟢 *3. BAJO VOLUMEN (Acumulación Oculta)*\n"
            if volumen_bajo:
                s_b, p_b, v_b, c_b = volumen_bajo[0]
                reporte += f"• *{s_b}* | `${p_b}` (`{c_b:+.2f}%`) | Vol: `${v_b:,.0f}`\n"

            reporte += "\n🤖 *Estado:* Nube activa con motor de Inteligencia Artificial."
            self.enviar_mensaje(reporte)
            print("✅ Reporte con IA enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoIAOficial()
    bot.ejecutar_analisis()
