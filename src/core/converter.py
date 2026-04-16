import os
import csv
import json
import img2pdf
import fitz  
import requests
import vtracer
from dotenv import load_dotenv

load_dotenv()

class FileConverter:

    # --- CONFIGURAÇÃO DE API (OCR.SPACE) ---
    OCR_API_KEY = os.getenv("OCR_SPACE_KEY", "helloworld")
    OCR_URL = "https://api.ocr.space/parse/image"

    # --- TXT PARA BINÁRIO ---
    @staticmethod
    def text_to_binary(input_path):
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_path = os.path.join(folder, f"{base_name}_convertido.bin")

            with open(input_path, 'r', encoding='utf-8') as file:
                text_content = file.read()

            binary_content = ' '.join(format(ord(char), '08b') for char in text_content)

            with open(output_path, 'w', encoding='utf-8') as bin_file:
                bin_file.write(binary_content)

            return True, output_path 
        except Exception as e:
            return False, str(e) 

    # --- CSV PARA JSON ---
    @staticmethod
    def csv_to_json(input_path):
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_path = os.path.join(folder, f"{base_name}_convertido.json")

            data = [] 
            with open(input_path, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    data.append(row)

            with open(output_path, 'w', encoding='utf-8') as json_file:
                json_file.write(json.dumps(data, indent=4, ensure_ascii=False))

            return True, output_path
        except Exception as e:
            return False, str(e)
        
    # --- IMAGEM PARA PDF ---
    @staticmethod
    def image_to_pdf(input_path):
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_path = os.path.join(folder, f"{base_name}.pdf")

            pdf_bytes = img2pdf.convert(input_path)
            with open(output_path, "wb") as file: 
                file.write(pdf_bytes)

            return True, output_path
        except Exception as e:
            return False, str(e)

    # --- IMAGEM PARA SVG (VETORIZAÇÃO REAL) ---
    @staticmethod
    def image_to_svg(input_path):
        """
        Transforma pixels em vetores matemáticos usando vtracer.
        Ideal para logos e ilustrações.
        """
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_path = os.path.join(folder, f"{base_name}_vetorizado.svg")

            # Executa a vetorização (tracing)
            vtracer.convert_image_to_svg(
                input_path, 
                output_path,
                colormode='color', # Preserva as cores da imagem
                mode='spline',     # Cria curvas suaves (melhor qualidade)
                filter_speckle=4,  # Remove ruídos pequenos
                color_precision=6  # Equilíbrio entre qualidade e tamanho do arquivo
            )

            return True, f"Vetorizado: {output_path}"
        except Exception as e:
            return False, f"Erro na vetorização: {str(e)}"

    # --- PDF PARA IMAGENS (PNG/JPEG) ---
    @staticmethod
    def pdf_to_images(input_path, output_format="png", dpi=300):
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_folder = os.path.join(folder, f"{base_name}_imagens")
            if not os.path.exists(output_folder): os.makedirs(output_folder)

            doc = fitz.open(input_path)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)

            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                image_path = os.path.join(output_folder, f"{base_name}_p{i+1}.{output_format}")
                pix.save(image_path)
                pix = None 

            return True, f"Imagens em: {output_folder}"
        except Exception as e:
            return False, str(e)
        finally:
            if doc: doc.close()

    # --- PDF PARA SVG ---
    @staticmethod
    def pdf_to_svg(input_path):
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_folder = os.path.join(folder, f"{base_name}_svg")
            if not os.path.exists(output_folder): os.makedirs(output_folder)

            doc = fitz.open(input_path)
            for i, page in enumerate(doc):
                svg_path = os.path.join(output_folder, f"{base_name}_p{i+1}.svg")
                with open(svg_path, "w", encoding="utf-8") as f:
                    f.write(page.get_svg_image())

            return True, f"SVGs em: {output_folder}"
        except Exception as e:
            return False, str(e)
        finally:
            if doc: doc.close()

    # --- EXTRAIR IMAGENS DE PDF ---
    @staticmethod
    def extract_images_from_pdf(input_path):
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_folder = os.path.join(folder, f"{base_name}_extraidas")
            if not os.path.exists(output_folder): os.makedirs(output_folder)

            doc = fitz.open(input_path)
            count = 0
            for i in range(len(doc)):
                for img_index, img in enumerate(doc.get_page_images(i)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_path = os.path.join(output_folder, f"img_p{i+1}_{img_index+1}.{base_image['ext']}")
                    with open(image_path, "wb") as f: f.write(base_image["image"])
                    count += 1
            return True, f"{count} fotos em: {output_folder}"
        except Exception as e:
            return False, str(e)
        finally:
            if doc: doc.close()

    # --- PDF PARA MARKDOWN ---
    @staticmethod
    def pdf_to_markdown(input_path):
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            output_path = os.path.join(folder, f"{base_name}.md")

            doc = fitz.open(input_path)
            content = f"# {base_name}\n\n"
            for i, page in enumerate(doc):
                content += f"## Página {i+1}\n\n{page.get_text('text')}\n\n---\n\n"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True, f"Markdown salvo em: {output_path}"
        except Exception as e:
            return False, str(e)
        finally:
            if doc: doc.close()

    # --- OCR VIA API ---
    @staticmethod
    def ocr_via_api(input_path):
        try:
            with open(input_path, 'rb') as f:
                payload = {'apikey': FileConverter.OCR_API_KEY, 'language': 'por'}
                files = {'file': f}
                response = requests.post(FileConverter.OCR_URL, data=payload, files=files)
                result = response.json()

            if result.get('OCRExitCode') == 1:
                parsed_text = result['ParsedResults'][0]['ParsedText']
                folder = os.path.dirname(input_path)
                base_name = os.path.basename(input_path).split('.')[0]
                output_path = os.path.join(folder, f"{base_name}_ocr.txt")
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(parsed_text)
                return True, f"Texto extraído: {output_path}"
            return False, f"Erro API: {result.get('ErrorMessage')}"
        except Exception as e:
            return False, f"Falha: {str(e)}"