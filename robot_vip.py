import os
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from tabulate import tabulate
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN SEGURA (GitHub leerá esto de tus 'Secrets') ---
MI_CORREO = os.environ.get('MI_CORREO')
MI_CLAVE = os.environ.get('MI_CLAVE')

def enviar_email(tabla_html, noticias_html):
    if not MI_CORREO or not MI_CLAVE:
        print("❌ Error: No se han configurado los Secretos en GitHub.")
        return

    msg = MIMEMultipart()
    msg['From'] = MI_CORREO
    msg['To'] = MI_CORREO
    msg['Subject'] = "🚀 TOP Oportunidades Insiders (Informe Automático)"
    
    cuerpo = f"<html><body><h2>📊 Informe VIP</h2>{tabla_html}<br>{noticias_html}</body></html>"
    msg.attach(MIMEText(cuerpo, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(MI_CORREO, MI_CLAVE)
        server.send_message(msg)
        server.quit()
        print("✅ ¡Email enviado con éxito!")
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")

def ejecutar_rastreador():
    print("--- 🕵️ RASTREANDO COMPRAS VIP (>100k) ---")
    url = "http://openinsider.com/insider-purchases-100k"
    headers = {'User-Agent': 'Mozilla/5.0'}
    cambio_eur = 0.93 

    try:
        respuesta = requests.get(url, headers=headers)
        sopa = BeautifulSoup(respuesta.text, 'html.parser')
        tabla_web = sopa.find('table', {'class': 'tinytable'})
        
        if not tabla_web:
            print("❌ No se pudo leer la tabla de OpenInsider.")
            return

        filas = tabla_web.find_all('tr')[1:50] # Analizamos las 50 más recientes
        datos_lista = []
        html_noticias = ""

        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) < 12: continue
            
            try:
                ticker = cols[3].text.strip().replace('$', '')
                precio_jefe_eur = float(cols[8].text.strip().replace('$', '').replace(',', '').replace('%', '')) * cambio_eur
                inversion_eur = float(cols[11].text.strip().replace('$', '').replace(',', '').replace('%', '')) * cambio_eur

                if inversion_eur >= 100000:
                    stock = yf.Ticker(ticker)
                    precio_hoy_eur = stock.history(period="1d")['Close'].iloc[-1] * cambio_eur
                    nombre = stock.info.get('longName', ticker)
                    
                    datos_lista.append({
                        'Empresa': nombre[:25],
                        'Cargo': cols[5].text.strip()[:15],
                        'Inversión (€)': f"{int(inversion_eur):,} €",
                        'Precio Jefe (€)': round(precio_jefe_eur, 2),
                        'Precio Ahora (€)': round(precio_hoy_eur, 2),
                        '¿Ganga?': "SI ✅" if precio_hoy_eur < precio_jefe_eur else "NO"
                    })
                    
                    # Añadir noticias al final del email
                    html_noticias += f"<h4>🏢 {nombre}</h4><ul>"
                    for n in stock.news[:1]:
                        html_noticias += f"<li>{n['title']}</li>"
                    html_noticias += "</ul>"
            except:
                continue

        if datos_lista:
            df = pd.DataFrame(datos_lista).sort_values(by='Inversión (€)', ascending=False)
            enviar_email(df.to_html(index=False), html_noticias)
        else:
            print("No se han detectado compras hoy.")

    except Exception as e:
        print(f"Error crítico: {e}")

if __name__ == "__main__":
    ejecutar_rastreador()