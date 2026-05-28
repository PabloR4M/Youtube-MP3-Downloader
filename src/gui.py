import threading
import sys
import os
import urllib.request
import io
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

# funciones backend
from backend import setup, download, search_music, play_audio_preview

class RedirectText(object):
    def __init__(self, text_widget):
        self.output = text_widget
    def write(self, string):
        self.output.after(0, lambda: self._insert(string))
    def _insert(self, string):
        self.output.insert('end', string)
        self.output.see('end') 
    def flush(self):
        pass

def gui():
    window = ttk.Window(themename="darkly")
    window.title("YouTube -> MP3 Pro")
    window.geometry("850x850") 
    window.resizable(False, False)

    # Variables
    dest_path_var = tk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Music'))
    current_search_results = []
    
    # Variable para filtro de búsqueda
    filter_var = tk.StringVar(value="songs") # Por defecto


    # --- FUNCIONES ---
    def browse_folder():
        folder = filedialog.askdirectory(initialdir=dest_path_var.get(), title="Seleccionar Destino")
        if folder:
            dest_path_var.set(folder)

    def execute_search():
        query = search_entry.get().strip()
        if not query: return
        
        search_btn.configure(state='disabled', text='Buscando...')
        
        for w in results_container.winfo_children():
            w.destroy()
        ttk.Label(results_container, text="Buscando y descargando portadas...").grid(row=0, column=0, pady=20, padx=20)

        def search_thread():
            nonlocal current_search_results
            
            q_filter = filter_var.get()
            if q_filter == "": q_filter = None 
            
            raw_results = search_music(query, search_filter=q_filter, max_results=12)
            
            # Descargar imágenes de las portadas en segundo plano
            for res in raw_results:
                res['pil_image'] = None
                if res['thumbnail']:
                    try:
                        req = urllib.request.Request(res['thumbnail'], headers={'User-Agent': 'Mozilla/5.0'})
                        raw_data = urllib.request.urlopen(req, timeout=3).read()
                        im = Image.open(io.BytesIO(raw_data))
                        res['pil_image'] = im.resize((45, 45), Image.Resampling.LANCZOS)
                    except:
                        pass
                        
            current_search_results = raw_results
            window.after(0, update_results_ui)

        t = threading.Thread(target=search_thread)
        t.daemon = True
        t.start()

    def add_to_queue(res):
        url = res['url']
        title = res['title']
        current_text = text_input.get('1.0', 'end').strip()
        if current_text:
            text_input.insert('end', f"\n{url}")
        else:
            text_input.insert('end', f"{url}")
        print(f"[✅ Añadido a la cola] {title}")

    def update_results_ui():
        for w in results_container.winfo_children():
            w.destroy()
        
        if not current_search_results:
            ttk.Label(results_container, text="No se encontraron resultados.").grid(row=0, column=0, pady=20, padx=20)
            search_btn.configure(state='normal', text='Buscar')
            return

        # Títulos de columnas
        ttk.Label(results_container, text="🎧", font="bold").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(results_container, text="Título", font="bold").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(results_container, text="Artista", font="bold").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(results_container, text="Tipo", font="bold").grid(row=0, column=3, sticky="w", padx=5, pady=5)
        ttk.Label(results_container, text="Acción", font="bold").grid(row=0, column=4, padx=5, pady=5)
        
        for i, res in enumerate(current_search_results, start=1):
            title = res['title'] if len(res['title']) < 38 else res['title'][:35] + "..."
            artist = res['artist'] if len(res['artist']) < 25 else res['artist'][:22] + "..."
            
            # Cargar imagen
            photo = None
            if res.get('pil_image'):
                photo = ImageTk.PhotoImage(res['pil_image'])
            
            # Label de imagen, Click para Reproducir
            img_lbl = ttk.Label(results_container, image=photo, cursor="hand2")
            img_lbl.image = photo # Guardar en memoria para que no desaparezca
            img_lbl.grid(row=i, column=0, padx=5, pady=5)
            
            # Vincular el clic de la imagen a función preview
            img_lbl.bind("<Button-1>", lambda e, u=res['url']: play_audio_preview(u))
            
            ttk.Label(results_container, text=title).grid(row=i, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(results_container, text=artist).grid(row=i, column=2, sticky="w", padx=5, pady=5)
            ttk.Label(results_container, text=res['type']).grid(row=i, column=3, sticky="w", padx=5, pady=5)
            
            btn = ttk.Button(results_container, text="➕ Agregar", bootstyle="success", command=lambda r=res: add_to_queue(r))
            btn.grid(row=i, column=4, padx=5, pady=5)
                       
        search_btn.configure(state='normal', text='Buscar')

    def run_download_thread(links, path):
        setup()
        print(f"\n--- Iniciando Cola de Descarga ({len(links)} archivos) en: {path} ---")
        failed = download(links, path)
        print("\n--- Procesos terminados ---")
        window.after(0, lambda: down_button.configure(state='normal', text='🚀 Descargar Cola'))

    def start_download_process():
        raw_text = text_input.get('1.0', 'end')
        links = list(filter(lambda x: x.strip() != "", raw_text.split("\n")))
        if not links:
            print("¡La cola está vacía!")
            return
        down_button.configure(state='disabled', text='Descargando...')
        t = threading.Thread(target=run_download_thread, args=(links, dest_path_var.get()))
        t.daemon = True 
        t.start()


    # --- INTERFAZ GRÁFICA (UI) ---
    title_label = ttk.Label(master=window, text="Downloader & Queue", font='Verdana 18 bold')
    title_label.pack(pady=(10, 5))

    path_frame = ttk.LabelFrame(window, text="Ruta de Descarga")
    ttk.Entry(path_frame, textvariable=dest_path_var, width=70).pack(side="left", padx=5, pady=10)
    ttk.Button(path_frame, text="Explorar", command=browse_folder, bootstyle="secondary").pack(side="left", padx=5)
    path_frame.pack(fill="x", padx=20, pady=5)

    notebook = ttk.Notebook(window)
    notebook.pack(fill='both', expand=True, padx=20, pady=5)

    tab_search = ttk.Frame(notebook)
    tab_manual = ttk.Frame(notebook)
    notebook.add(tab_search, text="🔍 Buscador")
    notebook.add(tab_manual, text="📝 Manual / Cola de Links")

    # --- DESCARGAS, BUSCADOR ---
    search_input_frame = ttk.Frame(tab_search)
    search_entry = ttk.Entry(search_input_frame, width=70)
    search_entry.pack(side="left", padx=5)
    search_entry.bind('<Return>', lambda event: execute_search()) 
    search_btn = ttk.Button(search_input_frame, text="Buscar", command=execute_search, bootstyle="primary")
    search_btn.pack(side="left", padx=5)
    search_input_frame.pack(pady=10)

    # Filtros
    filter_frame = ttk.Frame(tab_search)
    ttk.Label(filter_frame, text="Filtro:", font="bold").pack(side="left", padx=5)
    ttk.Radiobutton(filter_frame, text="Canciones", variable=filter_var, value="songs").pack(side="left", padx=5)
    ttk.Radiobutton(filter_frame, text="Álbumes", variable=filter_var, value="albums").pack(side="left", padx=5)
    ttk.Radiobutton(filter_frame, text="Playlists", variable=filter_var, value="playlists").pack(side="left", padx=5)
    filter_frame.pack(pady=5)

    # --- SCROLL DE BUSQUEDA ---
    scroll_frame = ttk.Frame(tab_search)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

    canvas = tk.Canvas(scroll_frame, bg="#222222", highlightthickness=0)
    scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
    results_container = ttk.Frame(canvas)
    
    results_window = canvas.create_window((0, 0), window=results_container, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Actualizar zona desplazable 
    results_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(results_window, width=e.width))

    # Scroll con la rueda del ratón si el mouse está encima
    def on_mousewheel(event):
        try: canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except: pass
        
    canvas.bind('<Enter>', lambda e: window.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind('<Leave>', lambda e: window.unbind_all("<MouseWheel>"))

    # --- DESCARGAS, MANUAL ---
    lbl_inst = ttk.Label(tab_manual, text="Pega tus links aquí (uno por línea):", bootstyle="info")
    lbl_inst.pack(anchor="w", padx=10, pady=(15,5))
    text_input = ttk.Text(tab_manual, wrap='none', width=85, height=12)
    text_input.pack(pady=5, padx=10)

    # --- GLOBAL ---
    down_button = ttk.Button(window, text='Descargar Cola Completa', command=start_download_process, bootstyle="info", width=30)
    down_button.pack(pady=(5, 5))

    lbl_cons = ttk.Label(window, text="Consola:")
    lbl_cons.pack(anchor="w", padx=20)
    console_output = ttk.Text(window, wrap='word', width=90, height=7, font=("Consolas", 9))
    console_output.pack(pady=(5, 15), padx=20)
    
    sys.stdout = RedirectText(console_output)
    print("Sistema listo. Al buscar, haz clic en la foto de la canción para escuchar un fragmento (15s).")
    
    window.mainloop()

if __name__ == "__main__":
    gui()