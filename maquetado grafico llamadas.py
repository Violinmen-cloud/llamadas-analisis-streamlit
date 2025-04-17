import pandas as pd
import streamlit as st
import plotly.express as px
import zipfile
import os

# Definir rutas
zip_path = 'call_logs_limpio_bigquery.zip'
output_dir = 'data'
csv_path = os.path.join(output_dir, 'call_logs_limpio_bigquery.csv')

# Descomprimir si aún no existe el CSV
if not os.path.exists(csv_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

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

# Mejorando el gráfico de tiempo total
fig_tiempo = px.bar(df_tiempo_agg, x="tipo_llamada", y="duracion_segundos",
                    title=f"Duración total de llamadas en {mes_seleccionado} {ano_seleccionado}",
                    labels={"tipo_llamada": "Tipo de llamada", "duracion_segundos": "Duración (segundos)"})
fig_tiempo.update_layout(
    title_font=dict(size=24, family='Verdana', color='darkblue'),
    xaxis_title="Tipo de Llamada", yaxis_title="Duración (segundos)",
    plot_bgcolor='white', font=dict(family='Arial', size=12, color='black'),
    showlegend=False
)
fig_tiempo.update_traces(marker=dict(color='rgb(0, 204, 255)'))  # Cambiar el color de las barras
st.plotly_chart(fig_tiempo)

# Cantidad de llamadas por tipo en ese mes y año
df_cantidad_mes = df_filtrado[df_filtrado["tipo_llamada"].isin(["recibida", "realizada", "perdida"])]
df_cantidad_agg = df_cantidad_mes.groupby("tipo_llamada").size().reset_index(name="cantidad")

# Mejorando el gráfico de cantidad por tipo de llamada
fig_cantidad = px.bar(df_cantidad_agg, x="tipo_llamada", y="cantidad",
                      title=f"Cantidad de llamadas en {mes_seleccionado} {ano_seleccionado}",
                      labels={"tipo_llamada": "Tipo de llamada", "cantidad": "Cantidad"})
fig_cantidad.update_layout(
    hovermode='x unified',
    title="Cantidad de llamadas por tipo",
    xaxis_tickangle=-45,
    xaxis_title="Tipo de llamada",
    yaxis_title="Cantidad de llamadas"
)
st.plotly_chart(fig_cantidad)

# Gráfico pastel: Cantidad total por tipo de llamada
df_cantidades_total = df[df["tipo_llamada"].isin(["recibida", "realizada", "perdida"])]
df_cantidades_total = df_cantidades_total.groupby("tipo_llamada").size().reset_index(name="cantidad")

# Mejorando el gráfico de pastel
fig_cantidad_total = px.pie(df_cantidades_total, values="cantidad", names="tipo_llamada",
                            title="Cantidad total por tipo de llamada",
                            color_discrete_sequence=["rgb(0, 204, 255)", "rgb(255, 85, 85)", "rgb(85, 255, 85)"])
fig_cantidad_total.update_layout(
    title_font=dict(size=24, family='Verdana', color='darkblue'),
    font=dict(family='Arial', size=12, color='black')
)
st.plotly_chart(fig_cantidad_total)

# Contador de llamadas totales en ese mes/año
total_llamadas_filtradas = len(df_filtrado)
st.metric(label="Total de registros en el mes/año seleccionado", value=total_llamadas_filtradas)

# ----------------------
# Gráfico de llamadas perdidas
# ----------------------

df_perdidas = df_filtrado[df_filtrado["tipo_llamada"] == "perdida"]
df_perdidas_agg = df_perdidas.groupby("tipo_llamada").size().reset_index(name="cantidad")

# Mejorando gráfico de llamadas perdidas
fig_perdidas = px.bar(df_perdidas_agg, x="tipo_llamada", y="cantidad",
                      title=f"📵 Llamadas Perdidas - {mes_seleccionado} {ano_seleccionado}",
                      labels={"tipo_llamada": "Tipo", "cantidad": "Cantidad"})
fig_perdidas.update_layout(
    title_font=dict(size=24, family='Verdana', color='darkblue'),
    xaxis_title="Tipo de llamada",
    yaxis_title="Cantidad",
    font=dict(family='Arial', size=12, color='black'),
    showlegend=False
)
fig_perdidas.update_traces(marker=dict(color='rgb(255, 85, 85)'))  # Color rojo para las llamadas perdidas
st.plotly_chart(fig_perdidas)

# ----------------------
# Contadores individuales
# ----------------------

total_perdidas_mes = df_perdidas.shape[0]

# Mostrar contadores
col1, col2 = st.columns(2)
with col1:
    st.metric("📵 Total de Llamadas Perdidas", total_perdidas_mes)

# ----------------------
# Gráfico mensual de llamadas perdidas
# ----------------------

df_anual = df[df["ao"] == ano_seleccionado]
df_anual_perdidas = df_anual[df_anual["tipo_llamada"] == "perdida"]

# Agrupar por mes
df_mensual_agg = df_anual_perdidas.groupby(["mes"]).size().reset_index(name="cantidad")
df_mensual_agg["mestexto"] = df_mensual_agg["mes"].map(meses)

# Ordenar los meses correctamente
orden_meses = list(meses.values())
df_mensual_agg["mestexto"] = pd.Categorical(df_mensual_agg["mestexto"], categories=orden_meses, ordered=True)
df_mensual_agg = df_mensual_agg.sort_values("mestexto")

# Mejorando gráfico de llamadas perdidas por mes
fig_mensual = px.bar(df_mensual_agg, x="mestexto", y="cantidad", 
                     title=f"📅 Llamadas Perdidas por Mes - {ano_seleccionado}",
                     labels={"mestexto": "Mes", "cantidad": "Cantidad"})
fig_mensual.update_layout(
    title_font=dict(size=24, family='Verdana', color='darkblue'),
    xaxis_title="Mes",
    yaxis_title="Cantidad",
    font=dict(family='Arial', size=12, color='black'),
    showlegend=False
)
fig_mensual.update_traces(marker=dict(line=dict(color='rgb(255, 85, 85)', width=2)))  # Mejora visual en las barras
st.plotly_chart(fig_mensual)
