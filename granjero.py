import threading
import time
import tkinter as tk
from tkinter import messagebox
import pyautogui

running = threading.Event()
worker_thread = None
remaining_seconds = 0

def format_mmss(s):
    m = s // 60
    ss = s % 60
    return f"{m:02d}:{ss:02d}"

def update_countdown():
    global remaining_seconds
    if running.is_set():
        countdown_var.set(format_mmss(max(0, remaining_seconds)))
        if remaining_seconds > 0:
            remaining_seconds -= 1
        root.after(1000, update_countdown)
    else:
        countdown_var.set("--:--")

def bot_loop(comando, intervalo_min):
    # Hilo que envia el comando cada X minutos mientras running este activo.
    global remaining_seconds
    try:
        intervalo_seg = int(intervalo_min) * 60
    except ValueError:
        status_var.set("Minimo 1min.")
        running.clear()
        return

    if intervalo_seg <= 0:
        status_var.set("Minimo 1min.")
        running.clear()
        return

    status_var.set("Iniciando en 5s… enfoca la ventana del juego!!!")
    initial_wait = remaining_seconds
    for _ in range(initial_wait):
        if not running.is_set():
            break
        time.sleep(1)

    while running.is_set():
        try:
            pyautogui.typewrite(comando)
            pyautogui.press('enter')

            current = send_count_var.get()
            try:
                current = int(current)
            except:
                current = 0
            send_count_var.set(str(current + 1))

            status_var.set(f"Enviado: '{comando}'. Proximo en {intervalo_min}min.")
        except Exception as e:
            status_var.set("Error al enviar teclas.")
            messagebox.showerror("Error", f"Hubo un problema enviando teclas:\n{e}")
            running.clear()
            break

        remaining_seconds = intervalo_seg
        for _ in range(intervalo_seg):
            if not running.is_set():
                break
            time.sleep(1)

    status_var.set("Detenido.")

def start():
    global worker_thread, remaining_seconds
    if running.is_set():
        return

    comando = cmd_entry.get().strip()
    intervalo = interval_entry.get().strip()

    if not comando:
        messagebox.showwarning("Falta comando", "Por favor ingresa el comando a enviar.")
        return
    if not intervalo:
        messagebox.showwarning("Falta intervalo", "Por favor ingresa el intervalo en minutos.")
        return

    send_count_var.set("0")

    running.set()
    start_btn.config(state="disabled")
    stop_btn.config(state="normal")

    remaining_seconds = 5
    update_countdown()

    worker_thread = threading.Thread(target=bot_loop, args=(comando, intervalo), daemon=True)
    worker_thread.start()

def stop():
    global remaining_seconds
    running.clear()
    start_btn.config(state="normal")
    stop_btn.config(state="disabled")
    remaining_seconds = 0

def on_close():
    running.clear()
    root.destroy()

# ---------- UI ----------
root = tk.Tk()
root.title("Granjero vAlpha")
root.resizable(False, False)

title_lbl = tk.Label(root, text="Granjero vAlpha by nachito ツ", font=("Segoe UI", 12, "bold"))
title_lbl.pack(padx=20, pady=(16, 8))

frame_inputs = tk.Frame(root)
frame_inputs.pack(pady=8)

tk.Label(frame_inputs, text="Comando:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
cmd_entry = tk.Entry(frame_inputs, width=24)
cmd_entry.insert(0, "/heal")
cmd_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_inputs, text="Minutos:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
interval_entry = tk.Entry(frame_inputs, width=10)
interval_entry.insert(0, "15")
interval_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Contador de envios
counter_frame = tk.Frame(root)
counter_frame.pack(pady=(0, 4))
tk.Label(counter_frame, text="Envios realizados:").grid(row=0, column=0, padx=5)
send_count_var = tk.StringVar(value="0")
send_count_lbl = tk.Label(counter_frame, textvariable=send_count_var)
send_count_lbl.grid(row=0, column=1, padx=5)

# Cuenta regresiva
cd_frame = tk.Frame(root)
cd_frame.pack(pady=(0, 8))
tk.Label(cd_frame, text="Proximo envio en:").grid(row=0, column=0, padx=5)
countdown_var = tk.StringVar(value="--:--")
countdown_lbl = tk.Label(cd_frame, textvariable=countdown_var)
countdown_lbl.grid(row=0, column=1, padx=5)

buttons = tk.Frame(root)
buttons.pack(pady=8)

start_btn = tk.Button(buttons, text="Comenzar", width=12, command=start)
start_btn.grid(row=0, column=0, padx=6)

stop_btn = tk.Button(buttons, text="Parar", width=12, state="disabled", command=stop)
stop_btn.grid(row=0, column=1, padx=6)

status_var = tk.StringVar(value="Listo.")
status_lbl = tk.Label(root, textvariable=status_var, anchor="w")
status_lbl.pack(fill="x", padx=16, pady=(6, 12))

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
