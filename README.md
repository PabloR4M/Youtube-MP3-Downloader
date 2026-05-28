# Youtube->MP3 Downloader

Una aplicación de escritorio escrita en Python diseñada para buscar, previsualizar y descargar música desde YouTube Music directamente en formato MP3. La herramienta permite descargar pistas individuales, álbumes completos o playlists, encargándose de incrustar automáticamente las carátulas y los metadatos oficiales (artista, álbum, año) para que los archivos estén listos para ser leídos por reproductores de automóviles y bibliotecas de música tradicionales.

## Cómo Ejecutar

**Opción 1: Acceso Directo (Recomendado)**
Para iniciar la aplicación de forma automática, simplemente ejecuta el acceso directo "YouTube2MP3 Pro" (o el archivo `iniciar-app.bat`). Este script comprobará e instalará de forma silenciosa cualquier actualización necesaria en las dependencias antes de lanzar la interfaz gráfica, asegurando que la herramienta siempre funcione con la versión más reciente.

**Opción 2: Desde la Terminal**
Si prefieres un entorno manual o necesitas usar la interfaz de línea de comandos, abre tu terminal, navega hasta la carpeta `src` del proyecto y ejecuta el archivo principal:

    python main.py

*Nota para usuarios avanzados:* Puedes ejecutar la aplicación sin interfaz gráfica usando `python main.py --cli` para el modo consola, o `python main.py --file links.txt` para descargar masivamente leyendo un documento de texto.

## Cómo usar la aplicación

La herramienta cuenta con dos métodos de descarga principales que se pueden alternar mediante pestañas:

**Modo Automático (Buscador Integrado)**
1. Configura la ruta de descarga en la parte superior seleccionando la carpeta destino en tu computadora.
2. Selecciona el filtro de búsqueda adecuado según lo que desees encontrar (Canciones, Álbumes, Artistas o Playlists).
3. Ingresa el nombre de la pista en la barra y presiona "Buscar".
4. (Opcional) Haz clic sobre la imagen de cualquier resultado para reproducir una previsualización de 15 segundos. El reproductor detectará el mapa de calor de YouTube y saltará automáticamente a la parte más reproducida de la canción.
5. Presiona el botón "Agregar" junto a los resultados deseados para enviarlos a la cola de descargas.
6. Presiona el botón "Descargar Cola Completa" en la parte inferior para iniciar el proceso.

**Modo Manual (Cola de Links)**
1. Abre tu navegador, ingresa a YouTube o YouTube Music y busca tus canciones, álbumes o playlists.
2. Copia los enlaces y pégalos en la caja de texto de la pestaña "Manual / Cola de Links" (asegurándote de colocar un enlace por línea).
3. Presiona el botón "Descargar Cola Completa".

*Importante: Toda la música procesada se descargará y organizará en carpetas estructuradas dentro de la ruta seleccionada en el paso 1.*

## Cómo funciona la aplicación (Backend)

El motor de descarga está construido utilizando la librería `yt-dlp` para la extracción de datos y conectividad, delegando el procesamiento multimedia a `FFmpeg`. Por cada enlace procesado, el sistema ejecuta la siguiente lógica secuencial:

1. **Descarga de componentes:** El programa se conecta simulando las credenciales de un dispositivo móvil para eludir bloqueos. Descarga el flujo de audio en bruto (su máxima calidad disponible) y guarda la imagen de la carátula como un archivo temporal separado.
2. **Extracción de metadatos:** De manera invisible, el sistema recupera la información estructural de la pista (Título, Artista, Álbum) y la almacena en memoria mediante un diccionario JSON.
3. **Procesamiento de audio y video:** Una vez descargados los elementos, se ejecuta una cadena de post-procesadores de `FFmpeg`:
   - Se convierte el flujo de audio crudo al formato MP3 universal (192kbps).
   - Se convierte la imagen temporal de la carátula a formato JPG estandarizado.
4. **Fusión e Incrustación:** `FFmpeg` inyecta los datos de texto en el archivo de audio forzando la versión de metadatos ID3v2.3 (para asegurar compatibilidad total con estéreos de modelos antiguos). Finalmente, incrusta la imagen JPG dentro del MP3.
5. **Limpieza del sistema:** Un sistema de interrupción ("hook") monitorea el proceso. Una vez que detecta que `FFmpeg` ha terminado de fusionar y crear el archivo MP3 definitivo con éxito, ordena al sistema operativo eliminar las imágenes temporales residuales, dejando únicamente el archivo musical listo para reproducirse.