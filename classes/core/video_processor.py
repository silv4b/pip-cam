from PyQt6.QtGui import QImage, QPixmap, QPainter, QPainterPath, QColor, QPen
from PyQt6.QtCore import Qt


class VideoProcessor:
    @staticmethod
    def process_frame(frame, zoom, pan_x, pan_y, target_w, target_h):
        import cv2

        if frame is None:
            return None

        h_orig, w_orig = frame.shape[:2]

        # Zoom e Pan
        if zoom > 100:
            zoom_f = zoom / 100.0
            new_h = int(h_orig / zoom_f)
            new_w = int(w_orig / zoom_f)

            pan_x_val = pan_x / 100.0
            pan_y_val = pan_y / 100.0

            y_o = int((h_orig - new_h) * pan_y_val)
            x_o = int((w_orig - new_w) * pan_x_val)

            frame = frame[y_o : y_o + new_h, x_o : x_o + new_w]

        # Aspect Ratio
        h_f, w_f = frame.shape[:2]
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
            # Para QPixmap (Avatar), fazemos o preenchimento centralizado (Crop to fill)
            pixmap = image_or_pixmap.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Calculamos o crop central se ficou maior que o target
            crop_x = (pixmap.width() - target_w) // 2
            crop_y = (pixmap.height() - target_h) // 2
            pixmap = pixmap.copy(crop_x, crop_y, target_w, target_h)

        painter.drawPixmap(0, 0, pixmap)
        painter.setClipping(False)

        # Borda
        if show_border:
            pen = QPen(QColor(border_color))
            pen.setWidthF(border_width)
            painter.setPen(pen)
            painter.drawPath(path)

        painter.end()
        return out_pixmap
