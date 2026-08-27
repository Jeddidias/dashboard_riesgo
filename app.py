"""
Dashboard de Riesgo Psicosocial — Departamento de Escalaciones
Basado en Batería del Ministerio del Trabajo (2025)
 
Uso: python app.py
"""
 
import io
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import os
 
# ─────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────
CSV_PATH = "datos_ejemplo.csv"
 
ORDEN_NIVELES = ["Sin riesgo", "Bajo", "Medio", "Alto", "Muy alto"]
 
COLOR_MAPA = {
    "Sin riesgo": "#27AE60",
    "Bajo":       "#27AE60",
    "Medio":      "#F1C40F",
    "Alto":       "#E74C3C",
    "Muy alto":   "#C0392B",
}
 
COLOR_FONDO_TABLA = {
    "Sin riesgo": "#D5F5E3",
    "Bajo":       "#D5F5E3",
    "Medio":      "#FCF3CF",
    "Alto":       "#FADBD8",
    "Muy alto":   "#F1948A",
}
 
FUENTE = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
 
# ─────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────
def cargar_datos():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"No se encontró el archivo: {CSV_PATH}")
 
    # Intentar UTF-8 con BOM primero, luego latin-1
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            df = pd.read_csv(CSV_PATH, dtype=str, encoding=enc)
            # Verificar que las columnas clave existen
            if "nivel_riesgo_global" in df.columns:
                break
        except Exception:
            continue
 
    # Columnas numéricas
    for col in ["dominio_intralaboral_puntaje", "dominio_extralaboral_puntaje",
                "puntaje_total_individual"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
 
    if "antigüedad_meses" in df.columns:
        df["antigüedad_meses"] = pd.to_numeric(df["antigüedad_meses"], errors="coerce").astype("Int64")
 
    for col in ["campaña", "antigüedad_meses"]:
        if col not in df.columns:
            df[col] = None
 
    for col in ["dominio_intralaboral_nivel", "dominio_extralaboral_nivel", "nivel_riesgo_global"]:
        if col in df.columns:
            df[col] = df[col].str.strip()
 
    print("Columnas detectadas:", list(df.columns))
    print("Filas cargadas:", len(df))
    return df
 
# ─────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────
df_global = cargar_datos()
tiene_campana = "campaña" in df_global.columns and df_global["campaña"].notna().any()
 
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Dashboard Riesgo Psicosocial",
)
app.config.suppress_callback_exceptions = True
 
# ─────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────
ESTILO_TARJETA = {
    "background": "#FFFFFF",
    "borderRadius": "10px",
    "padding": "18px 20px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "textAlign": "center",
    "fontFamily": FUENTE,
}
 
ESTILO_VALOR = {
    "fontSize": "28px",
    "fontWeight": "700",
    "margin": "4px 0",
    "fontFamily": FUENTE,
    "color": "#2C3E50",
}
 
ESTILO_ETIQUETA = {
    "fontSize": "13px",
    "color": "#6C757D",
    "fontFamily": FUENTE,
    "marginBottom": "0",
}
 
def tarjeta(id_valor, etiqueta_texto, color_valor="#2C3E50", color_fondo="#FFFFFF", borde_color=None):
    estilo = {**ESTILO_TARJETA, "background": color_fondo}
    if borde_color:
        estilo["borderLeft"] = f"5px solid {borde_color}"
    return html.Div([
        html.P(etiqueta_texto, style=ESTILO_ETIQUETA),
        html.H3(id=id_valor, style={**ESTILO_VALOR, "color": color_valor}),
    ], style=estilo)
 
def seccion_titulo(texto):
    return html.H5(texto, style={
        "fontFamily": FUENTE,
        "color": "#2C3E50",
        "fontWeight": "600",
        "marginBottom": "10px",
        "marginTop": "24px",
        "borderBottom": "2px solid #E8EDF2",
        "paddingBottom": "6px",
    })
 
# ─────────────────────────────────────────
# OPCIONES DE FILTROS
# ─────────────────────────────────────────
opciones_nivel = [{"label": "Todos los niveles", "value": "Todos"}] + [
    {"label": n, "value": n} for n in ORDEN_NIVELES
]
 
