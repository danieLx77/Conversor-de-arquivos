# Conversor-de-arquivos

Aplicativo desktop com interface gráfica desenvolvido em Python para conversão de arquivos entre múltiplos formatos, eliminando a necessidade de instalar ferramentas separadas para cada transformação. O sistema opera como uma central única de conversão local, cobrindo TXT para binário, CSV para JSON, imagem (JPG/JPEG/PNG/WEBP) para PDF, SVG e texto extraído por OCR, além de PDF para PNG/JPEG, SVG, Markdown e extração de imagens.

A arquitetura adota o princípio de camadas com baixo acoplamento entre interface e serviço: a camada de UI expõe um menu de destinos preenchido dinamicamente a partir de um mapeamento declarativo de conversões, e a camada de serviço centraliza as operações em métodos estáticos. As conversões são executadas localmente, exceto o reconhecimento óptico de caracteres (OCR), que delega a extração de texto a uma API externa via HTTP.

## Tecnologias e Dependências

- Linguagem: Python 3.13
- Interface gráfica: customtkinter 5.2.2
- Processamento de PDF: PyMuPDF 1.27.2.2
- Conversão de imagem para PDF: img2pdf 0.6.3
- Vetorização de imagem para SVG: vtracer 0.6.15
- Manipulação de imagens: pillow 12.1.0
- Requisições HTTP (OCR): requests 2.33.1
- Variáveis de ambiente: python-dotenv 1.2.2
- Testes automatizados: pytest >= 8.0
- Toolchain: pip + venv (Python 3.13)

## Arquitetura do Sistema

O projeto segue o padrão de arquitetura em camadas (entrypoint, interface/controlador e serviço), sem banco de dados e sem exposição de API HTTP própria.

```
Conversor-de-arquivos/
├── src/
│   ├── main.py                  # Entrypoint: instancia a App e inicia o loop do Tkinter
│   ├── core/
│   │   └── converter.py         # Serviço: FileConverter (operações) + mapeamento declarativo
│   └── ui/
│       └── app_window.py        # Interface/controlador: App (menu dinâmico e despacho de conversões)
├── tests/
│   ├── conftest.py              # Adiciona src/ ao sys.path para importação nos testes
│   └── test_converter.py        # Suíte de testes unitários e de integração
├── .env.example                 # Modelo de configuração de variáveis de ambiente
├── .env                         # Configuração local (ignorado pelo versionamento)
├── requirements.txt             # Dependências de runtime e desenvolvimento
├── LICENSE                      # Licença MIT
└── README.md
```

- `core/converter.py`: define as constantes `FORMATS`, `SUPPORTED_CONVERSIONS`, `SUPPORTED_EXTENSIONS` e `LABEL_TO_CODE`, que constituem o contrato declarativo entre interface e serviço; a classe `FileConverter` concentra as nove operações de conversão como métodos estáticos e o helper `unique_output_path`, que garante nomes de saída sem sobrescrita.
- `ui/app_window.py`: a classe `App` atua como controlador de interface. Ao importar um arquivo, valida a extensão e popula o menu de destinos apenas com as conversões suportadas; `start_conversion` traduz o rótulo selecionado para um código estável e delega a execução ao serviço por meio do despacho `_dispatch`.
- `main.py`: ponto de entrada que instancia `App` e executa o loop de eventos do Tkinter.

## Pré-requisitos

- Python 3.13 ou superior instalado no ambiente.
- Tkinter disponível no ambiente gráfico (no Linux, instalar o pacote `python3-tk`).
- Acesso à internet para a funcionalidade de OCR.
- Chave de API do serviço OCR.SPACE para utilização da funcionalidade de OCR (obter em https://ocr.space).

## Instalação e Configuração

1. Clonagem do repositório:

```bash
git clone <url-do-repositorio>
cd Conversor-de-arquivos
```

2. Configuração das variáveis de ambiente. Copie o arquivo de exemplo e preencha a chave da API:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e defina o valor da variável `OCR_SPACE_KEY`, utilizada exclusivamente pela funcionalidade de OCR. Sem essa chave, as demais conversões operam normalmente e o OCR retorna erro de configuração.

3. Criação do ambiente virtual e instalação das dependências:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Execução

O entrypoint importa os pacotes `ui` e `core` relativos ao diretório `src`, portanto a aplicação deve ser executada a partir desse diretório:

```bash
cd src
python main.py
```

O aplicativo abre uma janela com botão de importação de arquivo, menu de formatos de destino e botão de conversão. As saídas são geradas no mesmo diretório do arquivo de origem, com nomes derivados do arquivo original; se o arquivo de destino já existir, um sufixo numérico é adicionado automaticamente.

## Testes Automatizados

A suíte cobre os conversores e o contrato de mapeamento da interface, com a chamada HTTP de OCR simulada via mock. Execute a partir da raiz do projeto:

```bash
python -m pytest tests/ -v
```

Análise de cobertura de código: a dependência `pytest-cov` não está incluída no projeto. Para habilitá-la, instale o pacote e execute:

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src
```

## Endpoints da API

Este projeto é um aplicativo desktop e não expõe API HTTP própria. As operações de conversão são acionadas pela interface e executadas pela camada de serviço:

| Entrada | Destino | Método (FileConverter) | Artefato de saída |
|---------|---------|------------------------|-------------------|
| .txt | Binário | `text_to_binary` | `<nome>_convertido.bin` |
| .csv | JSON | `csv_to_json` | `<nome>_convertido.json` |
| .jpg/.jpeg/.png/.webp | PDF | `image_to_pdf` | `<nome>.pdf` |
| .jpg/.jpeg/.png/.webp | SVG | `image_to_svg` | `<nome>_vetorizado.svg` |
| .jpg/.jpeg/.png/.webp | OCR | `ocr_via_api` | `<nome>_ocr.txt` |
| .pdf | PNG/JPEG | `pdf_to_images` | `<nome>_imagens/<nome>_pN.png\|.jpeg` |
| .pdf | SVG | `pdf_to_svg` | `<nome>_svg/<nome>_pN.svg` |
| .pdf | Extrair imagens | `extract_images_from_pdf` | `<nome>_extraidas/img_pN_M.ext` |
| .pdf | Markdown | `pdf_to_markdown` | `<nome>.md` |

Integração HTTP externa utilizada pela funcionalidade de OCR:

| Método | Rota | Parâmetros | Descrição |
|--------|------|------------|-----------|
| POST | `https://api.ocr.space/parse/image` | multipart: `file` (arquivo de imagem), `apikey` (`OCR_SPACE_KEY`), `language=por`; `timeout=30` | Envia uma imagem e retorna o texto extraído (campo `ParsedResults[0].ParsedText`), salvo em arquivo `.txt`. |

## Licença

Distribuído sob a licença MIT. Copyright (c) 2026 Daniel de Jesus Moreira. Consulte o arquivo `LICENSE` para detalhes.