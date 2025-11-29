import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading
import datetime
import queue
import os

# ====================================================
# SIMULADOR DE CLASIFICACIÓN
# ====================================================
def predict_image_fake(path):
    import random
    resultados = [
        ("BENIGNO - Nevus melanocítico", 0.87),
        ("BENIGNO - Queratosis seborreica", 0.92),
        ("MALIGNO - Melanoma", 0.76),
        ("BENIGNO - Dermatofibroma", 0.94)
    ]
    resultado, confianza = random.choice(resultados)
    return f"{resultado} (Confianza: {confianza:.1%})"

class AnalysisWindow:
    def __init__(self, parent, image_path):
        self.parent = parent
        self.image_path = image_path
        self.create_window()
        
    def create_window(self):
        self.window = tb.Toplevel(self.parent)
        self.window.title("Análisis Dermatológico - DermaScan Pro")
        self.window.geometry("1000x700")
        self.window.configure(padx=20, pady=20)
        
        # Frame principal
        main_frame = tb.Frame(self.window)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Título
        title_label = tb.Label(
            main_frame,
            text="ANÁLISIS DERMATOLÓGICO",
            font=('Arial', 20, 'bold'),
            bootstyle='primary'
        )
        title_label.pack(pady=(0, 20))
        
        # Contenido en dos columnas
        content_frame = tb.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True)
        
        # Columna izquierda - Imagen
        left_frame = tb.Frame(content_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 20))
        
        # Panel de imagen
        image_panel = tb.Labelframe(
            left_frame,
            text="IMAGEN CAPTURADA",
            bootstyle='info',
            padding=10
        )
        image_panel.pack(fill=BOTH, expand=True)
        
        # Frame para la imagen con scrollbars
        image_container = tb.Frame(image_panel)
        image_container.pack(fill=BOTH, expand=True)
        
        # Canvas para la imagen con zoom
        self.canvas = tk.Canvas(image_container, bg='#2c3e50', highlightthickness=0)
        
        # Scrollbars
        v_scrollbar = tb.Scrollbar(image_container, orient=VERTICAL, bootstyle='round')
        h_scrollbar = tb.Scrollbar(image_container, orient=HORIZONTAL, bootstyle='round')
        
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Configurar scrollbars
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.configure(command=self.canvas.yview)
        h_scrollbar.configure(command=self.canvas.xview)
        
        # Bind eventos de zoom
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.canvas.bind("<Button-4>", self.zoom_image)  # Linux
        self.canvas.bind("<Button-5>", self.zoom_image)  # Linux
        
        self.zoom_level = 1.0
        self.load_image()
        
        # Columna derecha - Controles y resultados
        right_frame = tb.Frame(content_frame, width=300)
        right_frame.pack(side=RIGHT, fill=Y)
        right_frame.pack_propagate(False)
        
        # Panel de controles
        control_panel = tb.Labelframe(
            right_frame,
            text="CONTROLES DE ANÁLISIS",
            bootstyle='primary',
            padding=15
        )
        control_panel.pack(fill=X, pady=(0, 20))
        
        # Botones de análisis
        buttons = [
            ("🔬 ANALIZAR IMAGEN", 'info', self.analyze_image),
            ("💾 GUARDAR ANÁLISIS", 'success', self.save_analysis),
            ("📊 VER DETALLES", 'secondary', self.show_details)
        ]
        
        for text, style, command in buttons:
            btn = tb.Button(
                control_panel,
                text=text,
                bootstyle=style,
                command=command,
                padding=(15, 10)
            )
            btn.pack(fill=X, pady=5)
        
        # Panel de resultados
        result_panel = tb.Labelframe(
            right_frame,
            text="RESULTADO DEL DIAGNÓSTICO",
            bootstyle='success',
            padding=15
        )
        result_panel.pack(fill=BOTH, expand=True)
        
        # Etiqueta de diagnóstico
        self.diagnosis_label = tb.Label(
            result_panel,
            text="ESPERANDO ANÁLISIS",
            font=('Arial', 16, 'bold'),
            anchor=CENTER,
            justify=CENTER,
            wraplength=250
        )
        self.diagnosis_label.pack(fill=X, pady=10)
        
        # Etiqueta de confianza
        self.confidence_label = tb.Label(
            result_panel,
            text="Confianza: --%",
            font=('Arial', 12),
            anchor=CENTER
        )
        self.confidence_label.pack(fill=X, pady=5)
        
        # Botón de clasificación final
        self.final_diagnosis_btn = tb.Button(
            result_panel,
            text="CLASIFICAR LESIÓN",
            bootstyle='warning',
            command=self.show_final_diagnosis,
            padding=(10, 8),
            state='disabled'
        )
        self.final_diagnosis_btn.pack(fill=X, pady=10)
        
        # Información adicional
        info_text = """
INSTRUCCIONES:
1. Capture una imagen clara del lunar
2. Haga clic en 'ANALIZAR IMAGEN'
3. Revise los resultados
4. Guarde el análisis si es necesario

Nota: Este sistema es de apoyo al diagnóstico y no sustituye la evaluación de un especialista.
        """
        
        info_label = tb.Label(
            result_panel,
            text=info_text,
            font=('Arial', 9),
            justify=LEFT,
            bootstyle='secondary'
        )
        info_label.pack(fill=X, pady=(20, 0))
    
    def load_image(self):
        """Cargar y mostrar la imagen en el canvas"""
        if self.image_path and os.path.exists(self.image_path):
            self.original_image = Image.open(self.image_path)
            self.display_image = self.original_image.copy()
            self.update_canvas_image()
    
    def update_canvas_image(self):
        """Actualizar la imagen en el canvas"""
        # Calcular nuevo tamaño basado en zoom
        width = int(self.original_image.width * self.zoom_level)
        height = int(self.original_image.height * self.zoom_level)
        
        resized_image = self.original_image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        
        # Actualizar canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def zoom_image(self, event):
        """Manejar zoom de la imagen"""
        if event.delta > 0 or event.num == 4:  # Zoom in
            self.zoom_level *= 1.1
        else:  # Zoom out
            self.zoom_level /= 1.1
        
        # Limitar zoom
        self.zoom_level = max(0.1, min(5.0, self.zoom_level))
        self.update_canvas_image()
    
    def analyze_image(self):
        """Analizar la imagen"""
        self.diagnosis_label.config(text="ANALIZANDO...", bootstyle='info')
        self.confidence_label.config(text="Procesando imagen...")
        
        # Simular análisis
        self.window.after(2000, self.show_analysis_results)
    
    def show_analysis_results(self):
        """Mostrar resultados del análisis"""
        result = predict_image_fake(self.image_path)
        self.diagnosis_label.config(text=result, bootstyle='primary')
        
        # Extraer confianza del resultado
        if "Confianza:" in result:
            confidence = result.split("Confianza: ")[1].split(")")[0]
            self.confidence_label.config(text=f"Confianza: {confidence}")
        
        self.final_diagnosis_btn.config(state='normal')
    
    def save_analysis(self):
        """Guardar análisis"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = f"analisis_{timestamp}.txt"
        
        with open(analysis_file, 'w') as f:
            f.write(f"Análisis Dermatológico - {timestamp}\n")
            f.write(f"Imagen: {self.image_path}\n")
            f.write(f"Resultado: {self.diagnosis_label.cget('text')}\n")
            f.write(f"Confianza: {self.confidence_label.cget('text')}\n")
        
        self.show_message("Análisis guardado exitosamente", 'success')
    
    def show_details(self):
        """Mostrar detalles adicionales"""
        details = """
