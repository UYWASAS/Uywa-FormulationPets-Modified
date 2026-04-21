def fmt2(x):
    """Formatea números como string con dos decimales."""
    try:
        f = float(x)
        return f"{f:,.2f}"
    except Exception:
        return x


def fmt2_df(df):
    """Aplica el formato fmt2 a todas las columnas de un DataFrame."""
    df_fmt = df.copy()
    for c in df_fmt.columns:
        df_fmt[c] = df_fmt[c].apply(fmt2)
    return df_fmt
