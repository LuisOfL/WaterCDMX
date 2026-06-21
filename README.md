# PLUVIA: Plataforma para la Predicción de Lluvia Intensa

**PLUVIA** es una plataforma web interactiva desarrollada con **Streamlit** diseñada para visualizar, analizar y predecir eventos de lluvias intensas y riesgos hídricos asociados en las 16 alcaldías de la Ciudad de México (CDMX). El sistema integra datos climáticos históricos de la NASA con reportes ciudadanos del 911 (periodo 2019-2021) mediante un modelo predictivo de **Regresión Logística**.

Este proyecto fue desarrollado bajo la guía del profesor **López Gómez Alejandro** por los integrantes:
* **Melendez Chavero Luis Angel**
* **Moysen Arcos Angel Eduardo**
* **Grupo:** 4AM1

---

##  Características Principales

* **Visualización Geográfica Interactiva:** Incorpora un mapa coroplético oficial de la CDMX mediante `folium`, que colorea las alcaldías según su nivel de riesgo y probabilidad de lluvia intensa en tiempo real.
* **Modelo Predictivo (Regresión Logística):** Clasifica directamente los niveles de riesgo (**BAJO, MEDIO, ALTO**) calculando la probabilidad basada en variables meteorológicas e históricos de incidentes hídricos (inundaciones, afectaciones viales).
* **Arquitectura OLAP Estructurada:** Implementa un diseño de cubo OLAP basado en un Modelo de Estrellas con dimensiones explícitas (`DimTiempo`, `DimAlcaldia`, `DimMetricasLluvia`) y una tabla de hechos (`HechoClimatico`).
* **Contenedorización con Docker:** Listo para ser desplegado en cualquier entorno de manera aislada, rápida y reproducible.

---

##  Estructura del Proyecto

El repositorio consta de dos carpetas clave:

app -> Es la aplicacion

* `app.py`: Punto de entrada de la aplicación en Streamlit. Gestiona la interfaz gráfica, los filtros temporales, la carga de datos del Cubo OLAP y el renderizado del mapa dinámico.
* `clases.py`: Definición de la arquitectura de datos (POO) que modela el Cubo OLAP (Dimensiones, Hechos y abstracciones por Alcaldía).
* `predicciones_regresion_logistica_lluvia.csv`: Dataset con 17,520 registros que contienen las fechas, alcaldías, probabilidades calculadas por el modelo, predicciones, valores reales y categorías de riesgo.
* `Dockerfile`: Configuración de la imagen Docker optimizada basada en `python:3.11-slim`.
* `requirements.txt`: Dependencias del sistema (Streamlit, Pandas, Folium, Streamlit-Folium, PyShp).

pipeline -> Es el flujo de datos desde la extraccion hasta la carga (Los dataset se encuentran en un datalake en AWS debido a su peso, pero se pueden leer perfectamente en los codigos)

* **`pipeline/api.py`**
    * **Funcionamiento:** Script encargado de la generación de la malla geográfica de la CDMX (resolución de ~1km) mediante `geopandas` utilizando un filtro espacial (*spatial join*) para asegurar que los puntos pertenezcan al territorio oficial. Automatiza las solicitudes asíncronas por protocolo HTTP a la API *POWER* de la **NASA** para descargar el histórico diario crudo de parámetros climáticos, generando el archivo inicial `clima_nasa_crudo.csv`.
* **`pipeline/etl_nasa.py`**
    * **Funcionamiento:** Proceso ETL dedicado a la fuente meteorológica. Mapea y renombra los códigos técnicos de la NASA a nombres normalizados de variables en el negocio (`PRECTOTCORR` $\rightarrow$ `precip`, etc.). Su función principal es aplicar transformaciones de texto utilizando codificación **Unicode (NFKD)** para limpiar los nombres de las alcaldías (removiendo acentos y caracteres especiales) con el fin de estandarizar la llave de unión geográfica.
* **`pipeline/etl_oficial_911.py`**
    * **Funcionamiento:** Pipeline ETL enfocado en los reportes ciudadanos del **Portal Axolote**. Filtra la base de llamadas masiva del 911 para aislar únicamente incidentes de afectación hídrica urbana con prioridad en la clasificación **"Inundación"**. Ejecuta la misma estandarización Unicode en las alcaldías y agrupa de manera determinista los registros bajo una granularidad de **Fecha + Alcaldía** para contabilizar el volumen diario de siniestros.
* **`pipeline/integrar_datasets.py`**
    * **Funcionamiento:** Orquestador de fusión de datos. Realiza un *Merge* interno e indexado cruzando espacio y tiempo utilizando como llaves compuestas la fecha y la alcaldía limpia. Controla la integridad referencial imputando con un valor de cero (`fillna(0)`) los registros donde la atmósfera reportó actividad pero no existieron llamadas de emergencia en el 911, garantizando la creación de la variable objetivo binaria.
* **`pipeline/feature_engineering.py`**
    * **Funcionamiento:** Enriquece la matriz de características mediante la construcción de variables con perspectiva temporal. Calcula **variables de rezago (lags)** y ventanas móviles acumuladas de precipitación (1, 3, 7, 14 y 30 días) para dotar al modelo de memoria sobre la saturación previa del suelo. Implementa cruces no lineales de variables atmosféricas (humedad específica y punto de rocío) y aplica una **transformación logarítmica ($log(x + 1)$)** a las columnas de lluvia para estabilizar la varianza ante tormentas atípicas.
* **`pipeline/analisis_integrado.py`**
    * **Funcionamiento:** Script de analítica exploratoria intermedio. Evalúa de manera estadística el balance general de las clases hídricas del dataset unificado y calcula la tasa de incidencia porcentual de inundaciones distribuidas específicamente por cada alcaldía, validando las bases del comportamiento del fenómeno antes del entrenamiento.
* **`pipeline/modelo_regresion_logistica.py`**
    * **Funcionamiento:** El núcleo predictivo del sistema. Divide cronológicamente los datos para evitar fuga de información (*data leakage*). Emplea un pipeline de `scikit-learn` que procesa variables categóricas con `OneHotEncoder` y numéricas con `StandardScaler`. Para solucionar el desbalance extremo de los días con inundación, implementa la técnica **SMOTE** (muestreo sintético). Entrena una **Regresión Logística**, calibra un umbral de decisión personalizado para optimizar el balance *Precision-Recall*, y evalúa el rendimiento mediante curvas ROC y matrices de confusión, exportando finalmente el archivo CSV que consume la interfaz.



---

## Instalación y Uso Local

### Requisitos Previos
* Python 3.11 o superior instalado.
* Asegurar que los polígonos/shapefiles oficiales de las alcaldías se encuentren en la ruta `alcaldias/poligonos_alcaldias_cdmx`.

### Paso 1: Instalar Dependencias
```bash
pip install -r requirements.txt
