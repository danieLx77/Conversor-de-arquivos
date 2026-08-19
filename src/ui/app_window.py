import customtkinter as ctk
from tkinter import filedialog
import os
from core.converter import (
    FileConverter,
    FORMATS,
    SUPPORTED_CONVERSIONS,
    SUPPORTED_EXTENSIONS,
    LABEL_TO_CODE,
)

IMAGE_EXTS = ["jpg", "jpeg", "png", "webp"]


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

        # Menu de Opções (preenchido conforme o arquivo importado)
        self.format_menu = ctk.CTkOptionMenu(self, values=["Selecione um arquivo"])
        self.format_menu.grid(row=4, column=0, pady=10)

        # Botão de Converter
        self.convert_button = ctk.CTkButton(self, text="Converter Agora", fg_color="green", hover_color="#006400", command=self.start_conversion)
        self.convert_button.grid(row=5, column=0, pady=20)

        self.current_file_path = None

    @staticmethod
    def _file_extension(path):
        return os.path.splitext(path)[1].lstrip(".").lower()

    @staticmethod
    def _supported_targets(ext):
        if ext not in SUPPORTED_CONVERSIONS:
            return []
        return [FORMATS[code] for code in SUPPORTED_CONVERSIONS[ext]]

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Selecione um arquivo")
        if not file_path:
            return

        ext = self._file_extension(file_path)
        if ext not in SUPPORTED_EXTENSIONS:
            self.current_file_path = None
            self.format_menu.configure(values=["Selecione um arquivo"], require_redraw=True)
            self.format_menu.set("Selecione um arquivo")
            self.file_label.configure(text=f"Formato .{ext} não suportado.", text_color="red")
            return

        self.current_file_path = file_path
        targets = self._supported_targets(ext)
        self.format_menu.configure(values=targets, require_redraw=True)
        self.format_menu.set(targets[0])
        self.file_label.configure(text=f"Arquivo: {os.path.basename(file_path)}", text_color="white")

    def start_conversion(self):
        if not self.current_file_path:
            self.file_label.configure(text="Erro: Selecione um arquivo!", text_color="red")
            return

        ext = self._file_extension(self.current_file_path)
        target_label = self.format_menu.get()
        target_code = LABEL_TO_CODE.get(target_label)
        if target_code is None:
            self.file_label.configure(text="Selecione um formato de destino.", text_color="orange")
            return

        sucesso, resultado = self._dispatch(ext, target_code, self.current_file_path)

        if sucesso:
            self.file_label.configure(text=f"✅ {resultado}", text_color="green")
        else:
            self.file_label.configure(text=f"❌ {resultado}", text_color="red")

    def _dispatch(self, ext, target_code, file_path):
        # --- Lógica para Arquivos de Texto ---
        if ext == "txt" and target_code == "binary":
            return FileConverter.text_to_binary(file_path)

        # --- Lógica para Dados ---
        if ext == "csv" and target_code == "json":
            return FileConverter.csv_to_json(file_path)

        # --- Lógica para IMAGENS (PNG, JPG, WEBP) ---
        if ext in IMAGE_EXTS:
            if target_code == "pdf":
                return FileConverter.image_to_pdf(file_path)
            if target_code == "svg":
                return FileConverter.image_to_svg(file_path)
            if target_code == "ocr":
                return FileConverter.ocr_via_api(file_path)

        # --- Lógica para PDF ---
        if ext == "pdf":
            if target_code in ("png", "jpeg"):
                return FileConverter.pdf_to_images(file_path, target_code)
            if target_code == "svg":
                return FileConverter.pdf_to_svg(file_path)
            if target_code == "extract_images":
                return FileConverter.extract_images_from_pdf(file_path)
            if target_code == "markdown":
                return FileConverter.pdf_to_markdown(file_path)
            if target_code == "ocr":
                return FileConverter.ocr_via_api(file_path)

        return False, f"Ação {FORMATS[target_code]} não disponível para .{ext}."