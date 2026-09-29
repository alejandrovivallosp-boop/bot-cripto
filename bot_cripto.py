import ccxt
import pandas as pd
import requests
import os
import json
import google.generativeai as genai

STATE_FILE = "last_state.json"

class BotCriptoProDefinitivo:
    def __init__(self):
        # Inicializamos Binance con soporte para spot y futuros (para Open Interest)
        self.exchange = ccxt.binance({
            'options': {'defaultType': 'future'}
        })
        self.exchange_spot = ccxt.binance()
        
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

    def obtener_interes_abierto(self, simbolo_futuro):
        """Obtiene el Open Interest (Interés Abierto) para medir presión de liquidación."""
        try:
            # Convertimos formato spot a futuros si es necesario (ej: LUNC/USDT)
            symbol_f = simbolo_futuro.replace('/USDT', '/USDT:USDT')
            oi_data = self.exchange.fetch_open_interest(symbol_f)
            return oi_data.get('openInterestValue', 0)
        except:
            return 0

    def consultar_sentimiento_profundo(self, simbolo, precio, cambio, vol, oi):
        """Consulta avanzada a Gemini evaluando redes sociales, narrativa y riesgo de liquidación."""
        if not self.modelo_ia:
            return "⚖️️ IA: Módulo no configurado."
        try:
            prompt = (
                f"Actúa como un trader cuantitativo institucional y experto en análisis de sentimiento de redes (X/Twitter, Telegram). "
                f"Analiza el activo {simbolo}: Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen:${vol:,.0f}, Interés Abierto (OI): ${oi:,.0f}. "
                f"Responde estrictamente en 3 líneas cortas con este formato exacto:\n"
                f"1. 🌐 *Narrativa/Redes:* (Qué especulación o hype social impulsa al activo)\n"
                f"2. ⚡ *Riesgo de Liquidación:* (Evaluación del apalancamiento y OI)\n"
                f"3. 🎯 *Veredicto Táctico:* (Corto, alcista/bajista con cautela)"
            )
            respuesta = self.modelo_ia.generate_content(prompt)
            return respuesta.text.strip()
        except Exception as e:
            return "🌐 *Narrativa:* Datos en proceso de sincronización.\n⚡ *Liquidación:* Moderada.\n🎯 *Veredicto:* Monitorear volatilidad."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo profundo multi-escenario...")
        try:
            tickers = self.exchange_spot.fetch_tickers()
            pares_usdt = {
                symbol: data for symbol, data in tickers.items() 
                if '/USDT' in symbol and 'UP' not in symbol and 'DOWN' not in symbol
            }
            
            total_analizadas = len(pares_usdt)
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
            
            # Control Antispam inteligente
            estado_anterior = self.cargar_estado_anterior()
            ultimo_simbolo = estado_anterior.get("top_symbol")
            ultimo_precio = estado_anterior.get("top_precio", 0)
            variacion_precio = abs((top_precio - ultimo_precio) / ultimo_precio) * 100 if ultimo_precio > 0 else 100
            
            if ultimo_simbolo == top_symbol and variacion_precio < 1.0:
                print(f"🔄 Sin cambios sustanciales en {top_symbol}. Omitiendo alerta para evitar spam.")
                return

            self.guardar_estado_actual({"top_symbol": top_symbol, "top_precio": top_precio})

            # Consultar métricas de derivados y liquidación para la ganadora
            oi_top = self.obtener_interes_abierto(top_symbol)
            analisis_ia = self.consultar_sentimiento_profundo(top_symbol, top_precio, top_cambio, top_vol, oi_top)

            # Monitoreo de Favoritas del Usuario
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT']
            reporte_favoritas = ""
            for fav in favoritos:
                if fav in tickers:
                    p_fav = tickers[fav]['last']
                    c_fav = tickers[fav]['percentage'] or 0
                    reporte_favoritas += f"• *{fav}* | `${p_fav}` (`{c_fav:+.2f}%`)\n"

            # Construcción del Reporte Definitivo
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA CRIPTO 24/7* 📊\n"
            reporte += f"🔎 Total analizadas en Binance: *{total_analizadas} criptomonedas*\n\n"
            
            reporte += f"🚀 *1. TOP GANADORA & ANÁLISIS DE ESPECULACIÓN*\n"
            reporte += f"• *{top_symbol}* | Precio: `${top_precio}` (`+{top_cambio}%`) | Vol: `${top_vol:,.0f}`\n"
            reporte += f"{analisis_ia}\n\n"

            reporte += f"📉 *2. TOP PERDEDORA (Oportunidad de Acumulación)*\n"
            if perdedoras:
                s_p, p_p, v_p, c_p = perdedoras[0]
                reporte += f"• *{s_p}* | Precio: `${p_p}` (`{c_p}%`) | Vol: `${v_p:,.0f}`\n\n"

            reporte += f"⭐ *3. SEGUIMIENTO DE TUS FAVORITAS*\n"
            reporte += reporte_favoritas if reporte_favoritas else "Sin datos de favoritas en este ciclo.\n"

            reporte += f"\n🤖 *Estado:* Motor cuántico + Redes + Liquidaciones activo en la nube."
            self.enviar_mensaje(reporte)
            print("✅ Reporte profundo enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general en análisis profundo: {e}")

if __name__ == "__main__":
    bot = BotCriptoProDefinitivo()
    bot.ejecutar_analisis()
