import pandas as pd
import streamlit as st
import plotly.express as px

# Cargar datos
@st.cache_data
def cargar_datos():
    df = pd.read_csv("call_logs_limpio_bigquery.csv", encoding="utf-8")
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
    elif "sms" in etiqueta or "text" in etiqueta:
        return "sms"
    else:
        return "otro"
df["etiqueta_original"] = df["etiqueta_original"].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()


df["tipo_llamada"] = df["etiqueta_original"].apply(extraer_tipo_llamada)

def extraer_tipo_llamada(etiqueta):
    if "perdida" in etiqueta or "missed" in etiqueta:
        return "perdida"
    elif "realizadas" in etiqueta or "placed" in etiqueta:
        return "realizada"
    elif "recibidas" in etiqueta or "received" in etiqueta or "inbox" in etiqueta:
        return "recibida"
    elif "sms" in etiqueta or "sms" in etiqueta:
        return "sms"
    else:
        return "otro"

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

fig_tiempo = px.bar(df_tiempo_agg, x="tipo_llamada", y="duracion_segundos",
                    title=f"Duración total de llamadas en {mes_seleccionado} {ano_seleccionado}",
                    labels={"tipo_llamada": "Tipo de llamada", "duracion_segundos": "Duración (segundos)"})
st.plotly_chart(fig_tiempo)

# Cantidad de llamadas por tipo en ese mes y año
df_cantidad_mes = df_filtrado[df_filtrado["tipo_llamada"].isin(["recibida", "realizada", "perdida"])]
df_cantidad_agg = df_cantidad_mes.groupby("tipo_llamada").size().reset_index(name="cantidad")

fig_cantidad = px.bar(df_cantidad_agg, x="tipo_llamada", y="cantidad",
                      title=f"Cantidad de llamadas en {mes_seleccionado} {ano_seleccionado}",
                      labels={"tipo_llamada": "Tipo de llamada", "cantidad": "Cantidad"})
st.plotly_chart(fig_cantidad)

# Gráfico pastel: Cantidad total por tipo de llamada
df_cantidades_total = df[df["tipo_llamada"].isin(["recibida", "realizada", "sms", "perdida"])]
df_cantidades_total = df_cantidades_total.groupby("tipo_llamada").size().reset_index(name="cantidad")

fig_cantidad_total = px.pie(df_cantidades_total, values="cantidad", names="tipo_llamada",
                            title="Cantidad total por tipo de llamada")
st.plotly_chart(fig_cantidad_total)


# Contador de llamadas totales en ese mes/año
total_llamadas_filtradas = len(df_filtrado)
st.metric(label="Total de registros en el mes/año seleccionado", value=total_llamadas_filtradas)

# ----------------------
# Gráfico de mensajes vs llamadas perdidas
# ----------------------

df_sms_y_perdidas = df_filtrado[df_filtrado["tipo_llamada"].isin(["sms", "perdida"])]
df_sms_perdidas_agg = df_sms_y_perdidas.groupby("tipo_llamada").size().reset_index(name="cantidad")

fig_sms_perdidas = px.bar(df_sms_perdidas_agg, x="tipo_llamada", y="cantidad",
                          title=f"📬 Mensajes vs 📵 Llamadas Perdidas - {mes_seleccionado} {ano_seleccionado}",
                          labels={"tipo_llamada": "Tipo", "cantidad": "Cantidad"})
st.plotly_chart(fig_sms_perdidas)

# ----------------------
# Contadores individuales
# ----------------------

total_mensajes_mes = df_sms_y_perdidas[df_sms_y_perdidas["tipo_llamada"] == "sms"].shape[0]
total_perdidas_mes = df_sms_y_perdidas[df_sms_y_perdidas["tipo_llamada"] == "perdida"].shape[0]

col1, col2 = st.columns(2)
with col1:
    st.metric("📬 Total de Mensajes (SMS)", total_mensajes_mes)
with col2:
    st.metric("📵 Total de Llamadas Perdidas", total_perdidas_mes)
# ----------------------
# Gráfico mensual de SMS y llamadas perdidas en el año seleccionado
# ----------------------

df_anual = df[df["ao"] == ano_seleccionado]
df_anual_sms_perdidas = df_anual[df_anual["tipo_llamada"].isin(["sms", "perdida"])]

# Agrupar por mes y tipo
df_mensual_agg = df_anual_sms_perdidas.groupby(["mes", "tipo_llamada"]).size().reset_index(name="cantidad")
df_mensual_agg["mestexto"] = df_mensual_agg["mes"].map(meses)

# Ordenar los meses correctamente
orden_meses = list(meses.values())
df_mensual_agg["mestexto"] = pd.Categorical(df_mensual_agg["mestexto"], categories=orden_meses, ordered=True)
df_mensual_agg = df_mensual_agg.sort_values("mestexto")

# Gráfico de barras agrupadas
fig_mensual = px.bar(df_mensual_agg, x="mestexto", y="cantidad", color="tipo_llamada", barmode="group",
                     title=f"📅 Cantidad de SMS y Llamadas Perdidas por Mes - {ano_seleccionado}",
                     labels={"mestexto": "Mes", "cantidad": "Cantidad", "tipo_llamada": "Tipo"})
st.plotly_chart(fig_mensual)
