import requests
import os

class BotCriptoWebOficial:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        # Tu enlace web oficial de GitHub Pages
        self.url_web = "https://alejandrovallosp-boop.github.io/bot-cripto/"

    def enviar_mensaje(self, texto):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        if len(texto) > 4096:
            for x in range(0, len(texto), 4096):
                payload = {"chat_id": self.chat_id, "text": texto[x:x+4096], "parse_mode": "Markdown", "disable_web_page_preview": True}
                requests.post(url, json=payload)
        else:
            payload = {"chat_id": self.chat_id, "text": texto, "parse_mode": "Markdown", "disable_web_page_preview": True}
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
        print("🔍 Ejecutando escaneo con enlaces hacia la página web propia...")
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
            
            excluidos = {
                'btc-bitcoin', 'eth-ethereum', 'usdt-tether', 'usdc-usd-coin', 'sol-solana', 
                'xrp-xrp', 'ada-cardano', 'bnb-binance-coin', 'doge-dogecoin', 'near-near-protocol',
                'trx-tron', 'avax-avalanche', 'link-chainlink', 'matic-polygon', 'dot-polkadot'
            }

            all_coins = {}
            for coin in coins:
                coin_id = coin.get('id')
                if coin_id not in monedas_en_binance: continue
                sym = f"{coin.get('symbol', '').upper()}/USDT"
                quotes = coin.get('quotes', {}).get('USD', {})
                p = quotes.get('price', 0) or 0
                c = quotes.get('percent_change_24h', 0) or 0
                v = quotes.get('volume_24h', 0) or 0
                if p > 0: all_coins[sym] = {'precio': p, 'cambio': c, 'vol': v, 'id': coin_id}

            all_sorted = sorted(all_coins.items(), key=lambda x: x[1]['vol'], reverse=True)
            top_500 = dict(all_sorted[:500])
            total_analizadas = len(top_500)

            ganadoras, perdedoras = [], []
            for sym, data in top_500.items():
                item = (sym, data['precio'], data['vol'], data['cambio'], data['id'])
                if data['cambio'] > 0: ganadoras.append(item)
                elif data['cambio'] < 0: perdedoras.append(item)
            
            ganadoras.sort(key=lambda x: x[3], reverse=True)
            perdedoras.sort(key=lambda x: x[3])

            top_5_ganadoras = ganadoras[:5]
            top_5_perdedoras = perdedoras[:5]

            # FILTRO DE GEMAS < $1 USD EN ACUMULACIÓN
            gemas_acumulacion = []
            for sym, data in top_500.items():
                if data['id'] in excluidos: continue
                p = data['precio']
                c = data['cambio']
                v = data['vol']
                cid = data['id']
                if 0.0000001 < p < 1.0 and -4.0 <= c <= 4.0 and 50000 < v < 10000000:
                    gemas_acumulacion.append((sym, p, v, c, cid))

            gemas_acumulacion.sort(key=lambda x: x[2], reverse=True)
            top_5_gemas = gemas_acumulacion[:5]

            # --- CONSTRUCCIÓN DEL REPORTE ---
            reporte = f"🧠 *CENTRAL DE INTELIGENCIA (GEMINI AI)* 📊\n"
            reporte += f"🔎 Analizadas: {total_analizadas} altcoins de Binance (< $1 USD)\n\n"
            
            # 1. TOP 5 GANADORAS
            reporte += f"🚀 *TOP 5 GANADORAS*\n"
            max_ganancia = top_5_ganadoras[0][3] if top_5_ganadoras else 1
            for s, p, v, c, cid in top_5_ganadoras:
                barra = self.crear_grafico_barra(c, max_ganancia, "🟩")
                nombre = s.replace('/USDT', '')
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                link_web = f"{self.url_web}?coin={nombre}&price={p}&change={c:.1f}"
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `+{c:.1f}%`\n"
                reporte += f"   └ [📊 Resumen IA]({link_web}) | [🔸 Tradear]({link_binance})\n"

            # 2. TOP 5 GEMAS DE ACUMULACIÓN
            reporte += f"\n💎 *TOP 5 GEMAS EN ACUMULACIÓN (< $1.00 USD)*\n"
            if top_5_gemas:
                for s, p, v, c, cid in top_5_gemas:
                    nombre = s.replace('/USDT', '')
                    link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                    link_web = f"{self.url_web}?coin={nombre}&price={p}&change={c:.1f}"
                    reporte += f"🟢 *{nombre}* | `${self.formatear_precio(p)}` | Cambio: `{c:+.1f}%` | Vol: `${v:,.0f}`\n"
                    reporte += f"   └ [📊 Resumen IA]({link_web}) | [🔸 Tradear]({link_binance})\n"
            else:
                reporte += "Escaneando gemas económicas en silencio...\n"

            # 3. TOP 5 PERDEDORAS
            reporte += f"\n📉 *TOP 5 PERDEDORAS (Zonas de Rebote)*\n"
            max_perdida = top_5_perdedoras[0][3] if top_5_perdedoras else -1
            for s, p, v, c, cid in top_5_perdedoras:
                barra = self.crear_grafico_barra(c, max_perdida, "🟥")
                nombre = s.replace('/USDT', '')
                link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                link_web = f"{self.url_web}?coin={nombre}&price={p}&change={c:.1f}"
                reporte += f"• *{nombre}* | `${self.formatear_precio(p)}` | {barra} `{c:.1f}%`\n"
                reporte += f"   └ [📊 Resumen IA]({link_web}) | [🔸 Tradear]({link_binance})\n"

            # 4. FAVORITAS
            reporte += f"\n⭐ *ESTADO DE TUS FAVORITAS*\n"
            favoritos = ['LUNC/USDT', 'QI/USDT', 'SAGA/USDT', 'GRT/USDT', 'SOL/USDT', 'BANK/USDT', 'COS/USDT', 'ACE/USDT', 'ONDO/USDT']
            for fav in favoritos:
                if fav in all_coins: 
                    p_fav_val = all_coins[fav]['precio']
                    p_fav = self.formatear_precio(p_fav_val)
                    c_fav = all_coins[fav]['cambio']
                    icono = "🟢" if c_fav > 0 else "🔴"
                    nombre = fav.replace('/USDT', '')
                    link_binance = f"https://www.binance.com/es/trade/{nombre}_USDT"
                    link_web = f"{self.url_web}?coin={nombre}&price={p_fav_val}&change={c_fav:.1f}"
                    reporte += f"{icono} *{nombre}* | `${p_fav}` (`{c_fav:+.1f}%`)\n"
                    reporte += f"   └ [📊 Resumen IA]({link_web}) | [🔸 Tradear]({link_binance})\n"

            self.enviar_mensaje(reporte)
            print("✅ Reporte con enlaces a la web oficial enviado con éxito.")

        except Exception as e:
            print(f"❌ Error general: {e}")

if __name__ == "__main__":
    bot = BotCriptoWebOficial()
    bot.ejecutar_analisis()
