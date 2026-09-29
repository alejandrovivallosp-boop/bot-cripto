import ccxt
import pandas as pd
import requests
import os
import json
import google.generativeai as genai

STATE_FILE = "last_state.json"

class BotCriptoPro:
    def __init__(self):
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
        try:
            symbol_f = simbolo_futuro.replace('/USDT', '/USDT:USDT')
            oi_data = self.exchange.fetch_open_interest(symbol_f)
            return oi_data.get('openInterestValue', 0)
        except:
            return 0

    def consultar_analisis_por_categoria(self, simbolo, precio, cambio, vol, oi):
        if not self.modelo_ia:
            return "🏷️ *Categoría:* General\n🌐 *Narrativa:* Módulo IA no configurado."
        try:
            prompt = (
                f"Actúa como un analista cuantitativo de criptomonedas. "
                f"Analiza el activo {simbolo} (Precio: ${precio}, Cambio 24h: {cambio}\%, Volumen:${vol:,.0f}, Interés Abierto: ${oi:,.0f}). "
                f"Responde estrictamente en 4 líneas con este formato exacto:\n"
                f"1. 🏷️ *Categoría:* (Indica sector, ej: Capa 1, DeFi, AI, Memes, GameFi, etc.)\n"
                f"2. 🌐 *Narrativa/Redes:* (Catalizador o especulación del sector)\n"
                f"3. ⚡ *Riesgo de Liquidación:* (Evaluación del apalancamiento y OI)\n"
                f"4. 🎯 *Veredicto Táctico:* (Corto, alcista/bajista con cautela)"
            )
            respuesta = self.modelo_ia.generate_content(prompt)
            return respuesta.text.strip()
        except Exception as e:
            return "🏷️ *Categoría:* No especificada\n🌐 *Narrativa:* Sincronizando...\n⚡ *Liquidación:* Moderada\n🎯 *Veredicto:* Monitorear."

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo Top 500 con detección de crecimiento temprano...")
        try:
            tickers = self.exchange_spot.fetch_tickers()
            
            # 1. Filtrar pares USDT limpios
            pares_usdt = {
                symbol: data for symbol, data in tickers.items() 
                if '/USDT' in symbol and 'UP' not in symbol and 'DOWN' not in symbol
            }
            
            # 2. Ordenar por volumen y recortar estrictamente al Top 500 de mayor liquidez
            pares_ordenados = sorted(
                pares_usdt.items(), 
                key=lambda x: x[1].get('quoteVolume', 0) or 0, 
                reverse=True
            )
            top_500_mercado = dict(pares_ordenados[:500])
            total_analizadas = len(top_500_mercado)

            ganadoras, perdedoras, volumen_bajo, crecimiento_temprano = [], [], [], []
            
            for symbol, data in top_500_mercado.items():
                vol = data['quoteVolume'] or 0
                precio = data['last']
                cambio = data['percentage'] or 0
                if not precio or precio <= 0: continue
                
                item = (symbol, precio, vol, cambio)
                if cambio > 0: ganadoras.append(item)
                elif cambio < 0: perdedoras.append(item)
                if vol < 2_000_000: volumen_bajo.append(item)
                
                # Detectar monedas con arranque temprano (subida moderada entre 0.10% y 6%)
                if 0.10 <= cambio <= 6.0 and vol > 1_000_000:
                    crecimiento_temprano.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])
            volumen_bajo.sort(key=lambda x: x[2], reverse=True)
            crecimiento_temprano.sort(key=lambda x: x[2], reverse=True) # Ordenar por volumen para ver las de mayor interés real

            top_symbol, top_precio, top_vol, top_cambio = ganadoras[0]
            
            # Control Antispam
            estado_anterior = self.cargar_estado_anterior()
            ultimo_simbolo = estado_anterior.get("top_symbol")
            ultimo_precio = estado_anterior.get("top_precio", 0)
            variacion_precio = abs((top_precio - ultimo_precio) / ultimo_precio) * 100 if ultimo_precio > 0 else 100
            
            if ultimo_simbolo == top_symbol and variacion_precio < 1.0:
                print(f"🔄 Sin cambios sustanciales en {top_symbol}. Omitiendo alerta.")
                return

            self.guardar_estado_actual({"top_symbol": top_symbol, "top_precio": top_precio})

            # Análisis con IA, Categoría y Derivados
            oi_top = self.obtener_interes_abierto(top_symbol)
            analisis_ia = self.consultar_analisis_por_categoria(top_symbol, top_precio, top_cambio, top_vol, oi_top)

            # Monitoreo de Favoritas del Usuario
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT']
            reporte_favoritas = ""
            for fav in favoritos:
                if fav in tickers:
                    p_fav = tickers[fav]['last']
                    c_fav = tickers[fav]['percentage'] or 0
                    reporte_favoritas += f"• *{fav}* | `${p_fav}` (`{c_fav:+.2f}%`)\n"

            # Construcción del Reporte con Crecimiento Temprano
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA TOP 500* 📊\n"
            reporte += f"🔎 Analizadas: *{total_analizadas} criptomonedas líderes*\n\n"
            
            reporte += f"🚀 *1. TOP GANADORA ABSOLUTA*\n"
            reporte += f"• *{top_symbol}* | Precio: `${top_precio}` (`+{top_cambio}%`) | Vol: `${top_vol:,.0f}`\n"
            reporte += f"{analisis_ia}\n\n"

            reporte += f"🟢 *2. CRECIMIENTO TEMPRANO (Oportunidades de Entrada > 0.10%)*\n"
            if crecimiento_temprano:
                for s_t, p_t, v_t, c_t in crecimiento_temprano[:3]: # Muestra hasta 3 opciones con arranque inicial
                    reporte += f"• *{s_t}* | Precio: `${p_t}` (`+{c_t}%`) | Vol: `${v_t:,.0f}`\n"
            else:
                reporte += "Sin activos en rango de arranque temprano en este ciclo.\n"
            reporte += "\n"

            reporte += f"📉 *3. TOP PERDEDORA (Oportunidad de Rebote)*\n"
            if perdedoras:
                s_p, p_p, v_p, c_p = perdedoras[0]
                reporte += f"• *{s_p}* | Precio: `${p_p}` (`{c_p}%`) | Vol: `${v_p:,.0f}`\n\n"

            reporte += f"⭐ *4. SEGUIMIENTO DE TUS FAVORITAS*\n"
            reporte += reporte_favoritas if reporte_favoritas else "Sin datos de favoritas en este ciclo.\n"

            reporte += f"\n🤖 *Estado:* Top 500 + Crecimiento Temprano + IA activo."
            self.enviar_mensaje(reporte)
            print("✅ Reporte con crecimiento temprano enviado con éxito a Telegram.")

        except Exception as e:
            print(f"❌ Error general en análisis: {e}")

if __name__ == "__main__":
    bot = BotCriptoPro()
    bot.ejecutar_analisis()
