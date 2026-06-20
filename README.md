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

El repositorio consta de los siguientes archivos clave:

* `app.py`: Punto de entrada de la aplicación en Streamlit. Gestiona la interfaz gráfica, los filtros temporales, la carga de datos del Cubo OLAP y el renderizado del mapa dinámico.
* `clases.py`: Definición de la arquitectura de datos (POO) que modela el Cubo OLAP (Dimensiones, Hechos y abstracciones por Alcaldía).
* `predicciones_regresion_logistica_lluvia.csv`: Dataset con 17,520 registros que contienen las fechas, alcaldías, probabilidades calculadas por el modelo, predicciones, valores reales y categorías de riesgo.
* `Dockerfile`: Configuración de la imagen Docker optimizada basada en `python:3.11-slim`.
* `requirements.txt`: Dependencias del sistema (Streamlit, Pandas, Folium, Streamlit-Folium, PyShp).

---

## Instalación y Uso Local

### Requisitos Previos
* Python 3.11 o superior instalado.
* Asegurar que los polígonos/shapefiles oficiales de las alcaldías se encuentren en la ruta `alcaldias/poligonos_alcaldias_cdmx`.

### Paso 1: Instalar Dependencias
```bash
pip install -r requirements.txt