opciones_campana = [{"label": "Todas las campañas", "value": "Todos"}]
if tiene_campana:
    campanas_unicas = sorted(df_global["campaña"].dropna().unique().tolist())
    opciones_campana += [{"label": c, "value": c} for c in campanas_unicas]
 
columnas_tabla = [
    {"name": "ID Anónimo",       "id": "id_anonimo",                   "type": "text"},
    {"name": "Nivel de Riesgo",  "id": "nivel_riesgo_global",          "type": "text"},
    {"name": "Intralaboral",     "id": "dominio_intralaboral_puntaje", "type": "numeric",
     "format": dash_table.Format.Format(precision=1, scheme=dash_table.Format.Scheme.fixed)},
    {"name": "Extralaboral",     "id": "dominio_extralaboral_puntaje", "type": "numeric",
     "format": dash_table.Format.Format(precision=1, scheme=dash_table.Format.Scheme.fixed)},
    {"name": "Puntaje Total",    "id": "puntaje_total_individual",     "type": "numeric",
     "format": dash_table.Format.Format(precision=1, scheme=dash_table.Format.Scheme.fixed)},
]
if tiene_campana:
    columnas_tabla.append({"name": "Campaña", "id": "campaña", "type": "text"})
if df_global["antigüedad_meses"].notna().any():
    columnas_tabla.append({"name": "Antigüedad (meses)", "id": "antigüedad_meses", "type": "numeric"})
 
