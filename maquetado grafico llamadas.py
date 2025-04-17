import pandas as pd
import streamlit as st
import plotly.express as px
import zipfile
import os

# Ruta al archivo ZIP y directorio de salida
zip_path = 'call_logs_limpio_bigquery.zip'
output_dir = 'data'
csv_path = os.path.join(output_dir, 'call_logs_limpio_bigquery.csv')

# Descomprimir el archivo ZIP si no existe el CSV
if not os.path.exists(csv_path):
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
    else:
        st.error(f"El archivo ZIP {zip_path} no se encuentra en el directorio.")

# Cargar el DataFrame
@st.cache_data
def cargar_datos():
    df = pd.read_csv(csv_path, encoding="utf-8")
    df["fecha_datetime"] = pd.to_datetime(df["fecha_datetime"], errors="coerce")
    df = df.dropna(subset=["fecha_datetime"])
    return df

df = cargar_datos()

# Clasificar tipo de llamada
def extraer_tipo_llamada(etiqueta):
    etiqueta = str(etiqueta).lower()
    if "perdida" in etiqueta or "missed" in etiqueta:
        return "perdida"
    elif "realizadas" in etiqueta or "placed" in etiqueta:
        return "realizada"
    elif "recibidas" in etiqueta or "received" in etiqueta or "inbox" in etiqueta:
        return "recibida"
    else:
        return "otro"

df["etiqueta_original"] = df["etiqueta_original"].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
df["tipo_llamada"] = df["etiqueta_original"].apply(extraer_tipo_llamada)

# Agregar columnas de año, mes y mes texto
df["ao"] = df["fecha_datetime"].dt.year
df["mes"] = df["fecha_datetime"].dt.month
meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
df["mestexto"] = df["mes"].map(meses)

# Filtros
st.title("📊 Análisis de Llamadas")
anos_disponibles = sorted(df["ao"].dropna().unique())
meses_disponibles = list(meses.values())

ano_seleccionado = st.selectbox("Selecciona un año", anos_disponibles)
mes_seleccionado = st.selectbox("Selecciona un mes", meses_disponibles)

# Filtrar por selección
mes_num = list(meses.keys())[list(meses.values()).index(mes_seleccionado)]
df_filtrado = df[(df["ao"] == ano_seleccionado) & (df["mes"] == mes_num)]

# Tiempo de llamadas recibidas y realizadas
df_tiempo = df_filtrado[df_filtrado["tipo_llamada"].isin(["recibida", "realizada"])]
df_tiempo_agg = df_tiempo.groupby("tipo_llamada")["duracion_segundos"].sum().reset_index()

# Mejorando los colores y la visibilidad de los gráficos
fig_tiempo = px.bar(df_tiempo_agg, x="tipo_llamada", y="duracion_segundos",
                    title=f"Duración total de llamadas en {mes_seleccionado} {ano_seleccionado}",
                    labels={"tipo_llamada": "Tipo de llamada", "duracion_segundos": "Duración (segundos)"},
                    color="tipo_llamada", color_discrete_map={"recibida": "green", "realizada": "blue"})
fig_tiempo.update_layout(title_x=0.5, title_font_size=20, title_font_family="Arial", template="plotly_white")
st.plotly_chart(fig_tiempo)

# Cantidad de llamadas por tipo en ese mes y año
df_cantidad_mes = df_filtrado[df_filtrado["tipo_llamada"].isin(["recibida", "realizada", "perdida"])]
df_cantidad_agg = df_cantidad_mes.groupby("tipo_llamada").size().reset_index(name="cantidad")

fig_cantidad = px.bar(df_cantidad_agg, x="tipo_llamada", y="cantidad",
                      title=f"Cantidad de llamadas en {mes_seleccionado} {ano_seleccionado}",
                      labels={"tipo_llamada": "Tipo de llamada", "cantidad": "Cantidad"},
                      color="tipo_llamada", color_discrete_map={"recibida": "green", "realizada": "blue", "perdida": "red"})
fig_cantidad.update_layout(title_x=0.5, title_font_size=20, title_font_family="Arial", template="plotly_white")
st.plotly_chart(fig_cantidad)

# Gráfico pastel: Cantidad total por tipo de llamada
df_cantidades_total = df[df["tipo_llamada"].isin(["recibida", "realizada", "perdida"])]
df_cantidades_total = df_cantidades_total.groupby("tipo_llamada").size().reset_index(name="cantidad")

fig_cantidad_total = px.pie(df_cantidades_total, values="cantidad", names="tipo_llamada",
                            title="Cantidad total por tipo de llamada",
                            color_discrete_map={"recibida": "green", "realizada": "blue", "perdida": "red"})
fig_cantidad_total.update_layout(title_x=0.5, title_font_size=20, title_font_family="Arial", template="plotly_white")
st.plotly_chart(fig_cantidad_total)

# Contador de llamadas totales en ese mes/año
total_llamadas_filtradas = len(df_filtrado)
st.metric(label="Total de registros en el mes/año seleccionado", value=total_llamadas_filtradas)

# Duración promedio de llamadas
df_promedio = df_filtrado[df_filtrado["tipo_llamada"] != "otro"]
df_promedio_agg = df_promedio.groupby("tipo_llamada")["duracion_segundos"].mean().reset_index()

fig_promedio = px.bar(df_promedio_agg, x="tipo_llamada", y="duracion_segundos",
                      title=f"Duración promedio de llamadas en {mes_seleccionado} {ano_seleccionado}",
                      labels={"tipo_llamada": "Tipo de llamada", "duracion_segundos": "Duración promedio (segundos)"},
                      color="tipo_llamada", color_discrete_map={"recibida": "green", "realizada": "blue", "perdida": "red"})
fig_promedio.update_layout(title_x=0.5, title_font_size=20, title_font_family="Arial", template="plotly_white")
st.plotly_chart(fig_promedio)

# Distribución de llamadas por hora
df_filtrado["hora"] = df_filtrado["fecha_datetime"].dt.hour
df_distribucion_hora = df_filtrado.groupby("hora").size().reset_index(name="cantidad")

fig_distribucion_hora = px.line(df_distribucion_hora, x="hora", y="cantidad",
                                 title=f"Distribución de llamadas por hora en {mes_seleccionado} {ano_seleccionado}",
                                 labels={"hora": "Hora", "cantidad": "Cantidad de llamadas"})
fig_distribucion_hora.update_layout(title_x=0.5, title_font_size=20, title_font_family="Arial", template="plotly_white")
st.plotly_chart(fig_distribucion_hora)

