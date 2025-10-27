# Job Alert Bot 🤖

Este es un bot automatizado que busca empleos en el sector de TI, los procesa a través de un sistema avanzado de filtrado y puntuación, y notifica los resultados más relevantes en un canal de Telegram.

El objetivo principal es filtrar el "ruido" de los portales de empleo y presentar únicamente las ofertas que se ajustan a un perfil de búsqueda específico, el cual es fácilmente configurable (por defecto, está ajustado para roles de nivel inicial).

## ✨ Características Principales

-   **Scraping Multi-fuente**: Obtiene empleos de **Get on Board**, **Educación IT** y **JobSpy** (que a su vez busca en LinkedIn, Indeed, etc.).
-   **Base de Datos en Firestore**: Utiliza Firebase Firestore para almacenar los empleos y evitar el envío de duplicados.
-   **Filtrado Avanzado**:
    -   Descarta automáticamente empleos de áreas no relacionadas con TI (RRHH, Marketing, Finanzas, etc.).
    -   Excluye roles que no se ajustan al perfil de seniority deseado (ej: Senior, Lead, Manager).
-   **Sistema de Scoring (Puntuación)**:
    -   Cada empleo pasa por un algoritmo que le asigna una puntuación de 0 a 100 basada en su relevancia.
    -   El sistema analiza el título y la descripción en busca de palabras clave de tecnologías, roles y seniority.
    -   Aplica bonificaciones y penalizaciones según reglas configurables.
-   **Generación de Tags**: Extrae y asigna las palabras clave más importantes a cada empleo (ej: `react`, `python`, `aws`, `backend`) para una fácil identificación.
-   **Notificaciones en Telegram**: Envía los empleos que superan una puntuación mínima a un canal de Telegram.
-   **Ejecución Automatizada**: Diseñado para ser ejecutado automáticamente a través de **GitHub Actions** en un horario programado.

## ⚙️ Cómo Funciona (Flujo de Trabajo)

1.  **Scrape**: El bot se ejecuta y extrae las últimas ofertas de todas las fuentes.
2.  **Deduplicación**: Comprueba en Firestore si los empleos ya han sido procesados anteriormente.
3.  **Pre-filtrado**: Aplica una primera capa de filtros para descartar empleos por área y seniority no deseados.
4.  **Scoring y Filtrado Final**: Asigna una puntuación a los empleos restantes. Solo los que superan el `MIN_SCORE` son aceptados.
5.  **Notificación**: Los empleos aceptados se envían al canal de Telegram.
6.  **Almacenamiento**: Todos los empleos procesados (aceptados y rechazados) se guardan en Firestore para referencia futura y para el proceso de deduplicación.

## 🔧 Configuración

El proyecto se configura principalmente a través de dos archivos y variables de entorno.

1.  **`config.py`**:
    -   `UPLOAD_TO_FIREBASE`: Activa o desactiva la conexión con Firestore.
    -   `DAYS_OLD_THRESHOLD`: Límite de días de antigüedad para procesar un empleo.
    -   `JOBSPY_SEARCH_TERMS`: Palabras clave para la búsqueda en JobSpy.
    -   Y otras configuraciones específicas de cada fetcher.

2.  **`filters_scoring_config.py`**:
    -   Aquí reside el "cerebro" del bot. Es donde se define el perfil de búsqueda.
    -   `MIN_SCORE`: La puntuación mínima que un empleo debe tener para ser aceptado.
    -   Listas de palabras clave para el scoring: `TAGS_KEYWORDS`, `STRONG_ROLE_SIGNALS`, `EXCLUDED_AREA_TERMS_TITLE`, etc.

3.  **Variables de Entorno (Secrets)**:
    -   `BOT_TOKEN`: El token del bot de Telegram.
    -   `TELEGRAM_CHANNEL_ID`: El ID del canal de Telegram para las notificaciones.
    -   `FIREBASE_CREDENTIALS_BASE64`: Las credenciales de servicio de Google Cloud/Firebase, codificadas en Base64.

## 🚀 Uso

El bot está diseñado para funcionar de forma automatizada. El archivo `.github/workflows/scraper.yml` contiene una configuración de GitHub Actions para ejecutar el script varias veces al día.

Para ejecutarlo manualmente:

1.  **Clona el repositorio.**
2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configura tus credenciales:**
    -   Asegúrate de que el archivo de credenciales de Google Cloud (`.json`) esté disponible.
    -   Exporta las variables de entorno necesarias.
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/tus/credenciales.json"
    export BOT_TOKEN="TU_TOKEN"
    export TELEGRAM_CHANNEL_ID="ID_DEL_CANAL"
    ```
4.  **Ejecuta el script:**
    ```bash
    python main.py
    ```

## 🛠️ Pila Tecnológica

-   **Lenguaje**: Python 3.11
-   **Scraping**: `requests`, `beautifulsoup4`, `python-jobspy`
-   **Base de Datos**: Google Firestore
-   **Notificaciones**: `python-telegram-bot`
-   **Orquestación**: GitHub Actions
-   **Otros**: `pandas`, `dateparser`