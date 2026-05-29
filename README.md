# Actividad: DASHboards y Plotly
# ⚡ Pokémon Complete Pokédex — Dashboards y Plotly

## Integrantes

| Nombre | Matrícula |
|---|---|
| Jorge Emiliano Gómez Hernández | A01368016 |
| Jaime Trujillo Ruiz | A01276139 |

---

## Dataset

**Pokémon Complete Pokédex Dataset (2026)**  
🔗 [https://www.kaggle.com/datasets/patelris/pokemon-dataset-with-stats-and-types](https://www.kaggle.com/datasets/patelris/pokemon-dataset-with-stats-and-types)

Dataset con información completa de los 1,350 Pokémon registrados hasta 2026, incluyendo stats de combate, tipos, generación, habitat, tasa de captura y flags especiales como `is_legendary` e `is_mythical`.

---

## Contenido del repositorio

```
├── pokemon_complete.csv          # Dataset descargado de Kaggle
├── Actividad_Dashboards.ipynb    # Notebook con los 10 gráficos
├── dash_pokemon.py               # Dashboard con Dash y Plotly
└── README.md
```

---

## Cómo correr el notebook

1. Instala las dependencias:
```bash
pip install plotly pandas numpy
```

2. Abre el notebook en Jupyter:
```bash
jupyter notebook Actividad_Dashboards.ipynb
```

3. Asegúrate de tener `pokemon_complete.csv` en la misma carpeta.

---

## Correr el dashboard

1. Crea un entorno virtual e instala dependencias:
```bash
python3 -m venv venv
source venv/bin/activate
pip install dash pandas plotly numpy
```

2. Corre el dashboard:
```bash
python app.py
```

3. Abre en tu navegador: [http://127.0.0.1:8050]
