import os
import glob
import yt_dlp
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, 'ff')

def setup():
    pass

def getLinks(text):
    links = list(filter(lambda line: line != "", text))
    return links

def download(links):
    failed = []
    user_music_path = os.path.join(os.path.expanduser('~'), 'Music')

    # --- HOOK DE LIMPIEZA Y NOTIFICACIÓN ---
    def progress_hook(d):
        if d['status'] == 'finished':
            print(f"\n[Procesando] Conversión terminada: {d['filename']}")
            
            # TRUCO DE LIMPIEZA:
            # Una vez que yt-dlp termina, buscamos si dejó la imagen tirada y la borramos.
            # El nombre base del archivo (sin extensión .mp3)
            base_filename = os.path.splitext(d['filename'])[0]
            
            # Buscamos cualquier archivo que empiece igual pero sea imagen (.jpg, .webp, .png)
            potential_images = glob.glob(f"{base_filename}.*")
            
            for img in potential_images:
                if img.lower().endswith(('.jpg', '.jpeg', '.webp', '.png')):
                    try:
                        os.remove(img)
                        print(f"[Limpieza] Carátula residual eliminada: {os.path.basename(img)}")
                    except Exception as e:
                        print(f"[Warning] No se pudo borrar la imagen: {e}")

    # --- FILTRO INTELIGENTE (Duration) ---
    def smart_filter(info, *, incomplete):
        duration = info.get('duration')
        if duration is None: return None 
        if duration < 60: return 'Video muy corto (posible intro/short)'
        return None

    ydl_opts = {
        'ignoreerrors': True,
        'sleep_interval_requests': 2,
        'sleep_interval': 3,
        'match_filter': smart_filter, 
        'format': 'bestaudio/best',
        
        'extractor_args': {'youtube': ['client=android,ios']},
        
        # --- 1. LIMPIEZA DE ARTISTA (REGEX) ---
        # Creamos una variable 'clean_artist' que toma el Artista y corta todo
        # lo que esté después de una coma, un feat, un & o un ;
        'parse_metadata': [
            {
                'regex': r'(?P<clean_artist>[^,;&]+)',
                'from': 'artist'
            }
        ],

        # --- 2. JERARQUÍA DE CARPETAS ---
        # La lógica es:
        # A. ¿Existe 'album_artist'? (Ej. Album de Gorillaz feat Bad Bunny -> Folder: Gorillaz)
        # B. ¿No existe? Usa 'clean_artist' (Ej. Sencillo Imagine Dragons, JID -> Folder: Imagine Dragons)
        # C. ¿Falló todo? Usa 'uploader' (Nombre del canal)
        
        'outtmpl': f'{user_music_path}/%(album_artist|clean_artist|uploader)s/%(album,playlist_title|Singles)s/%(title)s.%(ext)s',
        
        'nooverwrites': True,
        'ffmpeg_location': FFMPEG_DIR,

        'writethumbnail': True, # La descargamos para incrustarla...
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'EmbedThumbnail', # ...aquí se incrusta en el MP3
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ],
        'postprocessor_args': {
            'ffmpeg': ['-id3v2_version', '3', '-metadata', 'comment=']
        },
        'quiet': False,
        
        # Activamos el hook de limpieza
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(links)
    except Exception as e:
        print(f"Error crítico: {str(e)}")
        failed.append(str(e))

    return failed