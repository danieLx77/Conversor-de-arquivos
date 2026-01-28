import os
import csv
import json
import img2pdf
class FileConverter:

    #.txt para binário
    @staticmethod
    def text_to_binary(input_path):
        """
        Lê um arquivo de texto (.txt) e converte cada letra em seu código binário (0s e 1s).
        Salva o novo arquivo na mesma pasta do original.
        """
        folder = os.path.dirname(input_path)
        base_name = os.path.basename(input_path).split('.')[0]
        
        output_path = os.path.join(folder, f"{base_name}_convertido.bin")

        try:
            with open(input_path, 'r', encoding='utf-8') as file:
                text_content = file.read()

            binary_content = ' '.join(format(ord(char), '08b') for char in text_content)

            with open(output_path, 'w', encoding='utf-8') as bin_file:
                bin_file.write(binary_content)

            return True, output_path 

        except Exception as e:
            return False, str(e) 
    

    #.csv para JSON
    @staticmethod
    def csv_to_json(input_path):
        """
        Lê um arquivo CSV (tabela) e converte para JSON (formato de dados da web).
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
        
        
        
    #.imagem para PDF
    @staticmethod
    def image_to_pdf(input_path):
            """
            Converte uma imagem (JPG, PNG) para PDF sem perda de qualidade (lossless).
            O PDF terá exatamente o tamanho da imagem original.
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