import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog, messagebox, END
import socket
import threading
import sys

# --- Налаштування CustomTkinter ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("800x600")
        self.title("Мій Чат")

        self.user_name = None
        self.menu_expanded = False

        # --- Налаштування мережі ---
        self.sock = None
        self.connected_to_server = False
        # ВАЖЛИВО: Оновіть ці дані на актуальні від Ngrok!
        self.HOST = '5.tcp.eu.ngrok.io'
        self.PORT = 14617

        self._create_widgets() # Викликаємо метод для створення всіх UI елементів
        self._initial_setup()  # Викликаємо метод для початкових налаштувань

    def _create_widgets(self):
        """Створює всі елементи графічного інтерфейсу."""
        # --- Фрейм для чату ---
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.message_display_box = ctk.CTkTextbox(self.chat_frame, wrap="word", state="disabled")
        self.message_display_box.pack(fill="both", expand=True, pady=(0, 10))

        self.message_input_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Введіть ваше повідомлення...")
        self.message_input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.message_input_entry.bind("<Return>", self._send_message_to_server)

        self.send_button = ctk.CTkButton(self.chat_frame, text="Надіслати", command=self._send_message_to_server)
        self.send_button.pack(side="right")

        # --- Бокове меню ---
        self.side_menu_width_contracted = 50
        self.side_menu_width_expanded = 200

        self.side_menu = ctk.CTkFrame(self, width=self.side_menu_width_contracted, height=self.winfo_height(), fg_color="light blue")
        self.side_menu.pack(side="left", fill="y")
        self.side_menu.pack_propagate(False)

        self.open_menu_button = ctk.CTkButton(self.side_menu, text="☰", width=30, command=self._toggle_menu)
        self.open_menu_button.pack(pady=10)

        # Фрейм для елементів меню (дозволяє приховувати/відображати їх разом)
        self.menu_elements_frame = ctk.CTkFrame(self.side_menu, fg_color="light blue")
        self.menu_elements_frame.pack(fill="both", expand=True)

        # Елементи розгорнутого меню
        self.close_menu_button = ctk.CTkButton(self.menu_elements_frame, text="◀️", width=30, command=self._toggle_menu)
        self.name_label = ctk.CTkLabel(self.menu_elements_frame, text="Ім'я:")
        self.name_display = ctk.CTkLabel(self.menu_elements_frame, text="Не визначено", wraplength=150)
        self.change_name_button = ctk.CTkButton(self.menu_elements_frame, text="Змінити ім'я", command=self._ask_username)
        self.theme_option = ctk.CTkOptionMenu(self.menu_elements_frame, values=["Світла", "Темна"], command=self._change_theme)
        self.theme_option.set("Світла")

        self.connect_button = ctk.CTkButton(self.menu_elements_frame, text="Підключитися", command=self._connect_to_server)
        self.disconnect_button = ctk.CTkButton(self.menu_elements_frame, text="Відключитися", command=self._disconnect_from_server, state="disabled")

    def _initial_setup(self):
        """Виконує початкові налаштування після створення UI."""
        self._hide_menu_elements()
        self.message_input_entry.configure(state="disabled") # Заборонити введення, доки не підключено
        self.after(100, self._ask_username)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Обробляє закриття вікна, відключаючись від сервера."""
        if self.connected_to_server:
            self._disconnect_from_server()
        self.destroy()
        sys.exit(0)

    def _ask_username(self):
        """Запитує ім'я користувача."""
        current_name = self.user_name if self.user_name else ""
        self.user_name = simpledialog.askstring("Введіть ім'я", "Будь ласка, введіть ваше ім'я для чату:", initialvalue=current_name, parent=self)
        if self.user_name:
            self.name_display.configure(text=self.user_name)
            if not self.connected_to_server:
                self._display_message(f"Привіт, {self.user_name}! Ласкаво просимо до чату.", "Системна")
            elif self.connected_to_server:
                # Якщо вже підключені, можна повідомити сервер про зміну імені
                try:
                    self.sock.sendall(f"NAME@{self.user_name}\n".encode())
                except Exception as e:
                    self._display_message(f"Помилка при оновленні імені на сервері: {e}", "Системна")
        else:
            if not self.user_name:
                self.user_name = "Гість"
                self._display_message("Ім'я не введено. Ви увійшли як Гість.", "Системна")
            self.name_display.configure(text=self.user_name)

    def _display_message(self, message, sender="Ви"):
        """Виводить повідомлення у вікно чату."""
        self.message_display_box.configure(state="normal")
        if sender == "Системна":
            self.message_display_box.insert("end", f"[СИСТЕМА]: {message}\n", "system_message")
            self.message_display_box.tag_config("system_message", foreground="blue")
        elif sender == "Ви":
            self.message_display_box.insert("end", f"[{self.user_name if self.user_name else 'Ви'}]: {message}\n", "my_message")
            self.message_display_box.tag_config("my_message", foreground="darkgreen")
        else:
            self.message_display_box.insert("end", f"[{sender}]: {message}\n", "other_message")
            self.message_display_box.tag_config("other_message", foreground="black")
        self.message_display_box.configure(state="disabled")
        self.message_display_box.see("end")

    # --- Мережеві функції ---

    def _connect_to_server(self):
        """Підключається до сервера Ngrok."""
        if self.connected_to_server:
            self._display_message("Ви вже підключені до сервера.", "Системна")
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.HOST, self.PORT))
            self.connected_to_server = True
            self._display_message(f"Успішно підключено до сервера Ngrok: {self.HOST}:{self.PORT}", "Системна")

            self._update_connection_ui_state(True) # Оновлюємо UI після підключення

            # Надсилаємо серверу команду "CONNECT" з іменем користувача
            if self.user_name:
                self.sock.sendall(f"CONNECT@{self.user_name}\n".encode())

            # Запускаємо окремий потік для прийому повідомлень
            receive_thread = threading.Thread(target=self._recv_message_from_server)
            receive_thread.daemon = True
            receive_thread.start()

        except ConnectionRefusedError:
            self._display_message(f"Не вдалося підключитися. Сервер на {self.HOST}:{self.PORT} не відповідає.", "Системна")
            self.sock = None
        except socket.gaierror:
            self._display_message(f"Невірний адрес сервера '{self.HOST}'. Перевірте IP/домен.", "Системна")
            self.sock = None
        except Exception as e:
            self._display_message(f"Виникла помилка підключення: {e}", "Системна")
            self.sock = None

    def _disconnect_from_server(self):
        """Відключається від сервера."""
        if not self.connected_to_server:
            self._display_message("Ви не підключені до сервера.", "Системна")
            return

        try:
            if self.sock:
                # Надіслати серверу команду "DISCONNECT"
                if self.user_name:
                    self.sock.sendall(f"DISCONNECT@{self.user_name}\n".encode())
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            self.connected_to_server = False
            self._display_message("Відключено від сервера.", "Системна")
        except Exception as e:
            self._display_message(f"Помилка при відключенні: {e}", "Системна")
        finally:
            self.sock = None
            self._update_connection_ui_state(False) # Оновлюємо UI після відключення

    def _send_message_to_server(self, event=None):
        """Надсилає повідомлення на сервер у форматі 'TEXT@username@message'."""
        message = self.message_input_entry.get()
        if not message:
            self._display_message("Ви не можете надіслати пусте повідомлення.", "Системна")
            return

        if not self.connected_to_server or not self.sock:
            self._display_message("Ви не підключені до сервера.", "Системна")
            self.message_input_entry.delete(0, END)
            return

        data_to_send = f"TEXT@{self.user_name if self.user_name else 'Гість'}@{message}\n"
        try:
            self.sock.sendall(data_to_send.encode('utf-8'))
            self._display_message(message, "Ви") # Відображаємо своє повідомлення
        except Exception as e:
            self._display_message(f"Помилка при надсиланні повідомлення: {e}", "Системна")
            self._disconnect_from_server()
        self.message_input_entry.delete(0, END)

    def _recv_message_from_server(self):
        """Приймає повідомлення від сервера та обробляє їх."""
        buffer = ""
        while self.connected_to_server and self.sock:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    self.after(0, self._display_message, "Сервер відключився або розірвав з'єднання.", "Системна")
                    self.after(0, self._disconnect_from_server)
                    break
                buffer += chunk.decode('utf-8')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.after(0, self._handle_server_line, line.strip())
            except ConnectionResetError:
                self.after(0, self._display_message, "З'єднання з сервером було скинуто.", "Системна")
                self.after(0, self._disconnect_from_server)
                break
            except OSError as e:
                if self.connected_to_server:
                    self.after(0, self._display_message, f"Помилка сокета при прийомі: {e}", "Системна")
                break
            except Exception as e:
                self.after(0, self._display_message, f"Невідома помилка при прийомі: {e}", "Системна")
                self.after(0, self._disconnect_from_server)
                break
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                print(f"Помилка при закритті сокета в _recv_message_from_server: {e}")

    def _handle_server_line(self, line):
        """Обробляє одну лінію повідомлення, отриману від сервера."""
        if not line:
            return

        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                self._display_message(message, author)
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                self._display_message(f"Отримано зображення від {author}: {filename}", "Системна")
        elif msg_type == "SERVER":
            if len(parts) >= 2:
                server_message = parts[1]
                self._display_message(server_message, "Сервер")
        else:
            self._display_message(line, "Невідомо")

    # --- Функції GUI (бічне меню) ---

    def _toggle_menu(self):
        """Розгортає або згортає бокове меню."""
        if self.menu_expanded:
            self._contract_menu()
        else:
            self._expand_menu()

    def _expand_menu(self):
        """Розгортає бокове меню."""
        self.menu_expanded = True
        self.open_menu_button.pack_forget()

        # Анімація розгортання
        for width in range(self.side_menu_width_contracted, self.side_menu_width_expanded + 1, 10):
            self.side_menu.configure(width=width)
            self.update_idletasks() # Оновлюємо UI негайно
            # self.after(5) # Занадто багато викликів, робить анімацію повільною на деяких системах
        self.side_menu.configure(width=self.side_menu_width_expanded) # Забезпечуємо кінцевий розмір

        self._pack_menu_elements() # Відображаємо елементи меню
        self.after(10, self.update_idletasks) # Маленька затримка для плавного відображення

    def _contract_menu(self):
        """Згортає бокове меню."""
        self.menu_expanded = False
        self._hide_menu_elements()

        # Анімація згортання
        for width in range(self.side_menu_width_expanded, self.side_menu_width_contracted - 1, -10):
            self.side_menu.configure(width=width)
            self.update_idletasks() # Оновлюємо UI негайно
            # self.after(5) # Аналогічно
        self.side_menu.configure(width=self.side_menu_width_contracted) # Забезпечуємо кінцевий розмір

        self.open_menu_button.pack(pady=10)
        self.after(10, self.update_idletasks) # Маленька затримка для плавного відображення

    def _pack_menu_elements(self):
        """Упаковує (робить видимими) елементи всередині розгорнутого меню."""
        self.close_menu_button.pack(pady=10)
        self.name_label.pack(pady=(20, 0))
        self.name_display.pack(pady=(0, 10))
        self.change_name_button.pack(pady=10)
        self.theme_option.pack(pady=10)
        self.connect_button.pack(pady=10)
        self.disconnect_button.pack(pady=10)

    def _hide_menu_elements(self):
        """Приховує елементи всередині розгорнутого меню."""
        self.close_menu_button.pack_forget()
        self.name_label.pack_forget()
        self.name_display.pack_forget()
        self.change_name_button.pack_forget()
        self.theme_option.pack_forget()
        self.connect_button.pack_forget()
        self.disconnect_button.pack_forget()

    def _change_theme(self, choice):
        """Змінює тему програми."""
        if choice == "Темна":
            ctk.set_appearance_mode("dark")
            self.side_menu.configure(fg_color="dodger blue")
            self.menu_elements_frame.configure(fg_color="dodger blue")
        else:
            ctk.set_appearance_mode("light")
            self.side_menu.configure(fg_color="light blue")
            self.menu_elements_frame.configure(fg_color="light blue") # Важливо змінити колір і для фрейму елементів

    def _update_connection_ui_state(self, is_connected):
        """Оновлює стан кнопок підключення/відключення та поля введення."""
        self.connect_button.configure(state="disabled" if is_connected else "normal")
        self.disconnect_button.configure(state="normal" if is_connected else "disabled")
        self.message_input_entry.configure(state="normal" if is_connected else "disabled")


if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()