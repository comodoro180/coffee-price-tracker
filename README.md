# Coffee Price Tracker - Cali, Colombia ☕

Aplicación web para comparar precios de café en tiempo real en los principales supermercados de Colombia.

## 🚀 Características

- **10 Almacenes**: Olímpica, Éxito, Carulla, Jumbo, Metro, Makro, D1, Alkosto, Ara, PriceSmart
- **Búsqueda en Tiempo Real**: Consulta precios actualizados de cualquier marca de café
- **Comparación Inteligente**: Identifica automáticamente el mejor precio
- **Progreso Visual**: Indicadores de estado para cada almacén durante la búsqueda
- **Enlaces Directos**: Acceso directo a cada producto en la tienda online

## 🛠️ Tecnologías

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python (Starlette, Uvicorn)
- **Scraping**: Requests (VTEX APIs) + Playwright (sitios dinámicos)

## 📦 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/coffee-price-tracker.git
cd coffee-price-tracker

# Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# Iniciar servidor
python server.py

# Abrir en navegador
# http://127.0.0.1:8000
```

## 🌐 Despliegue en Render

Este proyecto está configurado para desplegarse automáticamente en Render.com:

1. Haz fork de este repositorio
2. Conecta tu cuenta de Render con GitHub
3. Crea un nuevo Web Service desde tu repositorio
4. Render detectará automáticamente la configuración en `render.yaml`
5. ¡Listo! Tu app estará pública en minutos

## 📝 Uso

1. Escribe el nombre de la marca de café que buscas
2. Presiona "Sincronizar"
3. Espera 30-45 segundos mientras se consultan los 10 almacenes
4. Compara precios y haz clic en "Ver en tienda" para comprar

## ⚠️ Limitaciones

- **Ara**: No tiene catálogo en línea
- **PriceSmart**: Requiere membresía para ver precios
- **Tiempo de búsqueda**: 30-45 segundos (scraping en tiempo real)

## 📄 Licencia

MIT License - Siéntete libre de usar y modificar este proyecto

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor abre un issue o pull request.

---

Desarrollado con ❤️ para encontrar el mejor precio de café en Colombia
