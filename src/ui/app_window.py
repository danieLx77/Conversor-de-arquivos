import customtkinter as ctk
from tkinter import filedialog
import os
from core.converter import FileConverter

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        
        self.title("Conversor Universal de Arquivos")
        self.geometry("600x400")
        
        
        self.grid_columnconfigure(0, weight=1)

        
        self.title_label = ctk.CTkLabel(self, text="Conversor de Arquivos", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        
        self.import_button = ctk.CTkButton(self, text="📁 Importar Arquivo", command=self.import_file)
        self.import_button.grid(row=1, column=0, padx=20, pady=10)

        
        self.file_label = ctk.CTkLabel(self, text="Nenhum arquivo selecionado", text_color="gray", wraplength = 500)
        self.file_label.grid(row=2, column=0, padx=20, pady=5)

        self.format_label = ctk.CTkLabel(self, text="Converter para:")
        self.format_label.grid(row=3, column=0, padx=20, pady=(20, 0))

        self.format_menu = ctk.CTkOptionMenu(self, values=["PDF", "CSV", "JSON", "TXT", "Binário"])
        self.format_menu.grid(row=4, column=0, padx=20, pady=10)

        self.convert_button = ctk.CTkButton(self, text="Converter Agora", fg_color="green", hover_color="#006400", command=self.start_conversion)
        self.convert_button.grid(row=5, column=0, padx=20, pady=20)

        self.current_file_path = None

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Selecione um arquivo")
        
        if file_path:
            self.current_file_path = file_path
            file_name = os.path.basename(file_path)
            self.file_label.configure(text=f"Arquivo atual: {file_name}", text_color="white")

    def start_conversion(self):
        if not self.current_file_path:
            self.file_label.configure(text="Erro: Selecione um arquivo primeiro!", text_color="red")
            return
            
        target_format = self.format_menu.get()
        extension = self.current_file_path.split('.')[-1].lower()

        sucesso = False
        resultado = "Formato não suportado ainda."

        if target_format == "Binário" and extension == "txt":
            self.file_label.configure(text="Convertendo TXT para Binário...", text_color="yellow")
            sucesso, resultado = FileConverter.text_to_binary(self.current_file_path)

        elif target_format == "JSON" and extension == "csv":
            self.file_label.configure(text="Convertendo CSV para JSON...", text_color="yellow")
            sucesso, resultado = FileConverter.csv_to_json(self.current_file_path)
            
        else:
            self.file_label.configure(text=f"Erro: Não convertemos .{extension} para {target_format}", text_color="orange")
            return

        if sucesso:
            self.file_label.configure(text=f"✅ Sucesso! Salvo em: {resultado}", text_color="green")
        else:
            self.file_label.configure(text=f"❌ Erro: {resultado}", text_color="red")