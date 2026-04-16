import customtkinter as ctk
from tkinter import filedialog
import os
from core.converter import FileConverter

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Conversor Universal de Arquivos")
        self.geometry("600x500")
        self.grid_columnconfigure(0, weight=1)

        # UI - Título
        ctk.CTkLabel(self, text="Conversor de Arquivos", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        
        # Botão de Importar
        self.import_button = ctk.CTkButton(self, text="📁 Importar Arquivo", command=self.import_file)
        self.import_button.grid(row=1, column=0, pady=10)

        # Label de status do arquivo
        self.file_label = ctk.CTkLabel(self, text="Nenhum arquivo selecionado", text_color="gray", wraplength=500)
        self.file_label.grid(row=2, column=0, pady=5)

        ctk.CTkLabel(self, text="Converter para:").grid(row=3, column=0, pady=(15, 0))

        # Menu de Opções
        self.format_menu = ctk.CTkOptionMenu(self, values=[
            "PNG", "JPEG", "SVG", "Markdown (.md)", "OCR na Nuvem (API)", 
            "Extrair Imagens", "PDF", "JSON", "CSV", "Binário"
        ])
        self.format_menu.grid(row=4, column=0, pady=10)

        # Botão de Converter
        self.convert_button = ctk.CTkButton(self, text="Converter Agora", fg_color="green", hover_color="#006400", command=self.start_conversion)
        self.convert_button.grid(row=5, column=0, pady=20)

        self.current_file_path = None

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Selecione um arquivo")
        if file_path:
            self.current_file_path = file_path
            self.file_label.configure(text=f"Arquivo: {os.path.basename(file_path)}", text_color="white")

    def start_conversion(self):
        if not self.current_file_path:
            self.file_label.configure(text="Erro: Selecione um arquivo!", text_color="red")
            return
            
        target = self.format_menu.get()
        ext = self.current_file_path.split('.')[-1].lower()
        sucesso, resultado = False, "Formato não suportado."

        # --- Lógica para Arquivos de Texto ---
        if ext == "txt" and target == "Binário":
            sucesso, resultado = FileConverter.text_to_binary(self.current_file_path)
        
        # --- Lógica para Dados ---
        elif ext == "csv" and target == "JSON":
            sucesso, resultado = FileConverter.csv_to_json(self.current_file_path)

        # --- Lógica para IMAGENS (PNG, JPG, WEBP) ---
        elif ext in ['jpg', 'jpeg', 'png', 'webp']:
            if target == "PDF":
                self.file_label.configure(text="Gerando PDF...", text_color="yellow")
                sucesso, resultado = FileConverter.image_to_pdf(self.current_file_path)
            
            elif target == "SVG":
                self.file_label.configure(text="Vetorizando imagem (vtracer)...", text_color="yellow")
                sucesso, resultado = FileConverter.image_to_svg(self.current_file_path)
            
            elif target == "OCR na Nuvem (API)":
                self.file_label.configure(text="Executando OCR na imagem...", text_color="yellow")
                sucesso, resultado = FileConverter.ocr_via_api(self.current_file_path)
            
            else:
                self.file_label.configure(text=f"Ação {target} não disponível para imagem.", text_color="orange")
                return

        # --- Lógica para PDF ---
        elif ext == "pdf":
            if target in ["PNG", "JPEG"]:
                sucesso, resultado = FileConverter.pdf_to_images(self.current_file_path, target.lower())
            
            elif target == "SVG":
                self.file_label.configure(text="Extraindo SVG do PDF...", text_color="yellow")
                sucesso, resultado = FileConverter.pdf_to_svg(self.current_file_path)
            
            elif target == "Extrair Imagens":
                sucesso, resultado = FileConverter.extract_images_from_pdf(self.current_file_path)
            
            elif target == "Markdown (.md)":
                sucesso, resultado = FileConverter.pdf_to_markdown(self.current_file_path)
            
            elif target == "OCR na Nuvem (API)":
                sucesso, resultado = FileConverter.ocr_via_api(self.current_file_path)
            
            else:
                self.file_label.configure(text=f"Ação {target} não disponível para PDF.", text_color="orange")
                return

        # Exibição do Resultado Final
        if sucesso:
            self.file_label.configure(text=f"✅ {resultado}", text_color="green")
        else:
            self.file_label.configure(text=f"❌ {resultado}", text_color="red")