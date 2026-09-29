import ccxt
import pandas as pd

# Conectarse a Binance (modo público para lectura de datos)
exchange = ccxt.binance()

def analizar_volumen_moneda(symbol='QI/USDT', timeframe='4h', limit=50):
    try:
        print(f"Analizando datos de {symbol} en Binance...")
        
        # Descargar datos históricos de velas de Binance
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        
        # Organizar los datos en una tabla estructurada
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calcular el volumen promedio histórico y el actual
        volumen_promedio = df['volume'].iloc[:-1].mean()
        volumen_actual = df['volume'].iloc[-1]
        
        print(f"\n--- Reporte para {symbol} ---")
        print(f"• Volumen promedio histórico: {volumen_promedio:,.2f}")
        print(f"• Volumen de la vela actual: {volumen_actual:,.2f}")
        
        # Detectar anomalía si el volumen actual duplica la media
        if volumen_actual > (volumen_promedio * 2.0):
            print(f"¡ALERTA! Movimiento de volumen anómalo detectado en {symbol}. Posible acumulación o ruptura.")
        else:
            print("El volumen se mantiene dentro de parámetros normales. Sin sorpresas.")
            
    except Exception as e:
        print(f"Ocurrió un error al consultar la API: {e}")

# Probar la función con QI/USDT
if __name__ == "__main__":
    analizar_volumen_moneda('QI/USDT', '4h', 50)