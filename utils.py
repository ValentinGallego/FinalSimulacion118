import yaml
import numpy as np
import pandas as pd

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg

def generar_exponencial(media, rand):
    exp = -media * np.log(1 - rand)
    return exp

def generar_uniforme(minimo, maximo, rand):
    uni = minimo + (maximo - minimo) * rand
    return uni

def jobs_to_wide_columns(df: pd.DataFrame, jobs_col="trabajos") -> pd.DataFrame:
    """
    Convierte df[jobs_col] (lista de dicts por fila) en columnas:
    t001_id, t001_estado, ..., tXYZ_fin_correccion
    """
    if jobs_col not in df.columns:
        return df

    jobs_series = df[jobs_col].apply(lambda x: x if isinstance(x, list) else [])
    max_jobs = jobs_series.apply(len).max()

    # Si no hay trabajos, devolvemos sin esa col
    if max_jobs == 0:
        return df.drop(columns=[jobs_col])

    base_keys = ["estado", "llegada", "prioridad", "duracion_trabajo", "fin_correccion"]

    rows_wide = []
    for jobs in jobs_series:
        row = {}
        for i in range(max_jobs):
            prefix = f"t{i+1:03d}_"
            if i < len(jobs) and isinstance(jobs[i], dict):
                for k in base_keys:
                    row[prefix + k] = jobs[i].get(k, None)
            else:
                for k in base_keys:
                    row[prefix + k] = None
        rows_wide.append(row)

    wide_df = pd.DataFrame(rows_wide, index=df.index)
    out = pd.concat([df.drop(columns=[jobs_col]), wide_df], axis=1)
    return out