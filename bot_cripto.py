import requests
import os
import json

class BotCriptoConBotones:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def enviar_mensaje_con_botones(self, texto, teclado_inline):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id, 
            "text": texto, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
            "reply_markup": json.dumps(teclado_inline)
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
        longitud_max = 6 
        bloques = int(round((abs(valor) / abs(max_valor)) * longitud_max))
        bloques = max(1, min(bloques, longitud_max)) 
        return color * bloques

    def ejecutar_analisis(self):
        print("🔍 Ejecutando escaneo con Botones Interactivos...")
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
            
            # --- CONSTRUCCIÓN DEL REPORTE CON BOTONES INTERACTIVOS ---
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA CON BOTONES* 📊\n"
            reporte += f"🔎 Analizadas: {total_analizadas} monedas de Binance\n\n"
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            reporte += f"Pincha el botón de cada moneda para ver su información detallada y análisis:\n"

            # Creamos la botonera interactiva en línea (Inline Keyboard)
            botones_inline = []

            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c, cid in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                
                # Agregamos texto en el reporte
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%`\n"
                
                # Creamos un botón interactivo para esta moneda específica
                # Al presionarlo, abrirá la ficha técnica con toda la información y opción de Binance
                fila_boton = [{
                    "text": f"🤖 Ver Análisis y Ficha de {nombre}",
                    "url": f"https://coinmarketcap.com/currencies/{cid}/"
                }]
                botones_inline.append(fila_boton)

            reporte += f"\n💎 *TOP 5 POTENCIAL (Acumulación)*\n"
            for s, p, v, c, cid in top_5_potencial:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟦")
                nombre = s.replace('/USDT', '')
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%`\n"
                
                fila_boton = [{
                    "text": f"💎 Analizar Potencial de {nombre}",
                    "url": f"https://coinmarketcap.com/currencies/{cid}/"
                }]
                botones_inline.append(fila_boton)

            # Estructura de teclado de Telegram
            teclado = {
                "inline_keyboard": botones_inline
            }

            self.enviar_mensaje_con_botones(reporte, teclado)
            print("✅ Reporte con Botones Interactivos enviado con éxito.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoConBotones()
    bot.ejecutar_analisis()
