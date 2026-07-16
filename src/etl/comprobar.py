from features import construir_fila_features
import joblib
import pandas as pd

fila, imputados = construir_fila_features(9841)

modelo = joblib.load("models/trafico.pkl")

X = fila.to_pandas()

# Debe coincidir EXACTAMENTE con las categorías vistas en entrenamiento
X["tipo_elem"] = pd.Categorical(X["tipo_elem"], categories=["URB", "M30", "C30"])

prediccion = modelo.predict(X)
print("\nPredicción:", prediccion[0])

