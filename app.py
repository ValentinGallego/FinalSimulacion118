import streamlit as st
import pandas as pd
import re
import json
import hashlib

from simulation import run_simulation
from utils import load_config, jobs_to_wide_columns


EVENT_COLUMNS_RENAME = {
    "reloj": "Reloj (min)",
    "evento": "Evento",
    "rnd_llegada1": "RND llegada 1",
    "rnd_llegada2": "RND llegada 2",
    "rnd_duracion": "RND duración",
    "tiempo_llegada1": "Tiempo llegada 1",
    "tiempo_llegada2": "Tiempo llegada 2",
    "tiempo_llegada3": "Tiempo llegada 3",
    "llegada1": "Llegada 1",
    "llegada2": "Llegada 2",
    "llegada3": "Llegada 3",
    "fin_fase": "Fin fase",
    "fase": "Fase",
    "id_atendido": "ID atendiendo",
    "rnd_trabajo": "RND trabajo",
    "duracion_trabajo": "Duración trabajo",
    "rnd_correccion": "RND corrección",
    "correccion": "¿Corrección?",
    "id_suspendido": "ID suspendido",
    "restante": "Tiempo restante",
    "restante_fase": "Tiempo restante fase",
    "estado_mecanografa": "Estado mecanógrafa",
    "cola": "Cola",
    "cola_prioridad": "Cola prioridad",
    "ac_espera": "Espera acumulada",
    "cont_atendidos": "Trabajos atendidos",
    "ac_tiempo_sistema": "Tiempo en sistema acumulado",
    "cont_trabajos": "Trabajos completados",
    "ultimo_cambio_cola": "Último cambio cola",
    "suma_area_cola": "Área bajo la cola",
}

JOB_FIELD_RENAME = {
    "id": "ID",
    "estado": "Estado",
    "llegada": "Llegada",
    "prioridad": "Prioridad",
    "duracion_trabajo": "Duración",
    "fin_correccion": "Fin corrección",
}