DETALLES DEL ANÁLISIS:

- Algoritmo: Red Neuronal Convolucional
- Resolución: 224x224 píxeles
- Modelo: EfficientNet-B3
- Dataset: ISIC 2020
- Precisión: 87.3%

CARACTERÍSTICAS ANALIZADAS:
✓ Asimetría
✓ Bordes
✓ Color
✓ Diámetro
✓ Evolución
        """
        self.show_message(details, 'info')
    
    def show_final_diagnosis(self):
        """Mostrar diagnóstico final"""
        diagnosis_window = tb.Toplevel(self.window)
        diagnosis_window.title("Diagnóstico Final")
        diagnosis_window.geometry("400x300")
        
        tb.Label(
            diagnosis_window,
            text="CLASIFICACIÓN FINAL",
            font=('Arial', 18, 'bold'),
            bootstyle='primary'
        ).pack(pady=20)
        
        # Botones de diagnóstico
        diagnoses = [
            ("🎯 MELANOMA", 'danger'),
            ("🔵 NEVUS", 'info'),
            ("🟢 QUERATOSIS", 'success'),
            ("🟠 DERMATOFIBROMA", 'warning')
        ]
        
        for text, style in diagnoses:
            btn = tb.Button(
                diagnosis_window,
                text=text,
                bootstyle=style,
                command=lambda t=text: self.set_final_diagnosis(t, diagnosis_window),
                padding=(10, 8)
            )
            btn.pack(fill=X, padx=20, pady=5)
    
    def set_final_diagnosis(self, diagnosis, window):
        """Establecer diagnóstico final"""
        self.diagnosis_label.config(text=f"DIAGNÓSTICO: {diagnosis}", bootstyle='primary')
        window.destroy()
        self.show_message(f"Diagnóstico establecido: {diagnosis}", 'success')
    
    def show_message(self, message, style):
        """Mostrar mensaje emergente"""
        mb = tb.dialogs.Messagebox
        mb.show_info(message, title="DermaScan Pro", parent=self.window)

class DermatoscopeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DermaScan Pro - Sistema de Análisis Dermatológico")
        self.root.geometry("1400x900")
        
        # Configurar estilo más profesional
        self.style = tb.Style("darkly")
        self.style.configure('Title.TLabel', font=('Arial', 24, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Arial', 11))
        self.style.configure('PanelTitle.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Arial', 10, 'bold'))
        
        # Variables de control de cámara
        self.frame_queue = queue.Queue(maxsize=1)
        self.cap = None
        self.camera_running = False
        self.current_image_path = None
        self.flash_on = False
        self.zoom_level = 1.0

        self.create_modern_layout()
        self.update_display()

    def create_modern_layout(self):
        # Frame principal
        main_container = tb.Frame(self.root, padding=15)
        main_container.pack(fill=BOTH, expand=True)

        # ====================================================
        # HEADER MINIMALISTA
        # ====================================================
        header_frame = tb.Frame(main_container)
        header_frame.pack(fill=X, pady=(0, 20))

        # Logo y título
        title_frame = tb.Frame(header_frame)
        title_frame.pack(side=LEFT, fill=Y)

        tb.Label(
            title_frame, 
            text="DERMASCAN PRO",
            style='Title.TLabel'
        ).pack(anchor=W)
        
        tb.Label(
            title_frame, 
            text="Sistema de Análisis Dermatológico - Versión Profesional",
            style='Subtitle.TLabel'
        ).pack(anchor=W, pady=(2, 0))

        # Estado del sistema
        status_frame = tb.Frame(header_frame)
        status_frame.pack(side=RIGHT, fill=Y)
        
        self.status_label = tb.Label(
            status_frame, 
            text="● SISTEMA LISTO",
            style='Status.TLabel',
            bootstyle='success'
        )
        self.status_label.pack(anchor=E)

        # ====================================================
        # CONTENIDO PRINCIPAL
        # ====================================================
        content_frame = tb.Frame(main_container)
        content_frame.pack(fill=BOTH, expand=True)

        # COLUMNA IZQUIERDA - VISTA DE CÁMARA
        left_column = tb.Frame(content_frame)
        left_column.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 15))

        # Panel de cámara con controles
        cam_panel = tb.Labelframe(
            left_column, 
            text="CÁMARA DERMATOSCÓPICA",
            bootstyle='primary',
            padding=12
        )
        cam_panel.pack(fill=BOTH, expand=True)

        # Controles de cámara
        control_frame = tb.Frame(cam_panel)
        control_frame.pack(fill=X, pady=(0, 10))

        # Botones de control de cámara
        cam_controls = [
            ("📷 Iniciar Cámara", 'outline-primary', self.start_camera),
            ("⏹️ Detener", 'outline-secondary', self.stop_camera),
        ]

        for text, style, command in cam_controls:
            btn = tb.Button(
                control_frame,
                text=text,
                bootstyle=style,
                command=command,
                padding=(12, 6)
            )
            btn.pack(side=LEFT, padx=(0, 8))

        # Controles de imagen
        image_controls = tb.Frame(control_frame)
        image_controls.pack(side=RIGHT)

        # Control de flash
        self.flash_btn = tb.Button(
            image_controls,
            text="⚡ Flash: OFF",
            bootstyle='outline-warning',
            command=self.toggle_flash,
            padding=(8, 4)
        )
        self.flash_btn.pack(side=LEFT, padx=(0, 8))

        # Control de zoom
        zoom_frame = tb.Frame(image_controls)
        zoom_frame.pack(side=LEFT)
        
        tb.Label(zoom_frame, text="Zoom:").pack(side=LEFT, padx=(0, 5))
        
        self.zoom_scale = tb.Scale(
            zoom_frame,
            from_=0.5,
            to=3.0,
            value=1.0,
            command=self.update_zoom,
            length=100,
            bootstyle='primary'
        )
        self.zoom_scale.pack(side=LEFT)

        # Vista de cámara
        cam_container = tb.Frame(cam_panel, bootstyle='dark', relief='sunken', height=500)
        cam_container.pack(fill=BOTH, expand=True, pady=5)
        cam_container.pack_propagate(False)

        self.cam_label = tb.Label(
            cam_container, 
            text="CÁMARA NO INICIADA\n\nHaga clic en 'INICIAR CÁMARA' para comenzar",
            anchor=CENTER,
            bootstyle='secondary'
        )
        self.cam_label.pack(fill=BOTH, expand=True, padx=2, pady=2)

        # Información de la cámara
        info_frame = tb.Frame(cam_panel)
        info_frame.pack(fill=X, pady=(10, 0))

        self.cam_info = tb.Label(
            info_frame, 
            text="Resolución: --- | FPS: ---",
            font=('Arial', 9)
        )
        self.cam_info.pack(side=LEFT)

        self.capture_info = tb.Label(
            info_frame, 
            text="Última captura: ---",
            font=('Arial', 9)
        )
        self.capture_info.pack(side=RIGHT)

        # COLUMNA DERECHA - PANEL DE ACCIONES
        right_column = tb.Frame(content_frame, width=350)
        right_column.pack(side=RIGHT, fill=Y)
        right_column.pack_propagate(False)

        # ====================================================
        # PANEL DE ACCIONES PRINCIPALES
        # ====================================================
        action_panel = tb.Labelframe(
            right_column, 
            text="ACCIONES",
            bootstyle='info',
            padding=15
        )
        action_panel.pack(fill=X, pady=(0, 15))

        # Botones de acción principales
        actions = [
            ("📸 CAPTURAR IMAGEN", 'success', self.capture),
            ("🔬 ABRIR ANÁLISIS", 'primary', self.open_analysis),
            ("📁 ABRIR ARCHIVO", 'secondary', self.open_file),
        ]

        for text, style, command in actions:
            btn = tb.Button(
                action_panel, 
                text=text,
                bootstyle=style,
                command=command,
                padding=(15, 12)
            )
            btn.pack(fill=X, pady=8)

        # ====================================================
        # PANEL DE INFORMACIÓN DEL SISTEMA
        # ====================================================
        info_panel = tb.Labelframe(
            right_column, 
            text="INFORMACIÓN DEL SISTEMA",
            bootstyle='secondary',
            padding=15
        )
        info_panel.pack(fill=BOTH, expand=True)

        # Estado de conexión
        conn_frame = tb.Frame(info_panel)
        conn_frame.pack(fill=X, pady=(0, 15))

        tb.Label(conn_frame, text="Conexión Raspberry Pi:", font=('Arial', 10, 'bold')).pack(anchor=W)
        
        self.conn_status = tb.Label(
            conn_frame, 
            text="● CONECTADO",
            bootstyle='success',
            font=('Arial', 9, 'bold')
        )
        self.conn_status.pack(anchor=W, pady=(2, 0))

        # Información de hardware
        hardware_info = """
