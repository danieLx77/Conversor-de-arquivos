import customtkinter as ctk
from tkinter import filedialog
import os
from core.converter import FileConverter

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Conversor Universal de Arquivos")
        self.geometry("600x480") 
        self.grid_columnconfigure(0, weight=1)

        # Componentes da Interface
        self.title_label = ctk.CTkLabel(self, text="Conversor de Arquivos", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Botão de Importar
        self.import_button = ctk.CTkButton(self, text="📁 Importar Arquivo", command=self.import_file)
        self.import_button.grid(row=1, column=0, padx=20, pady=10)

        # Label de status do arquivo
        self.file_label = ctk.CTkLabel(self, text="Nenhum arquivo selecionado", text_color="gray", wraplength=500)
        self.file_label.grid(row=2, column=0, padx=20, pady=5)

        self.format_label = ctk.CTkLabel(self, text="Converter para:")
        self.format_label.grid(row=3, column=0, padx=20, pady=(20, 0))

        # Menu de Opções 
        self.format_menu = ctk.CTkOptionMenu(self, values=[
            "PNG", "JPEG", "SVG", "PDF", 
            "JSON", "CSV", "Binário"
        ])
        self.format_menu.grid(row=4, column=0, padx=20, pady=10)

        # Botão de Converter
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
        # 1. Validação inicial
        if not self.current_file_path:
            self.file_label.configure(text="Erro: Selecione um arquivo primeiro!", text_color="red")
            return
            
        target_format = self.format_menu.get()
        extension = self.current_file_path.split('.')[-1].lower()

        sucesso = False
        resultado = "Formato não suportado."
        image_extensions = ['jpg', 'jpeg', 'png']

        # 2. Lógica de Roteamento de Conversão
        
        # --- TXT ---
        if extension == "txt" and target_format == "Binário":
            self.file_label.configure(text="Convertendo TXT para Binário...", text_color="yellow")
            sucesso, resultado = FileConverter.text_to_binary(self.current_file_path)

        # --- CSV ---
        elif extension == "csv" and target_format == "JSON":
            self.file_label.configure(text="Convertendo CSV para JSON...", text_color="yellow")
            sucesso, resultado = FileConverter.csv_to_json(self.current_file_path)

        # --- IMAGENS (PNG, JPG) ---
        elif extension in image_extensions and target_format == "PDF":
            self.file_label.configure(text="Gerando PDF da imagem...", text_color="yellow")
            sucesso, resultado = FileConverter.image_to_pdf(self.current_file_path)

        # --- PDF ---
        elif extension == "pdf":
            # PDF para Imagens Raster (PNG/JPEG)
            if target_format in ["PNG", "JPEG"]:
                format_lower = target_format.lower()
                self.file_label.configure(text=f"Convertendo PDF para {target_format}...", text_color="yellow")
                sucesso, resultado = FileConverter.pdf_to_images(self.current_file_path, output_format=format_lower)
            
            # PDF para SVG
            elif target_format == "SVG":
                self.file_label.configure(text="Convertendo PDF para SVG (Vetorial)...", text_color="yellow")
                sucesso, resultado = FileConverter.pdf_to_svg(self.current_file_path)
            
            else:
                self.file_label.configure(text=f"Erro: Não convertemos PDF para {target_format}", text_color="orange")
                return

        # --- Caso não encontre combinação válida ---
        else:
            self.file_label.configure(text=f"Erro: A combinação .{extension} -> {target_format} não é válida.", text_color="orange")
            return

        # 3. Exibição do Resultado Final
        if sucesso:
            self.file_label.configure(text=f"✅ Sucesso!\n{resultado}", text_color="green")
        else:
            self.file_label.configure(text=f"❌ Erro: {resultado}", text_color="red")