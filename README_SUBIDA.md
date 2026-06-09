# App Ahorro Mikel - guía rápida

## 1) Probar en tu ordenador
1. Instala Python 3.11 o superior.
2. Descomprime esta carpeta.
3. Abre una terminal dentro de la carpeta.
4. Ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

5. Se abrirá la app en el navegador. El Excel base debe llamarse `Ahorro.xlsx` y estar en esta misma carpeta.

## 2) Subir a GitHub
1. Crea un repositorio nuevo en GitHub, por ejemplo `app-ahorro-mikel`.
2. Sube estos archivos:
   - `app.py`
   - `requirements.txt`
   - `Ahorro.xlsx`
   - `.streamlit/config.toml`
3. Haz commit.

## 3) Publicar en Streamlit Community Cloud
1. Entra en Streamlit Community Cloud.
2. Pulsa **New app**.
3. Elige tu repositorio.
4. En **Main file path** escribe: `app.py`.
5. Pulsa **Deploy**.

## Importante sobre guardar datos
En local, la app guarda cambios en `Ahorro.xlsx`.
En Streamlit Cloud, los cambios pueden no ser persistentes si la app se reinicia. Por eso la app incluye botón para descargar siempre el Excel actualizado.

Para una versión con guardado permanente online, lo ideal es subirla a Render/Railway con disco persistente, o conectar Google Sheets/Drive.