# Funciones auxiliares
def rename_job_columns_pretty(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas t001_estado -> Trabajo 1 · Estado"""
    new_cols: dict[str, str] = {}

    for col in df.columns:
        m = re.match(r"t(\d{3})_(.+)", col)
        if m:
            idx = int(m.group(1))
            field = m.group(2)
            field_name = JOB_FIELD_RENAME.get(field, field)
            new_cols[col] = f"Trabajo {idx} · {field_name}"

    return df.rename(columns=new_cols)


def cfg_fingerprint(cfg: dict) -> str:
    s = json.dumps(cfg, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def validar_cfg(cfg: dict) -> list[str]:
    errors: list[str] = []
    ev = cfg.get("events", {}) or {}
    sim = cfg.get("simulation", {}) or {}

    def nonneg(name: str, value):
        if value is None:
            return
        try:
            if float(value) < 0:
                errors.append(f"'{name}' no puede ser negativo (actual: {value}).")
        except Exception:
            errors.append(f"'{name}' debe ser numérico (actual: {value}).")

    nonneg("events.media_llegada", ev.get("media_llegada"))
    nonneg("events.minimo_tiempo_servicio", ev.get("minimo_tiempo_servicio"))
    nonneg("events.maximo_tiempo_servicio", ev.get("maximo_tiempo_servicio"))
    nonneg("events.duracion_correccion", ev.get("duracion_correccion"))

    mn = ev.get("minimo_tiempo_servicio")
    mx = ev.get("maximo_tiempo_servicio")
    if mn is not None and mx is not None:
        try:
            if float(mn) > float(mx):
                errors.append(
                    f"'minimo_tiempo_servicio' ({mn}) no puede ser mayor que 'maximo_tiempo_servicio' ({mx})."
                )
        except Exception:
            pass

    p = ev.get("probabilidad_correccion")
    if p is not None:
        try:
            p = float(p)
            if not (0 <= p <= 1):
                errors.append(f"'probabilidad_correccion' debe estar entre 0 y 1 (actual: {p}).")
        except Exception:
            errors.append(f"'probabilidad_correccion' debe ser numérica (actual: {p}).")

    fin_trab = sim.get("fin_trabajos_completos")
    if fin_trab is not None:
        try:
            if int(fin_trab) <= 0:
                errors.append(f"'fin_trabajos_completos' debe ser > 0 (actual: {fin_trab}).")
        except Exception:
            errors.append(f"'fin_trabajos_completos' debe ser entero (actual: {fin_trab}).")

    decs = sim.get("decimales")
    if decs is not None:
        try:
            if int(decs) < 0:
                errors.append(f"'decimales' no puede ser negativo (actual: {decs}).")
        except Exception:
            errors.append(f"'decimales' debe ser entero (actual: {decs}).")

    return errors


st.set_page_config(page_title="Simulación de Mecanografía", layout="wide")
st.title("Simulación de Mecanografía")

CONFIG_PATH = "config.yaml"

# ---- Estado persistente ----
if "df" not in st.session_state:
    st.session_state.df = None
if "metricas" not in st.session_state:
    st.session_state.metricas = None
if "cfg_fp" not in st.session_state:
    st.session_state.cfg_fp = None
if "desde" not in st.session_state:
    st.session_state.desde = 0
if "hasta" not in st.session_state:
    st.session_state.hasta = 200

# ---- Recargar config (manual) ----
topA, topB = st.columns([1, 6])
with topA:
    if st.button("Recargar config"):
        st.cache_data.clear()
        st.rerun()

cfg = load_config(CONFIG_PATH)
current_fp = cfg_fingerprint(cfg)

errores_cfg = validar_cfg(cfg)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Configuración actual (en minutos)")
    st.json(cfg)

with col2:
    st.subheader("Ejecutar")

    b1, b2 = st.columns(2)
    with b1:
        run = st.button("Simular", type="primary", disabled=bool(errores_cfg))
    with b2:
        if st.button("Limpiar resultados 🧹"):
            st.session_state.df = None
            st.session_state.metricas = None
            st.session_state.cfg_fp = None
            st.session_state.desde = 0
            st.session_state.hasta = 200
            st.rerun()

# Mostrar errores de config (si hay)
if errores_cfg:
    st.error("Configuración inválida. Corregí lo siguiente:")
    for e in errores_cfg:
        st.write(f"- {e}")

# ---- Ejecutar simulación SOLO cuando se presiona ----
if run:
    with st.spinner("Simulando..."):
        df, metricas = run_simulation(cfg)

    st.session_state.df = df
    st.session_state.metricas = metricas
    st.session_state.cfg_fp = current_fp
    st.session_state.desde = 0
    st.session_state.hasta = min(200, len(df))

    st.rerun()

df = st.session_state.df
metricas = st.session_state.metricas

if df is None:
    st.info("Presioná **Simular** para generar resultados.")
    st.stop()

if st.session_state.cfg_fp != current_fp:
    st.warning(
        "⚠️ El archivo de configuración cambió. Estos resultados son del config anterior. "
        "Volvé a **Simular** o tocá **Limpiar resultados**."
    )

decs = int(cfg.get("simulation", {}).get("decimales", 2))

df_eventos = df.drop(columns=["trabajos"], errors="ignore").copy()
df_eventos = df_eventos.rename(columns=EVENT_COLUMNS_RENAME)

st.subheader("Eventos (vista general)")
st.success(f"Listo. Filas (eventos): {len(df_eventos):,}")
st.dataframe(df_eventos.round(decs), width="stretch")

st.subheader("Vista detallada (rango de filas)")

total = len(df)

c_from, c_to, c_info = st.columns([1, 1, 2])

with c_from:
    desde = st.number_input(
        "Fila desde (incl.)",
        min_value=0,
        max_value=max(total - 1, 0),
        value=int(st.session_state.desde),
        step=1,
        key="desde",
    )

with c_to:
    hasta = st.number_input(
        "Fila hasta (excl.)",
        min_value=1 if total > 0 else 0,
        max_value=total,
        value=int(st.session_state.hasta),
        step=1,
        key="hasta",
    )

if total == 0:
    st.info("No hay filas para mostrar.")
elif hasta <= desde:
    st.error("⚠️ 'Fila hasta' debe ser mayor que 'Fila desde'.")
elif (hasta - desde) > 200:
    st.error("⚠️ El rango no puede superar 200 filas.")
else:
    with c_info:
        st.caption(
            f"Mostrando filas [{desde}, {hasta}) → {hasta - desde} filas (DF completo aplanado)"
        )

    df_detalle = df.iloc[int(desde):int(hasta)].copy()

    df_detalle = jobs_to_wide_columns(df_detalle)
    df_detalle = df_detalle.rename(columns=EVENT_COLUMNS_RENAME)
    df_detalle = rename_job_columns_pretty(df_detalle)

    st.dataframe(df_detalle.round(decs), width="stretch")

st.subheader("Métricas")
c1, c2, c3 = st.columns(3)
c1.metric("Tiempo de espera promedio", f"{metricas[0]:.2f} min", border=True)
c2.metric("Longitud de cola promedio", f"{metricas[1]:.2f}", border=True)
c3.metric("Tiempo promedio en sistema", f"{metricas[2]:.2f} min", border=True)
