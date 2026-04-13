import os
import csv
import json
import img2pdf
import fitz  

class FileConverter:

    # --- TXT PARA BINÁRIO ---
    @staticmethod
    def text_to_binary(input_path):
        """
        Converte cada caractere de um arquivo .txt em sua representação binária de 8 bits.
        """
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
        """
        Converte uma tabela CSV em um arquivo JSON estruturado.
        """
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
        """
        Converte imagens (PNG/JPG) para um arquivo PDF sem perda de qualidade.
        """
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

    # --- PDF PARA IMAGENS (PNG/JPEG) ---
    @staticmethod
    def pdf_to_images(input_path, output_format="png", dpi=300):
        """
        Converte páginas inteiras de um PDF em imagens rasterizadas.
        """
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            
            output_folder = os.path.join(folder, f"{base_name}_imagens")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            doc = fitz.open(input_path)
            generated_files = []

            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)

            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                
                page_num = i + 1
                image_name = f"{base_name}_pagina_{page_num}.{output_format}"
                image_path = os.path.join(output_folder, image_name)
                
                pix.save(image_path)
                generated_files.append(image_path)
                
                pix = None # Garante liberação de RAM por página

            return True, f"Pasta: {output_folder}"

        except Exception as e:
            return False, f"Erro na conversão: {str(e)}"
        finally:
            if doc:
                doc.close()

    # --- PDF PARA SVG (VETORIAL) ---
    @staticmethod
    def pdf_to_svg(input_path):
        """
        Converte páginas de PDF para vetores SVG (zoom infinito sem pixelar).
        """
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            
            output_folder = os.path.join(folder, f"{base_name}_svg")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            doc = fitz.open(input_path)
            generated_files = []

            for i, page in enumerate(doc):
                page_num = i + 1
                svg_name = f"{base_name}_pagina_{page_num}.svg"
                svg_path = os.path.join(output_folder, svg_name)
                
                svg_content = page.get_svg_image()
                
                with open(svg_path, "w", encoding="utf-8") as f:
                    f.write(svg_content)
                
                generated_files.append(svg_path)

            return True, f"Pasta: {output_folder}"

        except Exception as e:
            return False, f"Erro no SVG: {str(e)}"
        finally:
            if doc:
                doc.close()

    # --- EXTRAIR IMAGENS EMBUTIDAS NO PDF ---
    @staticmethod
    def extract_images_from_pdf(input_path):
        """
        Busca e salva apenas as fotos/objetos de imagem originais dentro do PDF.
        """
        doc = None
        try:
            folder = os.path.dirname(input_path)
            base_name = os.path.basename(input_path).split('.')[0]
            
            output_folder = os.path.join(folder, f"{base_name}_extraidas")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            doc = fitz.open(input_path)
            image_count = 0

            for i in range(len(doc)):
                image_list = doc.get_page_images(i)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    image_name = f"foto_p{i+1}_{img_index+1}.{image_ext}"
                    image_path = os.path.join(output_folder, image_name)
                    
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    
                    image_count += 1

            return True, f"{image_count} imagens em: {output_folder}"

        except Exception as e:
            return False, f"Erro na extração: {str(e)}"
        finally:
            if doc:
                doc.close()