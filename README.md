# Job Alert Bot

Este es un bot que busca empleos en varios portales, los filtra según tus preferencias y te los envía a un canal de Telegram.

## Características

- **Múltiples fuentes:** Obtiene empleos de Get on Board, Educación IT y JobSpy.
- **Filtros personalizables:** Filtra los empleos por nivel de experiencia (seniority), área, palabras clave de TI y frases de experiencia excluidas.
- **Notificaciones en Telegram:** Envía los nuevos empleos a un canal de Telegram.
- **Dos modos de ejecución:**
    - **Modo scraper:** Ejecuta la búsqueda de empleos una sola vez y termina.
    - **Modo bot:** Inicia un bot de Telegram que responde a comandos.
- **Comandos del bot:**
    - `/fetch`: Inicia el proceso de búsqueda de empleos.
    - `/delete`: Elimina empleos de la base de datos.

## Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/job-alert-bot.git
    cd job-alert-bot
    ```

2.  **Crea un entorno virtual e instala las dependencias:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

## Configuración

1.  **Crea un archivo `.env`** en la raíz del proyecto, basándote en el archivo `.env.example` (si existiera) o créalo desde cero.

2.  **Añade las siguientes variables de entorno** a tu archivo `.env`:
    ```
    TELEGRAM_TOKEN="TU_TOKEN_DE_TELEGRAM"
    ADMIN_USER_ID="TU_ID_DE_USUARIO_DE_TELEGRAM"
    TELEGRAM_CHAT_ID="ID_DEL_CANAL_DE_TELEGRAM"
    ```
    - `TELEGRAM_TOKEN`: El token de tu bot de Telegram, que puedes obtener de BotFather.
    - `ADMIN_USER_ID`: Tu ID de usuario de Telegram. El bot solo responderá a los comandos que tú envíes.
    - `TELEGRAM_CHAT_ID`: El ID del canal o chat de Telegram a donde se enviarán los empleos.

3.  **Personaliza los filtros** en el archivo `config.py` para que se ajusten a tus necesidades.

## Uso

### Modo Scraper

Para ejecutar el scraper una sola vez y que envíe los nuevos empleos a Telegram, usa el siguiente comando:

```bash
python main.py --scraper
```

Esto es útil para ejecutar el script periódicamente usando un cron job o una GitHub Action.

### Modo Bot

Para iniciar el bot de Telegram y que espere tus comandos, ejecuta:

```bash
python main.py
```

El bot se iniciará y podrás interactuar con él en Telegram.

## Dependencias

- `python-dotenv`
- `python-telegram-bot`
- `requests`
- `beautifulsoup4`
- `pandas`
- `python-jobspy`

## Estructura del Proyecto

```
/
├── .gitignore
├── config.py
├── json_handler.py
├── main.py
├── requirements.txt
├── utils.py
├── bot/
│   ├── bot.py
│   └── utils.py
├── data/
│   ├── jobs_2025_10.json
│   ├── latest_jobs.json
│   └── trends_history.json
└── sources/
    ├── educacionit_fetcher.py
    ├── getonboard_fetcher.py
    └── jobspy_fetcher.py
```
