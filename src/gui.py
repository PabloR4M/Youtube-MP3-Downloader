import threading
import sys
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from backend import setup, download

# Clase para redirigir los "print" a la caja de texto de la GUI
class RedirectText(object):
    def __init__(self, text_widget):
        self.output = text_widget

    def write(self, string):
        # Usamos 'after' para que sea seguro con hilos (Thread-safe)
        self.output.after(0, lambda: self._insert(string))

    def _insert(self, string):
        self.output.insert('end', string)
        self.output.see('end') # Autoscroll hacia abajo

    def flush(self):
        pass

def gui():
    window = ttk.Window(themename="darkly")
    window.title("YouTube -> MP3 Pro")
    window.geometry("600x650")
    window.resizable(False, False)

    # --- LÓGICA DE LA COLA Y HILOS ---
    def run_download_thread(links):
        """Esta función corre en un universo paralelo (hilo secundario)"""
        setup()
        
        print(f"\n--- Iniciando Cola de Descarga ({len(links)} archivos) ---")
        
        # Ejecutamos la descarga (esto tardará un rato)
        failed = download(links)

        print("\n--- Procesos terminados ---")
        if len(failed) == 0:
            print("¡Todo descargado con éxito!")
        else:
            print(f"Errores en {len(failed)} archivos.")
        
        # Al terminar, reactivamos el botón (usando after para volver al hilo principal)
        window.after(0, lambda: down_button.configure(state='normal'))
        window.after(0, lambda: down_button.configure(text='Download Queue'))

    def start_download_process():
        # 1. Obtener links
        raw_text = text_input.get('1.0', 'end')
        links = list(filter(lambda x: x.strip() != "", raw_text.split("\n")))
        
        if not links:
            print("¡La cola está vacía! Pega algunos links primero.")
            return

        # 2. Bloquear botón para no spammear
        down_button.configure(state='disabled')
        down_button.configure(text='Descargando...')
        
        # 3. Limpiar consola de output (opcional, yo prefiero ver el historial)
        # console_output.delete("1.0", "end") 

        # 4. LANZAR EL HILO (Aquí está la magia anti-congelamiento)
        t = threading.Thread(target=run_download_thread, args=(links,))
        t.daemon = True # El hilo muere si cierras la app
        t.start()

    # --- INTERFAZ GRÁFICA (UI) ---
    
    # Título
    title_label = ttk.Label(master=window, text="Downloader & Queue", font='Verdana 18 bold')
    title_label.pack(pady=10)

    # Área de Entrada (Donde pegas los links)
    lbl_inst = ttk.Label(window, text="1. Pega tus links aquí (uno por línea):", bootstyle="info")
    lbl_inst.pack(anchor="w", padx=20)
    
    text_input = ttk.Text(window, wrap='none', width=65, height=8)
    text_input.pack(pady=5, padx=20)

    # Botón de Acción
    input_frame = ttk.Frame(master=window)
    down_button = ttk.Button(master=input_frame, text='Download Queue', command=start_download_process, bootstyle="success-outline", width=20)
    down_button.pack()
    input_frame.pack(pady=10)

    # Área de Salida (Consola)
    lbl_cons = ttk.Label(window, text="2. Estado del proceso:", bootstyle="secondary")
    lbl_cons.pack(anchor="w", padx=20)

    console_output = ttk.Text(window, wrap='word', width=75, height=15, font=("Consolas", 9))
    console_output.pack(pady=5, padx=20)
    
    # Redirigir prints a la consola de la UI
    sys.stdout = RedirectText(console_output)
    # sys.stderr = RedirectText(console_output) # Descomenta si quieres ver errores rojos de Python también

    print("Sistema listo. Esperando links...")

    window.mainloop()

# Esto permite probar el gui.py directamente
if __name__ == "__main__":
    gui()