import os
import glob
import subprocess
import threading
import yt_dlp
from pathlib import Path
from ytmusicapi import YTMusic 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, 'ff')

def setup():
    pass

# VARIABLES GLOBALES
current_preview_process = None
current_preview_id = 0


# BUSQUEDA DE CANCIONES PARA INTERFAZ GUI
def search_music(query, search_filter=None, max_results=12):
    """Busca música con filtros, respetando los resultados libres de la búsqueda General."""
    results = []
    try:
        ytmusic = YTMusic()
        search_results = ytmusic.search(query, filter=search_filter, limit=max_results)
        
        for item in search_results:
            title = item.get('title', item.get('artist', 'Desconocido'))
            
            thumb_list = item.get('thumbnails', [])
            thumbnail = thumb_list[0]['url'] if thumb_list else ""
            
            artists_list = [a['name'] for a in item.get('artists', []) if 'name' in a]
            artist_name = ", ".join(artists_list) if artists_list else "Desconocido"
            
            # Si no hay un resultType definido, se asume que es una canción
            raw_type = item.get('resultType', 'song')
            url = ""

            # Diferentes links dependiendo si es albu, playlist o cancion individual
            if raw_type in ['song', 'video'] and 'videoId' in item:
                url = f"https://music.youtube.com/watch?v={item['videoId']}"
            elif raw_type == 'album' and 'browseId' in item:
                url = f"https://music.youtube.com/browse/{item['browseId']}"
            elif raw_type == 'playlist' and 'browseId' in item:
                url = f"https://music.youtube.com/playlist?list={item['browseId']}"
            elif raw_type == 'artist' and 'browseId' in item:
                url = f"https://music.youtube.com/channel/{item['browseId']}"
            else:
                # Fallback por si la API cambia de nombre las variables
                if 'videoId' in item:
                    url = f"https://music.youtube.com/watch?v={item['videoId']}"
                elif 'playlistId' in item: 
                    url = f"https://music.youtube.com/playlist?list={item['playlistId']}"
                else:
                    continue # Salta resultado si no se puede abrir

            # Datos para tabla gui
            tipo_map = {'song': 'Canción', 'video': 'Video', 'album': 'Álbum', 'artist': 'Artista', 'playlist': 'Playlist'}
            tipo_limpio = tipo_map.get(raw_type, raw_type.capitalize())

            results.append({
                'title': title,
                'artist': artist_name,
                'type': tipo_limpio,
                'url': url,
                'thumbnail': thumbnail
            })
    except Exception as e:
        print(f"Error con la API de búsqueda: {e}")
        
    return results


# PREVIEW DE LA CANCION
def play_audio_preview(url):
    """Reproduce 15 segundos de audio descartando el inicio y deteniendo audios previos."""
    global current_preview_process, current_preview_id
    
    # Se detienen preview anteriores aun en reproduccion
    if current_preview_process and current_preview_process.poll() is None:
        try:
            current_preview_process.terminate()
        except Exception:
            pass

    # registro de cada click
    current_preview_id += 1
    my_preview_id = current_preview_id

    def task():
        global current_preview_process
        try:
            print("[Preview] Analizando mapa de calor y extrayendo audio...")
            
            ydl_opts = {'quiet': True, 'format': 'bestaudio'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info.get('url')
                heatmap = info.get('heatmap')
            
            # Se interrumpe la preview si se vuelve a dar click o se reproduce otra preview
            if my_preview_id != current_preview_id:
                return
            
            if stream_url:
                start_time = 0
                if heatmap:
                    # Se descartan los primeros 15 segundos (el falso pico de reproducciones del inicio)
                    filtered_heatmap = [x for x in heatmap if x.get('start_time', 0.0) > 15.0]
                    
                    if filtered_heatmap:
                        # Parte mas reproducida de la cancion
                        best_part = max(filtered_heatmap, key=lambda x: x.get('value', 0.0))
                        start_time = best_part.get('start_time', 0.0)
                        
                        mins, secs = divmod(int(start_time), 60)
                        print(f" Parte más reproducida encontrada en: {mins}:{secs:02d}")
                    else:
                        print("ℹ Canción muy corta o sin datos. Reproduciendo desde el inicio.")

                print("▶ Reproduciendo (15s)...")
                
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                ffplay_exe = os.path.join(FFMPEG_DIR, 'ffplay.exe')
                if not os.path.exists(ffplay_exe): 
                    ffplay_exe = 'ffplay' 
                
                cmd2 = [
                    ffplay_exe, 
                    '-nodisp', 
                    '-autoexit', 
                    '-ss', str(start_time), 
                    '-t', '15', 
                    stream_url
                ]
                
                # preview interrumpible
                current_preview_process = subprocess.Popen(cmd2, startupinfo=startupinfo)
                
                # preview de 15 segundos
                current_preview_process.wait()
                
                # La preview se detiene automaticamente tras los 15 segundos
                if my_preview_id == current_preview_id:
                    print("⏹ Preview finalizado.")
                    
        except FileNotFoundError:
            print(f"[Preview] Error: No se encontró 'ffplay'.")
        except Exception as e:
            if my_preview_id == current_preview_id:
                print(f"[Preview] Error al reproducir: {e}")
            
    threading.Thread(target=task, daemon=True).start()



def getLinks(text):
    links = list(filter(lambda line: line != "", text))
    return links

# DESCARGA DE LA CANCION
def download(links, dest_path):
    failed = []

    # Se descarga portada, mp3 y jscn con metadatos
    def progress_hook(d):
        if d['status'] == 'finished':
            print(f"\n[Descarga] Archivo descargado, iniciando conversión: {d['filename']}")

    # Hook final
    def postprocessor_hook(d):
        if d['status'] == 'finished' and d['postprocessor'] == 'EmbedThumbnail':
            print(f"[Metadatos] Carátula y metadatos incrustados con éxito.")
            
            # Se borra la iamagen y archivos residuales
            filepath = d.get('info_dict', {}).get('filepath', '')
            if filepath:
                base_filename = os.path.splitext(filepath)[0]
                potential_images = glob.glob(f"{base_filename}.*")
                for img in potential_images:
                    if img.lower().endswith(('.jpg', '.jpeg', '.webp', '.png')):
                        try:
                            os.remove(img)
                            print(f"[Limpieza] Carátula residual eliminada: {os.path.basename(img)}")
                        except Exception as e:
                            pass

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
        'parse_metadata': [
            {
                'regex': r'(?P<clean_artist>[^,;&]+)',
                'from': 'artist'
            }
        ],
        'outtmpl': f'{dest_path}/%(album_artist|clean_artist|uploader)s/%(album,playlist_title|Singles)s/%(title)s.%(ext)s',
        'nooverwrites': True,
        'ffmpeg_location': FFMPEG_DIR,
        'writethumbnail': True, 
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
            
            # Insercion de Metadatos + Imagen
            {'key': 'FFmpegMetadata', 'add_metadata': True},
            {'key': 'EmbedThumbnail'},
        ],
        'postprocessor_args': {
            'ffmpeg': ['-id3v2_version', '3', '-metadata', 'comment=']
        },
        'quiet': False,
        'progress_hooks': [progress_hook],
        'postprocessor_hooks': [postprocessor_hook], # hook de limpieza final
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(links)
    except Exception as e:
        print(f"Error crítico: {str(e)}")
        failed.append(str(e))

    return failed