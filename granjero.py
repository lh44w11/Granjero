import threading
import time
import tkinter as tk
from tkinter import messagebox
import pyautogui
import random
import os
import platform
from datetime import datetime


class BotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Granjero v2.0")
        self.root.resizable(True, True)   # Ventana redimensionable
        self.root.geometry("500x600")     # Tamaño inicial

        # Estado
        self.running = threading.Event()
        self.worker_thread = None
        self.remaining_seconds = 0
        self.quit_remaining_seconds = 0

        # Variables Tkinter
        self.send_count_var = tk.StringVar(value="0")
        self.next_send_var = tk.StringVar(value="--:--")
        self.autoquit_countdown_var = tk.StringVar(value="--")
        self.status_var = tk.StringVar(value="Listo.")
        self.auto_quit_var = tk.IntVar(value=0)
        self.random_interval_var = tk.IntVar(value=0)
        self.multi_cmd_var = tk.IntVar(value=0)
        self.shutdown_var = tk.IntVar(value=0)

        self.build_ui()
        self.set_status("Listo.", "black")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------------------- Helpers --------------------
    def format_mmss(self, s):
        if s <= 0:
            return "00:00"
        m, ss = divmod(s, 60)
        return f"{m:02d}:{ss:02d}"

    def format_minutes_from_seconds(self, s):
        if s <= 0:
            return "00 min"
        minutes = (s + 59) // 60
        return f"{minutes:02d} min"

    def log_event(self, text, level="info"):
        hora = datetime.now().strftime("%H:%M:%S")
        line = f"[{hora}] {text}\n"
        self.log_box.config(state="normal")
        self.log_box.insert("end", line, level)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")
        self.log_event("Log limpiado.", "warn")

    def set_status(self, text, color="black"):
        self.status_var.set(text)
        self.status_lbl.config(fg=color)

    # -------------------- Logica principal --------------------
    def update_countdown(self):
        if self.running.is_set():
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.next_send_var.set(self.format_mmss(self.remaining_seconds))
            else:
                self.next_send_var.set("--:--")

            if self.auto_quit_var.get() == 1:
                if self.quit_remaining_seconds > 0:
                    self.quit_remaining_seconds -= 1
                    self.autoquit_countdown_var.set(
                        self.format_minutes_from_seconds(self.quit_remaining_seconds)
                    )
                    if self.quit_remaining_seconds == 0:
                        try:
                            self.set_status("Enviando 'quit' y deteniendo…", "orange")
                            pyautogui.typewrite("quit")
                            pyautogui.press("enter")
                            self.log_event("Se envio 'quit' (autoquit).", "ok")
                        except Exception as e:
                            messagebox.showerror("Error", f"No se pudo enviar 'quit':\n{e}")
                            self.log_event(f"ERROR enviando 'quit': {e}", "error")
                            self.set_status("Error al enviar 'quit'.", "red")
                        finally:
                            self.stop()
                            if self.shutdown_var.get() == 1:
                                if messagebox.askyesno("Confirmar", "¿Seguro que queres apagar la PC?"):
                                    self.log_event("Apagando la computadora…", "warn")
                                    self.shutdown_pc()
                            return
                else:
                    self.autoquit_countdown_var.set("00 min")
            else:
                self.autoquit_countdown_var.set("-- min")

            self.root.after(1000, self.update_countdown)
        else:
            self.next_send_var.set("--:--")
            self.autoquit_countdown_var.set("-- min")

    def bot_loop(self, comando, intervalo_min):
        self.set_status("Iniciando en 5s… enfoca la ventana del juego!!!", "blue")
        self.log_event("Esperando 5s antes de iniciar (enfoca el juego).", "info")
        time.sleep(5)

        while self.running.is_set():
            try:
                if isinstance(comando, list):
                    cmd_to_send = random.choice(comando)
                else:
                    cmd_to_send = comando

                pyautogui.typewrite(cmd_to_send)
                pyautogui.press("enter")

                current = int(self.send_count_var.get())
                self.send_count_var.set(str(current + 1))

                if self.random_interval_var.get() == 1:
                    intervalo_seg = random.randint(1, 15) * 60
                    self.set_status(
                        f"Enviado: '{cmd_to_send}'. Proximo en {intervalo_seg // 60} min (aleatorio).",
                        "green"
                    )
                else:
                    try:
                        intervalo_seg = int(intervalo_min) * 60
                    except ValueError:
                        self.log_event("Intervalo invalido, deteniendo bot.", "error")
                        self.set_status("Intervalo invalido.", "red")
                        self.stop()
                        return
                    self.set_status(
                        f"Enviado: '{cmd_to_send}'. Proximo en {intervalo_min} min.",
                        "green"
                    )

                self.log_event(f"Enviado: '{cmd_to_send}'", "ok")

            except Exception as e:
                self.set_status("Error al enviar teclas.", "red")
                self.log_event(f"ERROR enviando teclas: {e}", "error")
                messagebox.showerror("Error", f"Hubo un problema enviando teclas:\n{e}")
                self.stop()
                return

            self.remaining_seconds = intervalo_seg
            for _ in range(intervalo_seg):
                if not self.running.is_set():
                    return
                time.sleep(1)

        self.set_status("Detenido.", "orange")
        self.log_event("Bot detenido.", "warn")

    def start(self):
        if self.running.is_set():
            return

        intervalo = self.interval_entry.get().strip()

        if self.multi_cmd_var.get() == 1:
            raw = self.multi_cmd_text.get("1.0", "end").strip()
            cmds = [c.strip() for c in raw.replace(",", "\n").splitlines() if c.strip()]
            if not cmds:
                messagebox.showwarning("Faltan comandos", "Agrega al menos un comando en la lista.")
                return
            comando = cmds
        else:
            comando = self.cmd_entry.get().strip()
            if not comando:
                messagebox.showwarning("Falta comando", "Por favor ingresa el comando a enviar.")
                return

        if self.random_interval_var.get() == 0:
            try:
                if int(intervalo) <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Intervalo invalido", "Ingresa un numero valido en minutos.")
                return

        if self.auto_quit_var.get() == 1:
            q_text = self.quit_minutes_entry.get().strip()
            try:
                if int(q_text) <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Tiempo invalido", "Ingresa un numero valido en minutos.")
                return
            self.quit_remaining_seconds = int(q_text) * 60
            self.autoquit_countdown_var.set(
                self.format_minutes_from_seconds(self.quit_remaining_seconds)
            )
        else:
            self.quit_remaining_seconds = 0
            self.autoquit_countdown_var.set("--")

        self.send_count_var.set("0")
        self.running.set()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        self.log_event("=" * 50, "special")
        self.log_event("Nuevo inicio del bot", "special")
        self.set_status("Preparando inicio…", "blue")

        self.remaining_seconds = 5
        self.next_send_var.set(self.format_mmss(self.remaining_seconds))
        self.update_countdown()

        self.worker_thread = threading.Thread(
            target=self.bot_loop, args=(comando, intervalo), daemon=True
        )
        self.worker_thread.start()

    def stop(self):
        self.running.clear()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.remaining_seconds = 0
        self.quit_remaining_seconds = 0
        self.next_send_var.set("--:--")
        self.autoquit_countdown_var.set("--")
        self.set_status("Detenido.", "orange")
        self.log_event("Bot detenido.", "warn")

    def shutdown_pc(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /s /t 0")
            else:
                os.system("shutdown -h now")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo apagar la PC:\n{e}")

    def on_close(self):
        if self.running.is_set():
            if not messagebox.askyesno("Salir", "El bot esta corriendo. ¿Seguro que queres salir?"):
                return
        self.running.clear()
        self.root.destroy()

    # -------------------- UI --------------------
    def build_ui(self):
        title_lbl = tk.Label(
            self.root, text="Granjero v2.0 by nachito ツ", font=("Segoe UI", 12, "bold")
        )
        title_lbl.pack(padx=20, pady=(16, 8))

        frame_inputs = tk.Frame(self.root)
        frame_inputs.pack(pady=8)

        tk.Label(frame_inputs, text="Comando:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cmd_entry = tk.Entry(frame_inputs, width=24)
        self.cmd_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_inputs, text="Minutos:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.interval_entry = tk.Entry(frame_inputs, width=10)
        self.interval_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        random_interval_check = tk.Checkbutton(
            frame_inputs,
            text="Usar intervalo aleatorio (1-15 min)",
            variable=self.random_interval_var,
            command=self.on_toggle_random_interval,
        )
        random_interval_check.grid(row=2, column=0, columnspan=2, pady=4)

        multi_frame = tk.Frame(self.root)
        multi_frame.pack(pady=(0, 8))
        multi_cmd_check = tk.Checkbutton(
            multi_frame,
            text="Modo aleatorio (varios comandos)",
            variable=self.multi_cmd_var,
            command=self.on_toggle_multi,
        )
        multi_cmd_check.grid(row=0, column=0, sticky="w", padx=5)

        self.multi_cmd_text = tk.Text(
            multi_frame, width=30, height=4, state="disabled", bg="#f0f0f0", fg="gray"
        )
        self.multi_cmd_text.insert("1.0", "heal\nattack\nsay hola")
        self.multi_cmd_text.grid(row=1, column=0, padx=5, pady=4)

        autoquit_frame = tk.Frame(self.root)
        autoquit_frame.pack(pady=(0, 8))
        autoquit_check = tk.Checkbutton(
            autoquit_frame, text="Auto-quit", variable=self.auto_quit_var, command=self.on_toggle_autoquit
        )
        autoquit_check.grid(row=0, column=0, padx=(5, 8))

        tk.Label(autoquit_frame, text="Minutos:").grid(row=0, column=1, padx=5)
        self.quit_minutes_entry = tk.Entry(autoquit_frame, width=6, state="disabled")
        self.quit_minutes_entry.insert(0, "60")
        self.quit_minutes_entry.grid(row=0, column=2, padx=5)

        self.shutdown_check = tk.Checkbutton(
            autoquit_frame, text="Apagar PC al Auto-quit", variable=self.shutdown_var, state="disabled"
        )
        self.shutdown_check.grid(row=0, column=3, padx=8)

        counter_frame = tk.Frame(self.root)
        counter_frame.pack(pady=(0, 4))
        tk.Label(counter_frame, text="Envios realizados:").grid(row=0, column=0, padx=5)
        tk.Label(counter_frame, textvariable=self.send_count_var).grid(row=0, column=1, padx=5)

        cd_frame = tk.Frame(self.root)
        cd_frame.pack(pady=(0, 2))
        tk.Label(cd_frame, text="Proximo envio en:").grid(row=0, column=0, padx=5)
        tk.Label(cd_frame, textvariable=self.next_send_var).grid(row=0, column=1, padx=5)

        cdq_frame = tk.Frame(self.root)
        cdq_frame.pack(pady=(0, 8))
        tk.Label(cdq_frame, text="Auto-quit en:").grid(row=0, column=0, padx=5)
        tk.Label(cdq_frame, textvariable=self.autoquit_countdown_var).grid(row=0, column=1, padx=5)

        buttons = tk.Frame(self.root)
        buttons.pack(pady=8)
        self.start_btn = tk.Button(buttons, text="Comenzar", width=12, command=self.start)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(buttons, text="Detener", width=12, state="disabled", command=self.stop)
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.clear_btn = tk.Button(buttons, text="Limpiar log", width=12, command=self.clear_log)
        self.clear_btn.grid(row=0, column=2, padx=6)

        # Estado centrado
        self.status_lbl = tk.Label(self.root, textvariable=self.status_var, font=("Segoe UI", 10, "bold"))
        self.status_lbl.pack(pady=(6, 4))

        # Log dinamico
        log_frame = tk.Frame(self.root)
        log_frame.pack(padx=16, pady=(4, 12), fill="both", expand=True)
        self.log_box = tk.Text(log_frame, state="disabled", bg="#f9f9f9", font=("Segoe UI", 9))
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

        # Estilos para el log
        self.log_box.tag_config("info", foreground="black")
        self.log_box.tag_config("ok", foreground="green")
        self.log_box.tag_config("warn", foreground="orange")
        self.log_box.tag_config("error", foreground="red", font=("Segoe UI", 9, "bold"))
        self.log_box.tag_config("special", foreground="blue", font=("Segoe UI", 9, "bold"))

    def on_toggle_autoquit(self):
        if self.auto_quit_var.get() == 1:
            self.quit_minutes_entry.config(state="normal")
            self.autoquit_countdown_var.set("--")
            self.shutdown_check.config(state="normal")
        else:
            self.quit_minutes_entry.config(state="disabled")
            self.autoquit_countdown_var.set("--")
            self.shutdown_check.config(state="disabled")
            self.shutdown_var.set(0)

    def on_toggle_multi(self):
        if self.multi_cmd_var.get() == 1:
            self.multi_cmd_text.config(state="normal", bg="white", fg="black")
            self.cmd_entry.config(state="disabled")
        else:
            self.multi_cmd_text.config(state="disabled", bg="#f0f0f0", fg="gray")
            self.cmd_entry.config(state="normal")

    def on_toggle_random_interval(self):
        if self.random_interval_var.get() == 1:
            self.interval_entry.config(state="disabled", bg="#f0f0f0", fg="gray")
        else:
            self.interval_entry.config(state="normal", bg="white", fg="black")


if __name__ == "__main__":
    root = tk.Tk()
    app = BotApp(root)
    root.mainloop()