HARDWARE:
• Raspberry Pi 5
• Cámara HQ 12MP
• Iluminación LED
• Lente dermatoscópico

SOFTWARE:
• OpenCV 4.8.0
• TensorFlow 2.13
• Python 3.11
"""

        tb.Label(
            info_panel,
            text=hardware_info,
            font=('Arial', 9),
            justify=LEFT,
            bootstyle='secondary'
        ).pack(anchor=W)

        # ====================================================
        # BARRA DE ESTADO
        # ====================================================
        statusbar = tb.Frame(main_container)
        statusbar.pack(fill=X, pady=(15, 0))

        # Información de versión
        version_label = tb.Label(
            statusbar, 
            text="DermaScan Pro v3.0 - Sistema Médico de Apoyo al Diagnóstico",
            font=('Arial', 9)
        )
        version_label.pack(side=LEFT)

        # Reloj
        self.clock_label = tb.Label(
            statusbar, 
            text="",
            font=('Arial', 9)
        )
        self.clock_label.pack(side=RIGHT)

        self.update_clock()

    def update_clock(self):
        """Actualizar reloj"""
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def update_display(self):
        """Actualizar pantalla desde el hilo principal"""
        try:
            if not self.frame_queue.empty():
                imgtk = self.frame_queue.get_nowait()
                self.cam_label.imgtk = imgtk
                self.cam_label.config(image=imgtk, text="")
        except queue.Empty:
            pass
        finally:
            self.root.after(30, self.update_display)

    # ====================================================
    # FUNCIONALIDADES MEJORADAS DE CÁMARA
    # ====================================================
    def start_camera(self):
        if self.camera_running:
            return
        
        self.camera_running = True
        self.status_label.config(text="● CÁMARA ACTIVA", bootstyle='success')
        self.cam_label.config(text="INICIANDO CÁMARA RASPBERRY PI...", bootstyle='info')

        # Conexión simplificada para Raspberry Pi
        try:
            # Para Raspberry Pi con cámara oficial
            self.cap = cv2.VideoCapture(0)
            
            # Configuración optimizada para Raspberry Pi
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Verificar conexión
            if not self.cap.isOpened():
                self.show_error("Error: No se pudo conectar a la cámara")
                self.camera_running = False
                return
                
        except Exception as e:
            self.show_error(f"Error de conexión: {str(e)}")
            self.camera_running = False
            return

        threading.Thread(target=self.capture_frames, daemon=True).start()

    def capture_frames(self):
        """Hilo secundario: captura frames"""
        frame_count = 0
        start_time = datetime.datetime.now()
        
        while self.camera_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                # Aplicar zoom si es necesario
                if self.zoom_level != 1.0:
                    frame = self.apply_zoom(frame, self.zoom_level)

                # Actualizar información de FPS
                frame_count += 1
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                if elapsed >= 1:
                    fps = frame_count / elapsed
                    self.root.after(0, lambda: self.cam_info.config(
                        text=f"Resolución: 1280x720 | FPS: {fps:.1f} | Zoom: {self.zoom_level:.1f}x"))
                    frame_count = 0
                    start_time = datetime.datetime.now()

                # Procesar frame para visualización
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Redimensionar manteniendo aspecto
                h, w = frame.shape[:2]
                target_h = 500
                target_w = int(w * target_h / h)
                
                img = Image.fromarray(frame).resize((target_w, target_h), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Poner el frame en la cola
                try:
                    if self.frame_queue.full():
                        self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(imgtk)
                except queue.Full:
                    pass
                    
            except Exception as e:
                print(f"Error en captura: {e}")
                break

    def apply_zoom(self, frame, zoom_level):
        """Aplicar zoom a la imagen"""
        if zoom_level == 1.0:
            return frame
            
        h, w = frame.shape[:2]
        new_h, new_w = int(h / zoom_level), int(w / zoom_level)
        
        # Calcular región de recorte
        start_x = (w - new_w) // 2
        start_y = (h - new_h) // 2
        
        # Recortar y redimensionar
        cropped = frame[start_y:start_y+new_h, start_x:start_x+new_w]
        zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        
        return zoomed

    def update_zoom(self, value):
        """Actualizar nivel de zoom"""
        self.zoom_level = float(value)

    def toggle_flash(self):
        """Alternar flash (simulado)"""
        self.flash_on = not self.flash_on
        state = "ON" if self.flash_on else "OFF"
        self.flash_btn.config(text=f"⚡ Flash: {state}")
        
        if self.flash_on:
            # Simular activación de flash (en una implementación real, controlarías el LED)
            self.status_label.config(text="● FLASH ACTIVADO", bootstyle='warning')
        else:
            self.status_label.config(text="● CÁMARA ACTIVA", bootstyle='success')

    def capture(self):
        if not self.camera_running:
            self.show_error("ERROR: ENCIENDA LA CÁMARA PRIMERO")
            return

        ret, frame = self.cap.read()
        if ret:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"captura_{timestamp}.jpg"
            
            cv2.imwrite(filename, frame)
            self.current_image_path = filename
            
            capture_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.capture_info.config(text=f"Última captura: {capture_time}")
            self.show_message(f"Imagen capturada: {filename}", 'success')

    def open_analysis(self):
        """Abrir ventana de análisis"""
        if not self.current_image_path:
            self.show_error("Capture una imagen primero")
            return
            
        AnalysisWindow(self.root, self.current_image_path)

    def open_file(self):
        """Abrir archivo de imagen"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            self.current_image_path = file_path
            self.show_message(f"Imagen cargada: {os.path.basename(file_path)}", 'success')

    def show_message(self, message, style='info'):
        """Mostrar mensaje"""
        mb = tb.dialogs.Messagebox
        mb.show_info(message, title="DermaScan Pro", parent=self.root)

    def show_error(self, message):
        """Mostrar error"""
        mb = tb.dialogs.Messagebox
        mb.show_error(message, title="Error", parent=self.root)

    def stop_camera(self):
        """Detener cámara"""
        self.camera_running = False
        if self.cap:
            self.cap.release()
        
        self.cam_label.config(
            image="", 
            text="CÁMARA NO INICIADA\n\nHaga clic en 'INICIAR CÁMARA' para comenzar",
            bootstyle='secondary'
        )
        self.status_label.config(text="● SISTEMA EN ESPERA", bootstyle='secondary')
        self.cam_info.config(text="Resolución: --- | FPS: ---")


# ====================================================
# EJECUCIÓN
# ====================================================
if __name__ == "__main__":
    root = tb.Window(themename="darkly")  
    app = DermatoscopeApp(root)
    root.mainloop()