# ─────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────
app.layout = html.Div(
    style={"background": "#F4F7FC", "minHeight": "100vh", "fontFamily": FUENTE},
    children=[
 
        # Encabezado
        html.Div(
            style={"background": "#2C3E50", "color": "white", "padding": "22px 32px", "marginBottom": "24px"},
            children=[
                html.H1("Dashboard de Riesgo Psicosocial — Departamento de Escalaciones",
                        style={"fontSize": "26px", "fontWeight": "700", "marginBottom": "4px", "color": "white"}),
                html.P("Basado en Batería del Ministerio del Trabajo (2025)",
                       style={"fontSize": "15px", "opacity": "0.8", "marginBottom": "0"}),
            ],
        ),
 
        html.Div(
            style={"maxWidth": "1300px", "margin": "0 auto", "padding": "0 24px 40px"},
            children=[
 
                # Filtros
                html.Div(
                    style={
                        "background": "#FFFFFF", "borderRadius": "10px", "padding": "16px 20px",
                        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)", "marginBottom": "20px",
                        "display": "flex", "alignItems": "center", "gap": "16px", "flexWrap": "wrap",
                    },
                    children=[
                        html.Div([
                            html.Label("Nivel de riesgo", style={"fontSize": "12px", "color": "#6C757D", "fontWeight": "600"}),
                            dcc.Dropdown(id="filtro-nivel", options=opciones_nivel, value="Todos",
                                         clearable=False, searchable=False,
                                         style={"width": "220px", "fontSize": "13px"}),
                        ]),
                        html.Div([
                            html.Label("Campaña", style={"fontSize": "12px", "color": "#6C757D", "fontWeight": "600"}),
                            dcc.Dropdown(id="filtro-campana", options=opciones_campana, value="Todos",
                                         clearable=False, searchable=False, disabled=False,
                                         style={"width": "220px", "fontSize": "13px"}),
                        ]),
                        html.Div(
                            style={"marginLeft": "auto", "paddingTop": "16px"},
                            children=[
                                html.Button("↻  Refrescar datos", id="btn-refrescar", n_clicks=0,
                                            style={"background": "#2C3E50", "color": "white", "border": "none",
                                                   "borderRadius": "6px", "padding": "9px 20px", "fontSize": "13px",
                                                   "cursor": "pointer", "fontFamily": FUENTE}),
                                html.Span(id="msg-refresh", style={"fontSize": "12px", "color": "#27AE60", "marginLeft": "10px"}),
                            ],
                        ),
                    ],
                ),
 
                # Alerta
                html.Div(id="alerta-riesgo", style={"marginBottom": "16px"}),
 
                # Tarjetas
                seccion_titulo("Resumen del grupo filtrado"),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "14px", "marginBottom": "24px"},
                    children=[
                        tarjeta("val-total", "Total empleados"),
                        tarjeta("val-alto", "Riesgo alto / muy alto", color_valor="#C0392B", color_fondo="#FEF0EF", borde_color="#E74C3C"),
                        tarjeta("val-medio", "Riesgo medio", color_valor="#9A6700", color_fondo="#FFFBEB", borde_color="#F1C40F"),
                        tarjeta("val-bajo", "Riesgo bajo / sin riesgo", color_valor="#1A7A3E", color_fondo="#F0FBF4", borde_color="#27AE60"),
                    ],
                ),
 
                # Gráficos superiores
                seccion_titulo("Distribución de riesgo"),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px", "marginBottom": "24px"},
                    children=[
                        html.Div(style={**ESTILO_TARJETA, "padding": "16px"}, children=[
                            html.P("Distribución por nivel de riesgo",
                                   style={"fontWeight": "600", "marginBottom": "4px", "color": "#2C3E50", "fontSize": "14px"}),
                            dcc.Graph(id="graf-barras", config={"displayModeBar": False}, style={"height": "300px"}),
                        ]),
                        html.Div(style={**ESTILO_TARJETA, "padding": "16px"}, children=[
                            html.P("Histograma de puntaje total individual",
                                   style={"fontWeight": "600", "marginBottom": "4px", "color": "#2C3E50", "fontSize": "14px"}),
                            dcc.Graph(id="graf-histograma", config={"displayModeBar": False}, style={"height": "300px"}),
                        ]),
                    ],
                ),
 
                # Radar
                seccion_titulo("Promedio de dominios (grupo filtrado)"),
                html.Div(style={**ESTILO_TARJETA, "padding": "16px", "marginBottom": "24px"}, children=[
                    html.P("Radar comparativo por dominio",
                           style={"fontWeight": "600", "marginBottom": "4px", "color": "#2C3E50", "fontSize": "14px"}),
                    dcc.Graph(id="graf-radar", config={"displayModeBar": False}, style={"height": "340px"}),
                ]),
 
                # Tabla
                seccion_titulo("Detalle de empleados"),
                html.Div(style={**ESTILO_TARJETA, "padding": "16px"}, children=[
                    html.Div(style={"marginBottom": "10px"}, children=[
                        dcc.Input(id="busqueda-id", type="text", placeholder="🔍  Buscar por ID anónimo…",
                                  debounce=True,
                                  style={"width": "300px", "padding": "8px 12px", "borderRadius": "6px",
                                         "border": "1px solid #DEE2E6", "fontSize": "13px", "fontFamily": FUENTE}),
                    ]),
                    dash_table.DataTable(
                        id="tabla-empleados",
                        columns=columnas_tabla,
                        data=[],
                        sort_action="native",
                        sort_mode="single",
                        page_size=15,
                        page_action="native",
                        style_table={"overflowX": "auto"},
                        style_header={"backgroundColor": "#F4F7FC", "fontWeight": "600", "fontSize": "13px",
                                      "color": "#2C3E50", "border": "1px solid #DEE2E6", "fontFamily": FUENTE},
                        style_cell={"fontFamily": FUENTE, "fontSize": "13px", "padding": "10px 14px",
                                    "border": "1px solid #F0F3F7", "textAlign": "left"},
                        style_data_conditional=[],
                    ),
                ]),
            ],
        ),
    ],
)
 
# ─────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────
 
@app.callback(
    Output("msg-refresh", "children"),
    Input("btn-refrescar", "n_clicks"),
    prevent_initial_call=True,
)
def refrescar_mensaje(n_clicks):
    cargar_datos()  # solo para validar que el archivo existe
    return "✔ Datos actualizados"
 
 
