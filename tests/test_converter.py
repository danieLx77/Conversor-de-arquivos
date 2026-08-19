import json
from unittest import mock

import fitz
from PIL import Image

from core.converter import (
    FileConverter,
    OCR_TIMEOUT,
    OCR_URL,
    unique_output_path,
)


def _make_pdf(tmp_path, text="Conteúdo teste"):
    pdf_path = tmp_path / "doc.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_unique_output_path(tmp_path):
    first = unique_output_path(str(tmp_path), "arquivo", ".pdf")
    assert first == str(tmp_path / "arquivo.pdf")

    open(first, "w").close()
    second = unique_output_path(str(tmp_path), "arquivo", ".pdf")
    assert second == str(tmp_path / "arquivo_1.pdf")

    open(second, "w").close()
    third = unique_output_path(str(tmp_path), "arquivo", ".pdf")
    assert third == str(tmp_path / "arquivo_2.pdf")


def test_text_to_binary(tmp_path):
    src = tmp_path / "exemplo.txt"
    src.write_text("AB", encoding="utf-8")

    sucesso, resultado = FileConverter.text_to_binary(str(src))
    assert sucesso

    output = tmp_path / "exemplo_convertido.bin"
    assert str(output) == resultado
    assert output.read_text(encoding="utf-8") == "01000001 01000010"


def test_text_to_binary_inexistente(tmp_path):
    sucesso, resultado = FileConverter.text_to_binary(str(tmp_path / "nao_existe.txt"))
    assert not sucesso
    assert isinstance(resultado, str)


def test_csv_to_json(tmp_path):
    src = tmp_path / "dados.csv"
    src.write_text("nome,idade\nMaria,30\nJoão,25\n", encoding="utf-8")

    sucesso, resultado = FileConverter.csv_to_json(str(src))
    assert sucesso

    output = tmp_path / "dados_convertido.json"
    assert str(output) == resultado
    assert json.loads(output.read_text(encoding="utf-8")) == [
        {"nome": "Maria", "idade": "30"},
        {"nome": "João", "idade": "25"},
    ]


def test_image_to_pdf(tmp_path):
    img_path = tmp_path / "imagem.png"
    Image.new("RGB", (10, 10), "red").save(img_path)

    sucesso, resultado = FileConverter.image_to_pdf(str(img_path))
    assert sucesso

    output = tmp_path / "imagem.pdf"
    assert str(output) == resultado
    assert output.read_bytes().startswith(b"%PDF")


def test_pdf_to_images(tmp_path):
    pdf = _make_pdf(tmp_path)

    sucesso, resultado = FileConverter.pdf_to_images(str(pdf), "png")
    assert sucesso

    output_folder = tmp_path / "doc_imagens"
    assert output_folder.exists()
    assert (output_folder / "doc_p1.png").exists()


def test_pdf_to_svg(tmp_path):
    pdf = _make_pdf(tmp_path)

    sucesso, resultado = FileConverter.pdf_to_svg(str(pdf))
    assert sucesso

    output_folder = tmp_path / "doc_svg"
    assert (output_folder / "doc_p1.svg").exists()


def test_pdf_to_markdown(tmp_path):
    pdf = _make_pdf(tmp_path)

    sucesso, resultado = FileConverter.pdf_to_markdown(str(pdf))
    assert sucesso

    output = tmp_path / "doc.md"
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "# doc" in content
    assert "Conteúdo teste" in content


def test_extract_images_from_pdf(tmp_path):
    img_path = tmp_path / "foto.png"
    Image.new("RGB", (20, 20), "blue").save(img_path)
    pdf_path = tmp_path / "com_foto.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, filename=str(img_path))
    doc.save(str(pdf_path))
    doc.close()

    sucesso, resultado = FileConverter.extract_images_from_pdf(str(pdf_path))
    assert sucesso
    assert resultado.startswith("1 fotos")

    output_folder = tmp_path / "com_foto_extraidas"
    assert len(list(output_folder.iterdir())) == 1


def test_ocr_via_api_success(tmp_path, monkeypatch):
    img_path = tmp_path / "texto.png"
    Image.new("RGB", (10, 10), "white").save(img_path)

    mock_response = mock.Mock()
    mock_response.json.return_value = {
        "OCRExitCode": 1,
        "ParsedResults": [{"ParsedText": "Texto extraído"}],
    }

    def fake_post(url, data, files, timeout):
        assert url == OCR_URL
        assert data["language"] == "por"
        assert data["apikey"] == "chave-teste"
        assert timeout == OCR_TIMEOUT
        return mock_response

    monkeypatch.setattr("core.converter.OCR_API_KEY", "chave-teste")
    with mock.patch("core.converter.requests.post", side_effect=fake_post):
        sucesso, resultado = FileConverter.ocr_via_api(str(img_path))

    assert sucesso
    output = tmp_path / "texto_ocr.txt"
    assert str(output) in resultado
    assert output.read_text(encoding="utf-8") == "Texto extraído"


def test_ocr_via_api_sem_chave(tmp_path, monkeypatch):
    monkeypatch.setattr("core.converter.OCR_API_KEY", None)

    sucesso, resultado = FileConverter.ocr_via_api(str(tmp_path / "x.png"))
    assert not sucesso
    assert "Chave OCR não configurada" in resultado


def test_supported_targets_mapping():
    from ui.app_window import App

    assert App._supported_targets("txt") == ["Binário"]
    assert App._supported_targets("csv") == ["JSON"]
    assert App._supported_targets("png") == ["PDF", "SVG", "OCR na Nuvem (API)"]
    assert App._supported_targets("pdf") == [
        "PNG",
        "JPEG",
        "SVG",
        "Extrair Imagens",
        "Markdown (.md)",
        "OCR na Nuvem (API)",
    ]
    assert App._supported_targets("exe") == []
    assert App._file_extension("Arquivo.PDF") == "pdf"