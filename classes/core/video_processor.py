from PyQt6.QtGui import QImage, QPixmap, QPainter, QPainterPath, QColor, QPen
from PyQt6.QtCore import Qt


class VideoProcessor:
    """
    Classe utilitária estática para processamento e manipulação de imagens da câmera.
    Realiza operações matemáticas e geométricas nos frames (zoom, pan, cortes) 
    sem interferir na lógica de UI.
    """

    # ==========================================
    # Sessão de Processamento de Matriz (OpenCV)
    # ==========================================

    @staticmethod
    def process_frame(frame, zoom, pan_x, pan_y, target_w, target_h):
        """
        Recebe um frame bruto do OpenCV (numpy array) e aplica transformações 
        como zoom, alinhamento (pan) horizontal e vertical, além de garantir o Aspect Ratio.
        
        Args:
            frame (numpy.ndarray): Frame capturado da câmera em BGR.
            zoom (int): Valor do zoom (100 a 500), onde 100 é 1x e 500 é 5x.
            pan_x (int): Alinhamento horizontal (0 a 100).
            pan_y (int): Alinhamento vertical (0 a 100).
            target_w (int): Largura desejada da imagem final.
            target_h (int): Altura desejada da imagem final.
            
        Returns:
            QImage: O frame processado e convertido para o formato do PyQt (QImage).
                    Retorna None se o frame original for inválido.
        """
        import cv2

        if frame is None:
            return None

        h_orig, w_orig = frame.shape[:2]

        # ------------------------------------------
        # Etapa de Zoom e Pan (Movimentação do Corte)
        # ------------------------------------------
        if zoom > 100:
            zoom_f = zoom / 100.0
            new_h = int(h_orig / zoom_f)
            new_w = int(w_orig / zoom_f)

            pan_x_val = pan_x / 100.0
            pan_y_val = pan_y / 100.0

            # Cálculo de offsets baseados nos sliders de pan (0 a 1)
            y_o = int((h_orig - new_h) * pan_y_val)
            x_o = int((w_orig - new_w) * pan_x_val)

            frame = frame[y_o : y_o + new_h, x_o : x_o + new_w]

        # ------------------------------------------
        # Etapa de Correção de Proporção (Aspect Ratio)
        # ------------------------------------------
        h_f, w_f = frame.shape[:2]
        target_ratio = target_w / target_h
        
        # Faz crop adicional para garantir que a imagem não fique distorcida (esticada)
        if (w_f / h_f) > target_ratio:
            crop_w = int(h_f * target_ratio)
            offset = (w_f - crop_w) // 2
            frame = frame[:, offset : offset + crop_w]
        else:
            crop_h = int(w_f / target_ratio)
            offset = (h_f - crop_h) // 2
            frame = frame[offset : offset + crop_h, :]

        # Efeito de espelho (flip horizontal) para visualização mais natural da webcam
        frame = cv2.flip(frame, 1)
        
        # Conversão de BGR (Padrão OpenCV) para RGB (Padrão Qt)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return QImage(
            frame.data,
            frame.shape[1],
            frame.shape[0],
            frame.shape[1] * 3,
            QImage.Format.Format_RGB888,
        )

    # ==========================================
    # Sessão de Desenho e Máscaras (PyQt)
    # ==========================================

    @staticmethod
    def create_masked_pixmap(
        image_or_pixmap,
        target_w,
        target_h,
        mode,
        border_color,
        border_width=6.0,
        show_border=True,
    ):
        """
        Gera um QPixmap final com o formato especificado (Círculo ou Retângulo Arredondado)
        e aplica a borda colorida sobre a imagem.
        
        Args:
            image_or_pixmap (QImage|QPixmap): A imagem processada ou o Avatar selecionado.
            target_w (int): Largura final.
            target_h (int): Altura final.
            mode (str): O formato da máscara ("Círculo", "1:1 (Quadrado)" ou "4:3").
            border_color (str): Cor hexadecimal da borda.
            border_width (float, optional): Espessura da borda. Padrão é 6.0.
            show_border (bool, optional): Define se a borda deve ser desenhada. Padrão é True.
            
        Returns:
            QPixmap: O pixmap final transparente com a máscara e a borda aplicadas.
        """
        out_pixmap = QPixmap(target_w, target_h)
        out_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ------------------------------------------
        # Definição do Formato da Máscara (Clipping)
        # ------------------------------------------
        clip_margin = 3.0
        path = QPainterPath()
        
        if mode == "Círculo":
            path.addEllipse(
                clip_margin,
                clip_margin,
                target_w - 2 * clip_margin,
                target_h - 2 * clip_margin,
            )
        else:
            path.addRoundedRect(
                clip_margin,
                clip_margin,
                target_w - 2 * clip_margin,
                target_h - 2 * clip_margin,
                25,  # Raio do arredondamento (Corners)
                25,
            )

        painter.setClipPath(path)

        # ------------------------------------------
        # Pintura da Imagem Interna
        # ------------------------------------------
        if isinstance(image_or_pixmap, QImage):
            # Imagem de Câmera já vem com o aspect ratio perfeito
            pixmap = QPixmap.fromImage(image_or_pixmap).scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            # Para QPixmap (Avatar estático), fazemos o preenchimento centralizado (Crop to fill)
            pixmap = image_or_pixmap.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Calculamos o crop central se o avatar ficou maior que o target
            crop_x = (pixmap.width() - target_w) // 2
            crop_y = (pixmap.height() - target_h) // 2
            pixmap = pixmap.copy(crop_x, crop_y, target_w, target_h)

        painter.drawPixmap(0, 0, pixmap)
        painter.setClipping(False)

        # ------------------------------------------
        # Desenho da Borda
        # ------------------------------------------
        if show_border:
            pen = QPen(QColor(border_color))
            pen.setWidthF(border_width)
            painter.setPen(pen)
            painter.drawPath(path)

        painter.end()
        return out_pixmap
