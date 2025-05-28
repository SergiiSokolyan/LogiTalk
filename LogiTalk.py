import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog 


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("800x600")
        self.title("Мій Чат")

        self.user_name = None 
        self.menu_expanded = False

       
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        
        self.message_display_box = ctk.CTkTextbox(self.chat_frame, wrap="word", state="disabled")
        self.message_display_box.pack(fill="both", expand=True, pady=(0, 10))

        
        self.message_input_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Введіть ваше повідомлення...")
        self.message_input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.message_input_entry.bind("<Return>", self.send_message) 

        
        self.send_button = ctk.CTkButton(self.chat_frame, text="Надіслати", command=self.send_message)
        self.send_button.pack(side="right")

        
        self.side_menu_width_contracted = 50 
        self.side_menu_width_expanded = 200

        self.side_menu = ctk.CTkFrame(self, width=self.side_menu_width_contracted, height=self.winfo_height(), fg_color="light blue")
        self.side_menu.pack(side="left", fill="y")
        self.side_menu.pack_propagate(False) 

        
        self.open_menu_button = ctk.CTkButton(self.side_menu, text="☰", width=30, command=self.toggle_menu)
        self.open_menu_button.pack(pady=10)

        
        self.menu_elements_frame = ctk.CTkFrame(self.side_menu, fg_color="light blue") # Прозорий фрейм для групування
        self.menu_elements_frame.pack(fill="both", expand=True)

        self.close_menu_button = ctk.CTkButton(self.menu_elements_frame, text="◀️", width=30, command=self.toggle_menu)
        self.name_label = ctk.CTkLabel(self.menu_elements_frame, text="Ім'я:")
        self.name_display = ctk.CTkLabel(self.menu_elements_frame, text="Не визначено", wraplength=150) # Для відображення імені
        self.change_name_button = ctk.CTkButton(self.menu_elements_frame, text="Змінити ім'я", command=self.ask_username)
        self.theme_option = ctk.CTkOptionMenu(self.menu_elements_frame, values=["Світла", "Темна"], command=self.change_theme)
        self.theme_option.set("Світла") 

        
        self.hide_menu_elements()

        
        self.after(100, self.ask_username) 

    def ask_username(self):
        """Запитує ім'я користувача за допомогою діалогового вікна."""
        self.user_name = simpledialog.askstring("Введіть ім'я", "Будь ласка, введіть ваше ім'я для чату:", parent=self)
        if self.user_name:
            self.name_display.configure(text=self.user_name)
            self.display_message(f"Привіт, {self.user_name}! Ласкаво просимо до чату.", "Системна")
        else:
            self.user_name = "Гість" 
            self.name_display.configure(text=self.user_name)
            self.display_message("Ім'я не введено. Ви увійшли як Гість.", "Системна")


    def display_message(self, message, sender="Ви"):
        """Виводить повідомлення у вікно чату."""
        self.message_display_box.configure(state="normal") 
        if sender == "Системна":
            self.message_display_box.insert("end", f"[СИСТЕМА]: {message}\n")
        elif sender == "Ви":
            self.message_display_box.insert("end", f"[{self.user_name if self.user_name else 'Ви'}]: {message}\n")
        else:
            self.message_display_box.insert("end", f"[{sender}]: {message}\n")
        self.message_display_box.configure(state="disabled") 
        self.message_display_box.see("end") 

    def send_message(self, event=None):
        """Надсилає повідомлення."""
        message = self.message_input_entry.get()
        if message:
            self.display_message(message, "Ви")
           
            print(f"Надсилаємо: {message}")
            self.message_input_entry.delete(0, "end") 
        else:
            self.display_message("Ви не можете надіслати пусте повідомлення.", "Системна")

    def toggle_menu(self):
        """Розгортає або згортає бокове меню."""
        if self.menu_expanded:
            self.contract_menu()
        else:
            self.expand_menu()

    def expand_menu(self):
        """Розгортає бокове меню."""
        self.menu_expanded = True
        self.open_menu_button.pack_forget() 

        for width in range(self.side_menu_width_contracted, self.side_menu_width_expanded + 1, 10):
            self.side_menu.configure(width=width)
            self.update()
            self.after(5) 

        
        self.close_menu_button.pack(pady=10)
        self.name_label.pack(pady=(20, 0))
        self.name_display.pack(pady=(0, 10))
        self.change_name_button.pack(pady=10)
        self.theme_option.pack(pady=10)


    def contract_menu(self):
        """Згортає бокове меню."""
        self.menu_expanded = False
        self.hide_menu_elements() 

        for width in range(self.side_menu_width_expanded, self.side_menu_width_contracted - 1, -10):
            self.side_menu.configure(width=width)
            self.update()
            self.after(5)

        self.open_menu_button.pack(pady=10) 

    def hide_menu_elements(self):
        """Приховує елементи всередині розгорнутого меню."""
        self.close_menu_button.pack_forget()
        self.name_label.pack_forget()
        self.name_display.pack_forget()
        self.change_name_button.pack_forget()
        self.theme_option.pack_forget()


    def change_theme(self, choice):
        """Змінює тему програми."""
        if choice == "Темна":
            ctk.set_appearance_mode("dark")
            self.side_menu.configure(fg_color="dodger blue") 
        else:
            ctk.set_appearance_mode("light")
            self.side_menu.configure(fg_color="light blue") 

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()