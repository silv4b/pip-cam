from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap


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

    if zoom > 100:
        zoom_f = zoom / 100.0
        new_h = int(h_orig / zoom_f)
        new_w = int(w_orig / zoom_f)

        pan_x_val = pan_x / 100.0
        pan_y_val = pan_y / 100.0

        y_o = int((h_orig - new_h) * pan_y_val)
        x_o = int((w_orig - new_w) * pan_x_val)

        frame = frame[y_o : y_o + new_h, x_o : x_o + new_w]

    h_f, w_f = frame.shape[:2]
    if target_w <= 0 or target_h <= 0:
        return None
    target_ratio = target_w / target_h

    if (w_f / h_f) > target_ratio:
        crop_w = int(h_f * target_ratio)
        offset = (w_f - crop_w) // 2
        frame = frame[:, offset : offset + crop_w]
    else:
        crop_h = int(w_f / target_ratio)
        offset = (h_f - crop_h) // 2
        frame = frame[offset : offset + crop_h, :]

    frame = cv2.flip(frame, 1)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    return QImage(
        frame.data,
        frame.shape[1],
        frame.shape[0],
        frame.shape[1] * 3,
        QImage.Format.Format_RGB888,
    )


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
    if image_or_pixmap is None:
        out_pixmap = QPixmap(target_w, target_h)
        out_pixmap.fill(Qt.GlobalColor.transparent)
        return out_pixmap

    out_pixmap = QPixmap(target_w, target_h)
    out_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

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
            25,
            25,
        )

    painter.setClipPath(path)

    if isinstance(image_or_pixmap, QImage):
        pixmap = QPixmap.fromImage(image_or_pixmap).scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    else:
        pixmap = image_or_pixmap.scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        crop_x = (pixmap.width() - target_w) // 2
        crop_y = (pixmap.height() - target_h) // 2
        pixmap = pixmap.copy(crop_x, crop_y, target_w, target_h)

    painter.drawPixmap(0, 0, pixmap)
    painter.setClipping(False)

    if show_border:
        pen = QPen(QColor(border_color))
        pen.setWidthF(border_width)
        painter.setPen(pen)
        painter.drawPath(path)

    painter.end()
    return out_pixmap


def process_avatar(pixmap, zoom, pan_x, pan_y, target_w, target_h):
    """
    Aplica zoom e alinhamento (pan) em um QPixmap de avatar, retornando um QImage.
    A lógica é análoga à process_frame: primeiro recorta com zoom, depois ajusta
    para o aspect ratio do target usando pan para posicionar o crop.

    Args:
        pixmap (QPixmap): Imagem do avatar.
        zoom (int): Nível de zoom (100 a 500), onde 100 é 1x e 500 é 5x.
        pan_x (int): Alinhamento horizontal (0 a 100).
        pan_y (int): Alinhamento vertical (0 a 100).
        target_w (int): Largura desejada da imagem final.
        target_h (int): Altura desejada da imagem final.

    Returns:
        QImage: A imagem processada. Retorna None se o pixmap for inválido.
    """
    if pixmap is None or pixmap.isNull():
        return None

    if target_w <= 0 or target_h <= 0:
        return None

    w_orig = pixmap.width()
    h_orig = pixmap.height()

    # Passo 1: Aplica zoom recortando da imagem original
    if zoom > 100:
        zoom_f = zoom / 100.0
        new_w = int(w_orig / zoom_f)
        new_h = int(h_orig / zoom_f)

        pan_x_val = pan_x / 100.0
        pan_y_val = pan_y / 100.0

        x_o = int((w_orig - new_w) * pan_x_val)
        y_o = int((h_orig - new_h) * pan_y_val)

        x_o = max(0, min(x_o, w_orig - new_w))
        y_o = max(0, min(y_o, h_orig - new_h))

        region = pixmap.copy(x_o, y_o, new_w, new_h)
    else:
        region = pixmap.copy(0, 0, w_orig, h_orig)

    # Passo 2: Ajusta para o aspect ratio do target usando pan para posicionar
    w_f = region.width()
    h_f = region.height()
    target_ratio = target_w / target_h
    source_ratio = w_f / h_f

    if source_ratio > target_ratio:
        # Imagem é mais larga que o target — crop horizontal, pan controla posição X
        crop_w = int(h_f * target_ratio)
        max_offset = w_f - crop_w
        offset = int(max_offset * (pan_x / 100.0))
        region = region.copy(offset, 0, crop_w, h_f)
    else:
        # Imagem é mais alta que o target — crop vertical, pan controla posição Y
        crop_h = int(w_f / target_ratio)
        max_offset = h_f - crop_h
        offset = int(max_offset * (pan_y / 100.0))
        region = region.copy(0, offset, w_f, crop_h)

    # Passo 3: Redimensiona para o tamanho final
    result = region.scaled(
        target_w,
        target_h,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return result.toImage()


class VideoProcessor:
    process_frame = staticmethod(process_frame)
    process_avatar = staticmethod(process_avatar)
    create_masked_pixmap = staticmethod(create_masked_pixmap)
