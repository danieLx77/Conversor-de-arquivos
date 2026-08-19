import contextlib
import io
import os
import platform
import re
import shutil
import subprocess
import threading

import customtkinter as ctk
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

from core.converter import (
    FileConverter,
    FORMATS,
    SUPPORTED_CONVERSIONS,
    SUPPORTED_EXTENSIONS,
    LABEL_TO_CODE,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

IMAGE_EXTS = ["jpg", "jpeg", "png", "webp"]

FORMAT_DESCRIPTIONS = {
    "binary": "Converte o conteúdo do texto em representação binária (UTF-8).",
    "json": "Converte os dados do CSV em um arquivo JSON estruturado.",
    "pdf": "Gera um arquivo PDF a partir da imagem.",
    "svg": "Vetoriza a imagem em SVG com curvas suaves e cores preservadas.",
    "png": "Converte cada página do PDF em imagens PNG em alta resolução (300 DPI).",
    "jpeg": "Converte cada página do PDF em imagens JPEG em alta resolução (300 DPI).",
    "markdown": "Extrai o texto do PDF para um arquivo Markdown.",
    "ocr": "Extrai o texto da imagem via API de reconhecimento óptico de caracteres.",
    "extract_images": "Extrai todas as imagens embutidas no PDF.",
}

SUCCESS_COLOR = "#2ecc71"
ERROR_COLOR = "#ff6b6b"
WARNING_COLOR = "#f1c40f"


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Conversor Universal de Arquivos")
        self.geometry("680x640")
        self.minsize(620, 580)
        self.grid_columnconfigure(0, weight=1)

        self.current_file_path = None
        self.last_output_path = None
        self._conversion_active = False

        self._build_header()
        self._build_file_card()
        self._build_target_card()
        self._build_status_card()
        self._build_actions()
        self._configure_dnd()

    # --- CONSTRUÇÃO DA INTERFACE ---

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 6))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_box, text="Conversor de Arquivos", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Transforme arquivos entre formatos em segundos",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(anchor="w")

        self.theme_switch = ctk.CTkSwitch(header, text="Modo escuro", command=self._toggle_theme)
        self.theme_switch.grid(row=0, column=1, sticky="e")
        self.theme_switch.select()

    def _card(self, row, title):
        frame = ctk.CTkFrame(self, corner_radius=14)
        frame.grid(row=row, column=0, sticky="ew", padx=28, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray",
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
        return frame

    def _build_file_card(self):
        frame = self._card(1, "Arquivo de entrada")

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=18, pady=(4, 4))
        content.grid_columnconfigure(1, weight=1)

        self.import_button = ctk.CTkButton(content, text="Importar arquivo", width=150, command=self.import_file)
        self.import_button.grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.file_label = ctk.CTkLabel(
            content,
            text="Nenhum arquivo selecionado",
            text_color="gray",
            wraplength=420,
            justify="left",
        )
        self.file_label.grid(row=0, column=1, sticky="w")

        self.drop_label = ctk.CTkLabel(
            frame,
            text="ou arraste e solte um arquivo aqui",
            text_color="gray",
            corner_radius=10,
            fg_color=("gray90", "gray20"),
            height=44,
        )
        self.drop_label.grid(row=2, column=0, sticky="ew", padx=18, pady=(10, 16))

    def _build_target_card(self):
        frame = self._card(2, "Formato de destino")

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=18, pady=(4, 16))
        content.grid_columnconfigure(0, weight=1)

        self.format_menu = ctk.CTkOptionMenu(
            content,
            values=["Selecione um arquivo"],
            width=340,
            command=self._on_format_change,
        )
        self.format_menu.grid(row=0, column=0, sticky="w")

        self.format_hint = ctk.CTkLabel(
            content,
            text="Importe um arquivo para ver os formatos disponíveis.",
            text_color="gray",
            wraplength=560,
            justify="left",
        )
        self.format_hint.grid(row=1, column=0, sticky="w", pady=(10, 0))

    def _build_status_card(self):
        frame = self._card(3, "Status")

        self.status_label = ctk.CTkLabel(frame, text="Aguardando arquivo...", text_color="gray")
        self.status_label.grid(row=1, column=0, sticky="w", padx=18, pady=(4, 10))

        self.progress_bar = ctk.CTkProgressBar(frame, mode="indeterminate")
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))
        self.progress_bar.set(0)

    def _build_actions(self):
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=28, pady=(4, 20))
        actions.grid_columnconfigure(0, weight=1)

        self.convert_button = ctk.CTkButton(
            actions,
            text="Converter Agora",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_conversion,
        )
        self.convert_button.grid(row=0, column=0, sticky="ew")

        self.open_button = ctk.CTkButton(
            actions,
            text="Abrir pasta de destino",
            height=40,
            fg_color="transparent",
            border_width=1,
            state="disabled",
            command=self._open_output_folder,
        )
        self.open_button.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    def _configure_dnd(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

    # --- UTILITÁRIOS ---

    @staticmethod
    def _file_extension(path):
        return os.path.splitext(path)[1].lstrip(".").lower()

    @staticmethod
    def _supported_targets(ext):
        if ext not in SUPPORTED_CONVERSIONS:
            return []
        return [FORMATS[code] for code in SUPPORTED_CONVERSIONS[ext]]

    @staticmethod
    def _human_size(num_bytes):
        for unit in ("B", "KB", "MB", "GB"):
            if num_bytes < 1024 or unit == "GB":
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024
        return f"{num_bytes:.1f} GB"

    @staticmethod
    def _clean_dropped_path(data):
        matches = re.findall(r"\{[^}]*\}|[^\s{}]+", data or "")
        for match in matches:
            path = match.strip("{}")
            if os.path.isfile(path):
                return path
        return None

    # --- FLUXO DA INTERFACE ---

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Selecione um arquivo")
        if file_path:
            self._load_file(file_path)

    def _on_drop(self, event):
        path = self._clean_dropped_path(event.data)
        if path:
            self._load_file(path)

    def _load_file(self, file_path):
        ext = self._file_extension(file_path)

        if ext not in SUPPORTED_EXTENSIONS:
            self.current_file_path = None
            self.last_output_path = None
            self.open_button.configure(state="disabled")
            self.format_menu.configure(values=["Selecione um arquivo"], require_redraw=True)
            self.format_menu.set("Selecione um arquivo")
            self.format_hint.configure(text=f"Formato .{ext} não suportado.", text_color=ERROR_COLOR)
            self.file_label.configure(text=f"Formato .{ext} não suportado.", text_color=ERROR_COLOR)
            self.status_label.configure(text="Arquivo inválido.", text_color=ERROR_COLOR)
            return

        self.current_file_path = file_path
        self.last_output_path = None
        self.open_button.configure(state="disabled")

        targets = self._supported_targets(ext)
        self.format_menu.configure(values=targets, require_redraw=True)
        self.format_menu.set(targets[0])
        self._on_format_change(targets[0])

        name = os.path.basename(file_path)
        size = self._human_size(os.path.getsize(file_path))
        self.file_label.configure(text=f"{name}  •  {size}", text_color="white")
        self.status_label.configure(text="Arquivo selecionado. Escolha o formato e converta.", text_color="white")

    def _on_format_change(self, label):
        code = LABEL_TO_CODE.get(label)
        if code:
            self.format_hint.configure(text=FORMAT_DESCRIPTIONS.get(code, ""), text_color="gray")

    def _toggle_theme(self):
        mode = "dark" if self.theme_switch.get() == 1 else "light"
        ctk.set_appearance_mode(mode)

    def start_conversion(self):
        if not self.current_file_path:
            self.status_label.configure(text="Erro: Selecione um arquivo!", text_color=ERROR_COLOR)
            return
        if self._conversion_active:
            return

        ext = self._file_extension(self.current_file_path)
        target_label = self.format_menu.get()
        target_code = LABEL_TO_CODE.get(target_label)
        if target_code is None:
            self.status_label.configure(text="Selecione um formato de destino.", text_color=WARNING_COLOR)
            return

        self._conversion_active = True
        self.convert_button.configure(state="disabled")
        self.import_button.configure(state="disabled")
        self.format_menu.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.status_label.configure(text="Convertendo...", text_color=WARNING_COLOR)
        self.progress_bar.start()

        thread = threading.Thread(
            target=self._run_conversion,
            args=(ext, target_code, self.current_file_path),
            daemon=True,
        )
        thread.start()

    def _run_conversion(self, ext, target_code, file_path):
        sucesso, resultado, output_path = self._dispatch(ext, target_code, file_path)
        self.after(0, self._finish_conversion, sucesso, resultado, output_path)

    def _finish_conversion(self, sucesso, resultado, output_path):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self._conversion_active = False
        self.convert_button.configure(state="normal")
        self.import_button.configure(state="normal")
        self.format_menu.configure(state="normal")
        self.last_output_path = output_path

        if sucesso:
            self.status_label.configure(text=f"Sucesso: {resultado}", text_color=SUCCESS_COLOR)
            if output_path:
                self.open_button.configure(state="normal")
        else:
            self.status_label.configure(text=f"Falha: {resultado}", text_color=ERROR_COLOR)

    @staticmethod
    def _is_wsl():
        try:
            with open("/proc/version") as f:
                if "microsoft" in f.read().lower():
                    return True
        except OSError:
            pass
        return shutil.which("wslview") is not None

    def _launch_file_manager(self, folder):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                system = platform.system()
                if system == "Windows":
                    os.startfile(folder)
                    return True
                if system == "Darwin":
                    return subprocess.run(["open", folder], capture_output=True).returncode == 0
                opener = "wslview" if self._is_wsl() else "xdg-open"
                return subprocess.run([opener, folder], capture_output=True).returncode == 0
        except Exception:
            return False

    def _open_output_folder(self):
        path = self.last_output_path
        if not path:
            return
        folder = path if os.path.isdir(path) else os.path.dirname(path)

        self.clipboard_clear()
        self.clipboard_append(folder)

        if self._launch_file_manager(folder):
            self.status_label.configure(text="Pasta aberta no gerenciador de arquivos.", text_color=SUCCESS_COLOR)
        else:
            self.status_label.configure(
                text="Não foi possível abrir a pasta. O caminho foi copiado para a área de transferência.",
                text_color=WARNING_COLOR,
            )

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

        return False, f"Ação {FORMATS[target_code]} não disponível para .{ext}.", None