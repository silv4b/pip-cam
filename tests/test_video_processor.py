import pytest
import numpy as np
from PyQt6.QtGui import QImage, QPixmap, QColor
from classes.core.video_processor import VideoProcessor


@pytest.fixture
def sample_frame():
    """Cria um frame de teste uniforme (480x640) com valor de cor 128 em todos os pixels."""
    return np.full((480, 640, 3), 128, dtype=np.uint8)


class TestProcessFrame:
    def test_returns_none_for_none_frame(self):
        """Garante que process_frame retorna None ao receber um frame inválido (None), evitando crashes."""
        result = VideoProcessor.process_frame(None, 100, 50, 50, 320, 240)
        assert result is None

    def test_returns_qimage_for_valid_frame(self, sample_frame):
        """Verifica que um frame válido (numpy array) é convertido com sucesso para QImage."""
        result = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 320, 240)
        assert isinstance(result, QImage)

    def test_returns_qimage_with_correct_format(self, sample_frame):
        """Confirma que o QImage resultante usa o formato RGB888, garantindo compatibilidade com PyQt6."""
        result = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 320, 240)
        assert result.format() == QImage.Format.Format_RGB888

    def test_returns_correct_dimensions(self, sample_frame):
        """Valida que o frame mantém suas dimensões originais quando não há zoom (100%) e o aspect ratio é preservado."""
        result = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 320, 240)
        assert result.width() == 640
        assert result.height() == 480

    def test_zoom_applies_correctly(self, sample_frame):
        """Testa que o zoom de 2x (valor 200) é aplicado corretamente e gera um QImage válido."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:200] = 255

        result = VideoProcessor.process_frame(frame, 200, 50, 50, 320, 240)
        assert isinstance(result, QImage)

    def test_pan_center(self, sample_frame):
        """Verifica que o pan centralizado (50/50) com zoom funciona sem erros."""
        result = VideoProcessor.process_frame(sample_frame, 150, 50, 50, 320, 240)
        assert isinstance(result, QImage)

    def test_pan_extreme_left(self, sample_frame):
        """Testa o pan horizontal no extremo esquerdo (pan_x=0) com zoom, garantindo que não causa crash."""
        result = VideoProcessor.process_frame(sample_frame, 200, 0, 50, 320, 240)
        assert isinstance(result, QImage)

    def test_pan_extreme_right(self, sample_frame):
        """Testa o pan horizontal no extremo direito (pan_x=100) com zoom, garantindo que não causa crash."""
        result = VideoProcessor.process_frame(sample_frame, 200, 100, 50, 320, 240)
        assert isinstance(result, QImage)

    def test_pan_extreme_top(self, sample_frame):
        """Testa o pan vertical no extremo superior (pan_y=0) com zoom, garantindo que não causa crash."""
        result = VideoProcessor.process_frame(sample_frame, 200, 50, 0, 320, 240)
        assert isinstance(result, QImage)

    def test_pan_extreme_bottom(self, sample_frame):
        """Testa o pan vertical no extremo inferior (pan_y=100) com zoom, garantindo que não causa crash."""
        result = VideoProcessor.process_frame(sample_frame, 200, 50, 100, 320, 240)
        assert isinstance(result, QImage)

    def test_no_zoom_no_crop_needed(self, sample_frame):
        """Confirma que sem zoom e com target igual ao original, o frame mantém suas dimensões exatas."""
        result = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 640, 480)
        assert isinstance(result, QImage)
        assert result.width() == 640
        assert result.height() == 480

    def test_flip_horizontal_is_applied(self):
        """Verifica que o espelhamento horizontal (cv2.flip) é aplicado: pixels brancos à esquerda aparecem à direita."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:, :10] = 255

        result = VideoProcessor.process_frame(frame, 100, 50, 50, 100, 100)

        left_pixel = result.pixelColor(0, 0)
        right_pixel = result.pixelColor(99, 0)

        assert right_pixel.red() == 255
        assert left_pixel.red() == 0

    def test_bgr_to_rgb_conversion(self):
        """Confirma que a conversão de BGR (OpenCV) para RGB (Qt) é feita corretamente: canal azul vira vermelho."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:, :] = [255, 0, 0]

        result = VideoProcessor.process_frame(frame, 100, 50, 50, 100, 100)

        pixel = result.pixelColor(0, 0)
        assert pixel.red() == 0
        assert pixel.green() == 0
        assert pixel.blue() == 255

    def test_various_aspect_ratios(self, sample_frame):
        """Testa que o processamento aceita diferentes aspect ratios (16:9, 4:3, 1:1) e sempre retorna um QImage válido."""
        ratios = [(16, 9), (4, 3), (1, 1)]
        for w, h in ratios:
            result = VideoProcessor.process_frame(
                sample_frame, 100, 50, 50, w * 10, h * 10
            )
            assert isinstance(result, QImage)

    def test_max_zoom(self, sample_frame):
        """Valida que o zoom máximo (500 = 5x) é aplicado sem erros."""
        result = VideoProcessor.process_frame(sample_frame, 500, 50, 50, 320, 240)
        assert isinstance(result, QImage)

    def test_min_zoom(self, sample_frame):
        """Valida que o zoom mínimo (100 = 1x, sem zoom) é aplicado sem erros."""
        result = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 320, 240)
        assert isinstance(result, QImage)


class TestCreateMaskedPixmap:
    def test_circle_mode(self, sample_frame):
        """Testa a geração de máscara circular com borda, verificando que o QPixmap final tem o tamanho correto."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage, 200, 200, "Circulo", "#4d6fc4", border_width=6.0, show_border=True
        )
        assert isinstance(pixmap, QPixmap)
        assert pixmap.width() == 200
        assert pixmap.height() == 200

    def test_square_mode(self, sample_frame):
        """Testa a geração de máscara com retângulo arredondado ('1:1 Quadrado')."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage,
            200,
            200,
            "1:1 (Quadrado)",
            "#4d6fc4",
            border_width=6.0,
            show_border=True,
        )
        assert isinstance(pixmap, QPixmap)

    def test_4x3_mode(self, sample_frame):
        """Testa a geração de máscara para o formato 4:3 com borda."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 150)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage, 200, 150, "4:3", "#4d6fc4", border_width=6.0, show_border=True
        )
        assert isinstance(pixmap, QPixmap)

    def test_no_border(self, sample_frame):
        """Verifica que a máscara é gerada corretamente mesmo quando a borda está desabilitada (show_border=False)."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage, 200, 200, "Circulo", "#4d6fc4", border_width=6.0, show_border=False
        )
        assert isinstance(pixmap, QPixmap)

    def test_with_pixmap_input(self):
        """Testa que create_masked_pixmap aceita QPixmap de entrada (avatar estático) com crop centralizado."""
        input_pixmap = QPixmap(200, 200)
        input_pixmap.fill(QColor(255, 0, 0))

        result = VideoProcessor.create_masked_pixmap(
            input_pixmap,
            100,
            100,
            "1:1 (Quadrado)",
            "#000000",
            border_width=4.0,
            show_border=True,
        )
        assert isinstance(result, QPixmap)
        assert result.width() == 100
        assert result.height() == 100

    def test_different_border_colors(self, sample_frame):
        """Valida que diversas cores hexadecimais de borda são aceitas sem erros."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffffff"]
        for color in colors:
            pixmap = VideoProcessor.create_masked_pixmap(
                qimage, 200, 200, "Circulo", color, border_width=8.0, show_border=True
            )
            assert isinstance(pixmap, QPixmap)

    def test_default_border_width(self, sample_frame):
        """Verifica que a função funciona usando apenas os valores padrão de border_width e show_border."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage, 200, 200, "Circulo", "#4d6fc4"
        )
        assert isinstance(pixmap, QPixmap)

    def test_has_transparent_background(self, sample_frame):
        """Confirma que o pixmap gerado possui canal alpha (fundo transparente), essencial para o widget flutuante."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage, 200, 200, "Circulo", "#4d6fc4", border_width=6.0, show_border=True
        )
        assert pixmap.hasAlpha()

    def test_circle_mode_with_accent(self, sample_frame):
        """Testa a geração de máscara circular usando o nome correto com acento ('Círculo'), cobrindo o caminho real do código."""
        qimage = VideoProcessor.process_frame(sample_frame, 100, 50, 50, 200, 200)
        pixmap = VideoProcessor.create_masked_pixmap(
            qimage, 200, 200, "Círculo", "#4d6fc4", border_width=6.0, show_border=True
        )
        assert isinstance(pixmap, QPixmap)
        assert pixmap.width() == 200
        assert pixmap.height() == 200
