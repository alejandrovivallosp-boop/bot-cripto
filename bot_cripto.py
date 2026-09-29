import ccxt
import pandas as pd
import requests
import os
import json
import google.generativeai as genai

STATE_FILE = "last_state.json"

class BotCriptoIAOficial:
    def __init__(self):
        self.exchange = ccxt.binance()
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

    def cargar_estado_anterior(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def guardar_estado_actual(self, estado):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(estado, f)
        except Exception as e:
            print(f"Error al guardar estado: {e}")

    def consultar_sentimiento_ia(self, simbolo, precio, cambio, vol):
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
        print("🔍 Ejecutando análisis inteligente con control antispam...")
        try:
            tickers = self.exchange.fetch_tickers()
            pares_usdt = {
                symbol: data for symbol, data in tickers.items() 
                if '/USDT' in symbol and 'UP' not in symbol and 'DOWN' not in symbol
            }
            
            ganadoras, perdedoras, volumen_bajo = [], [], []
            
            for symbol, data in pares_usdt.items():
                vol = data['quoteVolume'] or 0
                precio = data['last']
                cambio = data['percentage'] or 0
                if not precio or precio <= 0: continue
                
                item = (symbol, precio, vol, cambio)
                if cambio > 0: ganadoras.append(item)
                elif cambio < 0: perdedoras.append(item)
                
                if vol < 2_000_000: volumen_bajo.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            volumen_bajo.sort(key=lambda x: x[2], reverse=True)

            top_symbol, top_precio, top_vol, top_cambio = ganadoras[0]
            
            estado_anterior = self.cargar_estado_anterior()
            ultimo_simbolo = estado_anterior.get("top_symbol")
            ultimo_precio = estado_anterior.get("top_precio", 0)
            
            variacion_precio = abs((top_precio - ultimo_precio) / ultimo_precio) * 100 if ultimo_precio > 0 else 100
            
            if ultimo_simbolo == top_symbol and variacion_precio < 1.5:
                print(f"🔄 Sin cambios relevantes en {top_symbol}. Omitiendo notificación para evitar spam.")
                return

            self.guardar_estado_actual({"top_symbol": top_symbol, "top_precio": top_precio})

            analisis_ia = self.consultar_sentimiento_ia(top_symbol, top_precio, top_cambio, top_vol)

            reporte = f"🧠 *REPORTE INTELIGENTE (Actualizado)* 📊\n"
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

            reporte += "\n🤖 *Estado:* Sistema antispam activo en la nube."
            self.enviar_mensaje(reporte)
            print("✅ Reporte inteligente enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoIAOficial()
    bot.ejecutar_analisis()
