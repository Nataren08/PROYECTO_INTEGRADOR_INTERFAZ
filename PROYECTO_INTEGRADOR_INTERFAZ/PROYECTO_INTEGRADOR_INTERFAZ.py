import serial
import serial.tools.list_ports
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

def encontrar_puerto():
    puertos = list(serial.tools.list_ports.comports())
    for p in puertos:
        if "ARDUINO" in p.description or "CH340" in p.description or "USB-SERIAL" in p.description:
            return p.device
    return None

class InterfazElevador:
    def _init_(self, master):
        self.master = master
        master.title("CONTROL DE ELEVADOR")
        master.geometry("500x400")

        self.serial_port = None
        self.leyendo = True

        # Cuadro de texto para mostrar LOGS
        self.texto = scrolledtext.ScrolledText(master, height=10, state='disabled', bg='black', fg='lime')
        self.texto.pack(padx=10, pady=10, fill='x')

        # BOTONES DE LOS PISOS
        frame_botones = tk.Frame(master)
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Ir a PB", command=lambda: self.enviar_comando('0')).grid(row=0, column=0, padx=10)
        tk.Button(frame_botones, text="Ir a P1", command=lambda: self.enviar_comando('1')).grid(row=0, column=1, padx=10)
        tk.Button(frame_botones, text="Ir a P2", command=lambda: self.enviar_comando('2')).grid(row=0, column=2, padx=10)
        tk.Button(frame_botones, text="DETENER", fg="red", command=lambda: self.enviar_comando('S')).grid(row=0, column=3, padx=10)

        # ESTADO DE CONEXION
        self.label_estado = tk.Label(master, text="ESTADO: BUSCANDO ARDUINO....", fg="blue")
        self.label_estado.pack(pady=5)

        # ALERTA VISUAL
        self.alerta = tk.Label(master, text="", font=("Arial", 14), fg="red")
        self.alerta.pack()

        # INICIALIZAR CONEXION SERIAL
        self.inicializar_serial()

        # HILO DE LECTURA LOCALw
        self.hilo_lectura = threading.Thread(target=self.leer_serial, daemon=True)
        self.hilo_lectura.start()

    def inicializar_serial(self):
        puerto = encontrar_puerto()
        if puerto:
            try:
                self.serial_port = serial.Serial(puerto, 9600, timeout=1)
                mensaje = f"CONECTADO A  {puerto}"
                self.label_estado.config(text=mensaje, fg="green")
                self.mostrar_mensaje(mensaje)
            except Exception as e:
                mensaje = f"ERROR DE CONEXION: {e}"
                self.label_estado.config(text=mensaje, fg="red")
                self.mostrar_mensaje(mensaje)
        else:
            mensaje = "ARDUINO NO ENCONTRADO"
            self.label_estado.config(text=mensaje, fg="red")
            self.mostrar_mensaje(mensaje)

    def enviar_comando(self, cmd):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(cmd.encode())
            self.mostrar_mensaje(f"→ Comando enviado: {cmd}")
        else:
            self.mostrar_mensaje(" No se puede enviar comando: PUERTO NO DISPONIBLE")

    def leer_serial(self):
        while self.leyendo:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    linea = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if linea:
                        self.mostrar_mensaje(f"← {linea}")
                        self.verificar_alertas(linea)
            except Exception as e:
                self.mostrar_mensaje(f"ERROR: LEYENDO PUERTO SERIAL {e}")

    def mostrar_mensaje(self, mensaje):
        self.texto.configure(state='normal')
        self.texto.insert(tk.END, mensaje + '\n')
        self.texto.see(tk.END)
        self.texto.configure(state='disabled')

    def verificar_alertas(self, mensaje):
        msg = mensaje.lower()
        if "humo" in msg:
            self.alerta.config(text=" HUMO DETECTADO")
        elif "LIMITE DE PESO EXEDIDO" in msg:
            self.alerta.config(text=" PESO EXCEDIDO")
        elif "OBSTACULO" in msg:
            self.alerta.config(text=" OBSTÁCULO DETECTADO")
        elif "AMBIENTE SEGURO" in msg or "SISTEMA EN PAUSA" in msg:
            self.alerta.config(text="")

    def cerrar(self):
        self.leyendo = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.mostrar_mensaje("PUERTO SERIAL CERRADO")
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InterfazElevador(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()