@app.callback(
    Output("val-total",  "children"),
    Output("val-alto",   "children"),
    Output("val-medio",  "children"),
    Output("val-bajo",   "children"),
    Output("alerta-riesgo", "children"),
    Output("graf-barras", "figure"),
    Output("graf-histograma", "figure"),
    Output("graf-radar", "figure"),
    Output("tabla-empleados", "data"),
    Output("tabla-empleados", "style_data_conditional"),
    Input("filtro-nivel", "value"),
    Input("filtro-campana", "value"),
    Input("busqueda-id", "value"),
    Input("btn-refrescar", "n_clicks"),
)
def actualizar_dashboard(nivel, campana, busqueda, n_clicks):
    # Siempre releer el CSV desde disco
    df = cargar_datos()
 
    # Aplicar filtros
    if nivel and nivel != "Todos":
        df = df[df["nivel_riesgo_global"] == nivel]
    if campana and campana != "Todos" and "campaña" in df.columns:
        df = df[df["campaña"] == campana]
    if busqueda and busqueda.strip():
        df = df[df["id_anonimo"].str.upper().str.contains(busqueda.strip().upper(), na=False)]
 
    total = len(df)
 
    # ── Tarjetas ──────────────────────────────────────────────
    if total == 0:
        val_total, val_alto, val_medio, val_bajo, pct_alto = "0", "0%", "0%", "0%", 0
    else:
        n_alto  = df["nivel_riesgo_global"].isin(["Alto", "Muy alto"]).sum()
        n_medio = (df["nivel_riesgo_global"] == "Medio").sum()
        n_bajo  = df["nivel_riesgo_global"].isin(["Bajo", "Sin riesgo"]).sum()
        pct_alto  = round(n_alto  / total * 100, 1)
        pct_medio = round(n_medio / total * 100, 1)
        pct_bajo  = round(n_bajo  / total * 100, 1)
        val_total = str(total)
        val_alto  = f"{pct_alto}%"
        val_medio = f"{pct_medio}%"
        val_bajo  = f"{pct_bajo}%"
 
    # ── Alerta ─────────────────────────────────────────────────
    alerta = None
    if total > 0 and pct_alto > 30:
        alerta = html.Div(
            "⚠  ¡ALERTA! Más del 30 % de los empleados filtrados se encuentran en riesgo Alto o Muy alto.",
            style={"background": "#FADBD8", "border": "2px solid #E74C3C", "borderRadius": "8px",
                   "padding": "14px 20px", "color": "#922B21", "fontSize": "15px",
                   "fontWeight": "600", "fontFamily": FUENTE},
        )
 
    # ── Gráfico 1: Barras ──────────────────────────────────────
    conteos = (df["nivel_riesgo_global"].value_counts()
               .reindex(ORDEN_NIVELES, fill_value=0).reset_index())
    conteos.columns = ["Nivel", "Cantidad"]
 
    fig_barras = go.Figure(go.Bar(
        x=conteos["Nivel"], y=conteos["Cantidad"],
        marker_color=[COLOR_MAPA.get(n, "#7F8C8D") for n in conteos["Nivel"]],
        text=conteos["Cantidad"], textposition="outside",
        hovertemplate="%{x}: %{y} empleados<extra></extra>",
    ))
    fig_barras.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis=dict(title=None, tickfont=dict(family=FUENTE, size=12)),
        yaxis=dict(title="Cantidad", tickfont=dict(family=FUENTE, size=11), gridcolor="#F0F3F7"),
        showlegend=False, font=dict(family=FUENTE),
    )
 
    # ── Gráfico 2: Histograma ──────────────────────────────────
    fig_hist = go.Figure()
    puntajes = df["puntaje_total_individual"].dropna() if total > 0 else pd.Series([], dtype=float)
    if not puntajes.empty:
        mediana = puntajes.median()
        fig_hist.add_trace(go.Histogram(
            x=puntajes, nbinsx=12, marker_color="#3498DB",
            marker_line=dict(color="white", width=1), opacity=0.85,
            hovertemplate="Rango: %{x}<br>Frecuencia: %{y}<extra></extra>",
        ))
        fig_hist.add_vline(x=mediana, line_dash="dash", line_color="#E74C3C", line_width=2,
                           annotation_text=f"Mediana: {mediana:.1f}",
                           annotation_position="top right",
                           annotation_font=dict(color="#C0392B", size=11, family=FUENTE))
    else:
        fig_hist.add_annotation(text="Sin datos", x=0.5, y=0.5, showarrow=False,
                                 font=dict(size=14, family=FUENTE))
    fig_hist.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis=dict(title="Puntaje total (0–100)", tickfont=dict(family=FUENTE, size=11)),
        yaxis=dict(title="Frecuencia", tickfont=dict(family=FUENTE, size=11), gridcolor="#F0F3F7"),
        bargap=0.06, font=dict(family=FUENTE),
    )
 
    # ── Gráfico 3: Radar ───────────────────────────────────────
    prom_intra = round(df["dominio_intralaboral_puntaje"].mean(), 1) if total > 0 and df["dominio_intralaboral_puntaje"].notna().any() else 0
    prom_extra = round(df["dominio_extralaboral_puntaje"].mean(), 1) if total > 0 and df["dominio_extralaboral_puntaje"].notna().any() else 0
 
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[prom_intra, prom_extra, prom_intra],
        theta=["Intralaboral", "Extralaboral", "Intralaboral"],
        fill="toself", fillcolor="rgba(52,152,219,0.20)",
        line=dict(color="#2980B9", width=2), marker=dict(size=8, color="#2980B9"),
        name="Promedio del grupo",
        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=10, family=FUENTE), gridcolor="#E8EDF2"),
            angularaxis=dict(tickfont=dict(size=13, family=FUENTE, color="#2C3E50")),
            bgcolor="white",
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=True, legend=dict(font=dict(family=FUENTE, size=12)),
        font=dict(family=FUENTE),
        annotations=[dict(
            x=0.5, y=1.12, xref="paper", yref="paper",
            text=f"Intralaboral: <b>{prom_intra}</b> &nbsp;|&nbsp; Extralaboral: <b>{prom_extra}</b>",
            showarrow=False, font=dict(size=13, family=FUENTE, color="#2C3E50"),
        )],
    )
 
    # ── Tabla ──────────────────────────────────────────────────
    cols_mostrar = ["id_anonimo", "nivel_riesgo_global",
                    "dominio_intralaboral_puntaje", "dominio_extralaboral_puntaje",
                    "puntaje_total_individual"]
    if tiene_campana:
        cols_mostrar.append("campaña")
    if "antigüedad_meses" in df.columns and df["antigüedad_meses"].notna().any():
        cols_mostrar.append("antigüedad_meses")
 
    df_tabla = df[[c for c in cols_mostrar if c in df.columns]].copy()
    for col in ["dominio_intralaboral_puntaje", "dominio_extralaboral_puntaje", "puntaje_total_individual"]:
        if col in df_tabla.columns:
            df_tabla[col] = df_tabla[col].round(1)
 
    tabla_data = df_tabla.to_dict("records")
 
    estilo_cond = [
        {"if": {"filter_query": f'{{nivel_riesgo_global}} = "{nivel}"', "column_id": "nivel_riesgo_global"},
         "backgroundColor": COLOR_FONDO_TABLA[nivel], "color": "#2C3E50", "fontWeight": "600"}
        for nivel in ORDEN_NIVELES
    ]
    estilo_cond += [
        {"if": {"filter_query": '{nivel_riesgo_global} = "Alto"'},   "backgroundColor": "#FEF5F4"},
        {"if": {"filter_query": '{nivel_riesgo_global} = "Muy alto"'}, "backgroundColor": "#FDEDEC"},
    ]
 
    return (val_total, val_alto, val_medio, val_bajo, alerta,
            fig_barras, fig_hist, fig_radar, tabla_data, estilo_cond)
 
 
# ─────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Dashboard de Riesgo Psicosocial")
    print("  Abre tu navegador en: http://127.0.0.1:8050")
    print("="*60 + "\n")
    app.run(debug=False, host="127.0.0.1", port=8050)