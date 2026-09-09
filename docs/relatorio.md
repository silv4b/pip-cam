<!-- markdownlint-disable MD040 MD060 -->

# Relatório de Viabilidade Técnica: Migração PiP Cam para Tauri + React

**Data:** 15/07/2026
**Versão atual:** v1.2.3.1-alpha
**Stack atual:** Python 3.12+ / PyQt6 / OpenCV / sounddevice
**Stack proposta:** Tauri (Rust) + React (TypeScript)

---

## 1. Resumo do Projeto Atual

PiP Cam é um widget de câmera flutuante (Picture-in-Picture) para Windows/Linux/macOS. O usuário configura câmera, microfone, formato, zoom e preferências visuais num **Launcher** (janela de setup), e então um **widget frameless transparente** é aberto, sempre no topo, exibindo o feed da câmera com máscaras geométricas (círculo, quadrado 1:1, retângulo 4:3) e borda reativa a áudio ("Modo Discord").

### Arquitetura atual (MVC simplificado)

```text
main.py (entry point)
 ├── Launcher (View/Controller)       → classes/views/launcher.py (~970 linhas)
 │    └── PipCameraWidget (View)      → classes/views/pip_widget.py (~536 linhas)
 │         ├── FloatingToolbar        → classes/ui/floating_toolbar.py (~113 linhas)
 │         └── FilterDialog           → classes/ui/filter_dialogs.py (~111 linhas)
 ├── ConfigManager (Model/Singleton)  → classes/core/config_manager.py (~138 linhas)
 ├── DeviceManager (Model)            → classes/core/device_manager.py (~179 linhas)
 ├── AudioAnalyzer (Model)            → classes/core/audio_analyzer.py (~104 linhas)
 ├── HotkeyManager (Controller)       → classes/core/hotkey_manager.py (~74 linhas)
 │    └── ShortcutSignals            → classes/shortcut_signals.py (~17 linhas)
 ├── VideoProcessor (Model)           → classes/core/video_processor.py (~159 linhas)
 └── utils/functions.py               → utils/functions.py (~206 linhas)
```

### Dependências atuais

| Biblioteca     | Versão     | Função                           | Alternativa Tauri/Rust              |
|----------------|------------|----------------------------------|-------------------------------------|
| PyQt6          | >=6.11.0   | GUI (janelas, widgets, pintura)  | Tauri + WebView + HTML Canvas       |
| opencv-python  | >=4.13.0   | Captura de câmera, processamento | `nokhwa` (Rust)                     |
| numpy          | >=2.2.6    | Cálculo RMS de áudio             | `cpal` + matemática nativa          |
| keyboard       | >=0.13.5   | Hotkeys globais                  | `tauri-plugin-global-shortcut`      |
| sounddevice    | >=0.5.5    | Captura de áudio (microfone)     | `cpal` (Rust)                       |
| pygrabber      | >=0.2      | Enumeração DirectShow (Windows)  | `nokhwa` (já faz isso)              |
| qt-themes      | >=0.4.0    | Tema Dracula                     | CSS (React)                         |
| qtpy           | >=2.4.3    | Abstração de backend Qt          | Não aplicável (frontend web)        |

---

## 2. Mapeamento de Funcionalidades para Tauri + React

### 2.1 Captura de Câmera (VIÁVEL)

| Funcionalidade          | Implementação atual                  | Implementação Tauri + React                     |
|-------------------------|--------------------------------------|-------------------------------------------------|
| Enumeração dispositivos | `pygrabber` (Win) / OpenCV scan      | `nokhwa` (`nokhwa::query_devices()`)            |
| Abertura de câmera      | `cv2.VideoCapture(index, DSHOW)`     | `nokhwa::Camera::new(index, ...)`               |
| Captura de frames       | `cap.read()` em loop QTimer (30ms)   | Streaming via IPC (base64 JPEG ou raw bytes)    |
| Espelhamento horizontal | `cv2.flip(frame, 1)`                 | `image::imageops::flip_horizontal()` no Rust    |
| BGR → RGB               | `cv2.cvtColor(frame, BGR2RGB)`       | Conversão direta no Rust (swap R/B channels)    |

**Observação crítica:** O maior desafio técnico é a transmissão de frames da câmera do backend Rust para o frontend React com latência mínima (~33 FPS). Abordagens possíveis:

1. **Base64 JPEG via IPC** (~30-50 KB/frame) — Simples, mas overhead de encoding/decoding
2. **Raw bytes via `tauri::ipc`** — Mais eficiente, requer `Uint8ClampedArray` no JS
3. **OffscreenCanvas + ImageBitmap** — Renderização nativa no browser

Recomendação: Usar raw bytes via IPC binário (`tauri::ipc::Request` com `Response` binário) para minimizar latência.

### 2.2 Processamento de Frames (VIÁVEL)

| Funcionalidade | Implementação atual         | Alternativa Tauri + React                        |
|----------------|-----------------------------|--------------------------------------------------|
| Zoom/Corte     | Slicing numpy array         | Rust: cálculo de ROI, `image::crop_imm()`        |
| Pan (X/Y)      | Deslocamento do ROI         | Rust: ajuste de coordenadas do crop              |
| Aspect ratio   | Corte proporcional          | Rust ou Canvas 2D (frontend)                     |
| Máscara circular| `QPainterPath.addEllipse()`| Canvas 2D API: `ctx.arc()` + `ctx.clip()`        |
| Máscara retangular| `QPainterPath.addRoundedRect()`| Canvas 2D API: `ctx.roundRect()` + `ctx.clip()` |
| Borda colorida | `QPen` + `QPainter.drawPath()` | Canvas 2D: `ctx.strokeStyle` + `ctx.stroke()`   |
| Anti-aliasing  | `QPainter.setRenderHint(Antialiasing)` | Canvas 2D tem anti-aliasing nativo          |

**Decisão de arquitetura:** O processamento pesado (zoom, crop, flip, conversão de cor) deve ser feito **no Rust** antes de enviar o frame. A renderização das máscaras e bordas deve ser feita **no Canvas do frontend**, pois ele já oferece clipping nativo e é mais fácil de manter.

### 2.3 Janela Flutuante (VIÁVEL com ressalvas)

| Funcionalidade               | Implementação atual (PyQt6)                    | Alternativa Tauri                          |
|------------------------------|------------------------------------------------|--------------------------------------------|
| Frameless (sem bordas)       | `FramelessWindowHint`                          | `decorations: false` no `tauri.conf.json`  |
| Sempre no topo               | `WindowStaysOnTopHint`                         | `always_on_top: true`                      |
| Fundo transparente           | `WA_TranslucentBackground`                     | `transparent: true`                        |
| Arrastar com mouse           | Eventos `mousePressEvent` / `mouseMoveEvent`   | Eventos JS `mousedown` / `mousemove`       |
| Múltiplas janelas (multi-cam)| Múltiplos `PipCameraWidget`                    | Múltiplas `WebviewWindow`                  |
| Fechar com ESC               | `keyPressEvent(Qt.Key.Key_Escape)`             | Event listener JS `keydown(Escape)`        |

**Ressalva:** A transparência de janela em Tauri usa `WebView2` no Windows, que pode apresentar um fundo preto em vez de transparente em versões antigas do Windows 10. Solução: exigir WebView2 runtime moderno ou usar `windows-rs` para criar uma janela Win32 nativa com overlay WebView.

_Multi-camera mode:_ Cada widget PiP abre uma nova `WebviewWindow`. O consumo de memória será maior que o PyQt (cada janela carrega um WebView), mas ainda aceitável para 2-4 câmeras.

### 2.4 Barra de Ferramentas Flutuante (VIÁVEL)

Simples: overlay `<div>` com `position: absolute`, `pointer-events: auto`, mostrado/escondido via eventos `onMouseEnter`/`onMouseLeave`. Estilização com CSS (bordas arredondadas, fundo semi-transparente escuro).

### 2.5 Hotkeys Globais (VIÁVEL)

Uso do plugin oficial `tauri-plugin-global-shortcut`:

- `Alt+S` → toggle visibility
- `Alt+C` → toggle camera
- `Alt+M` → toggle mic
- `Alt+A` → toggle avatar
- `Alt+F` → toggle format
- `Alt+D` → toggle border mode
- `Alt+B` → toggle border visibility
- `Alt+=` / `Alt+-` → resize
- `Esc` → close widget

O frontend escuta eventos emitidos pelo plugin via `listen()` do Tauri IPC.

### 2.6 Captura e Análise de Áudio (VIÁVEL)

| Funcionalidade        | Atual (Python)                                   | Alternativa Rust                               |
|-----------------------|--------------------------------------------------|------------------------------------------------|
| Listar microfones     | `sounddevice.query_devices()`                    | `cpal::host().devices()`                       |
| Stream de áudio       | `sd.InputStream(callback=...)`                   | `cpal::Stream` com callback                    |
| Cálculo RMS           | `np.sqrt(np.mean(indata**2))`                    | Loop manual sobre samples (`f32`)              |
| Smoothing (média móvel)| Buffer circular de 5 amostras                   | `VecDeque<f32>` com 5 elementos                |
| Sensibilidade         | Multiplicador (1-10x)                            | Mesma lógica no Rust                           |
| Envio para UI         | `pyqtSignal(float)`                              | IPC `emit("audio_level", level)`               |

### 2.7 Gerenciamento de Configuração (VIÁVEL)

| Funcionalidade          | Atual                              | Alternativa Tauri                              |
|-------------------------|-----------------------------------|------------------------------------------------|
| Armazenamento           | JSON em `%APPDATA%/PiP_Cam/`      | `app_data_dir()` + `serde_json`                |
| Cache em memória        | Singleton `ConfigManager`          | `std::sync::Mutex<Config>` no estado do Tauri  |
| Salvamento agendado     | `QTimer` debounce 200ms            | `tokio::spawn` com delay (`tokio::time::sleep`)|
| Migração de versões     | Script em `functions.py`           | Lógica de migração em Rust no primeiro boot    |
| Configs por câmera/modo| Chaves híbridas (`"Cam1_Circulo"`) | Mesma estrutura, `HashMap<String, Value>`      |

### 2.8 Avatar / Foto Estática (VIÁVEL)

- Upload de imagem: `tauri-plugin-dialog` + `tauri-plugin-fs`
- Cópia para diretório de avatares: Rust (fs::copy)
- Exibição no Canvas: Carregar como `ImageBitmap` e desenhar no canvas com as mesmas máscaras

### 2.9 Diálogo de Filtros (VIÁVEL)

Diálogo modal React com `QListWidget` → `<ul>` com checkboxes. Estado gerenciado via `useState`.

---

## 3. Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────┐
│                  Tauri Backend (Rust)                   │
│                                                         │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │ CameraManager│  │AudioManager│  │ ConfigManager    │ │
│  │ (nokhwa)     │  │ (cpal)     │  │ (serde_json)     │ │
│  ├──────────────┤  ├────────────┤  ├──────────────────┤ │
│  │ list()       │  │ list()     │  │ load()           │ │
│  │ open(id)     │  │ start(id)  │  │ save()           │ │
│  │ read_frame() │  │ get_level  │  │ migrate()        │ │
│  │ close()      │  │ stop()     │  │                  │ │
│  └──────┬───────┘  └────┬───────┘  └────────┬─────────┘ │
│         │               │                   │           │
│  ┌──────┴──────┐  ┌─────┴────┐  ┌───────────┴──────┐    │
│  │WindowManager│  │HotkeyMgr │  │ IPC Commands     │    │
│  │(tauri::win) │  │(plugin)  │  │(tauri::command)  │    │
│  └─────────────┘  └──────────┘  └──────────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │ IPC (invoke / events)
┌──────────────────────────┴────────────────────────────┐
│                Frontend React (TypeScript)            │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │               Launcher Page                      │ │
│  │  ┌──────┐ ┌──────┐ ┌─────┐ ┌────────┐ ┌──────┐   │ │
│  │  │Camera│ │Shape │ │Zoom │ │Border  │ │Audio │   │ │
│  │  │Select│ │Select│ │/Pan │ │Controls│ │Contr.│   │ │
│  │  └──────┘ └──────┘ └─────┘ └────────┘ └──────┘   │ │
│  │  ┌──────────────────┐ ┌──────────────────────┐   │ │
│  │  │  Camera Preview  │ │  Avatar Picker       │   │ │
│  │  │  (Canvas)        │ │                      │   │ │
│  │  └──────────────────┘ └──────────────────────┘   │ │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │            PiP Widget Page (multi-instance)      │ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │         Canvas (máscara + borda)             ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │         FloatingToolbar (overlay)            ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

### Estrutura de diretórios sugerida

```
pip-cam-tauri/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs                 # Entry point
│   │   ├── camera/
│   │   │   ├── mod.rs
│   │   │   └── manager.rs          # CameraManager (nokhwa)
│   │   ├── audio/
│   │   │   ├── mod.rs
│   │   │   └── analyzer.rs         # AudioAnalyzer (cpal)
│   │   ├── config/
│   │   │   ├── mod.rs
│   │   │   └── manager.rs          # ConfigManager (serde)
│   │   ├── video/
│   │   │   ├── mod.rs
│   │   │   └── processor.rs        # VideoProcessor (zoom/crop/flip)
│   │   ├── hotkey/
│   │   │   ├── mod.rs
│   │   │   └── manager.rs          # HotkeyManager
│   │   └── commands.rs             # tauri::command functions
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                            # React frontend
│   ├── App.tsx
│   ├── main.tsx
│   ├── pages/
│   │   ├── Launcher.tsx
│   │   └── PipWidget.tsx
│   ├── components/
│   │   ├── CameraSelector.tsx
│   │   ├── ShapeSelector.tsx
│   │   ├── ZoomControl.tsx
│   │   ├── PanControl.tsx
│   │   ├── BorderControls.tsx
│   │   ├── AudioControls.tsx
│   │   ├── AvatarPicker.tsx
│   │   ├── CameraPreview.tsx        # Canvas preview
│   │   ├── FloatingToolbar.tsx
│   │   ├── FilterDialog.tsx
│   │   └── CameraCanvas.tsx         # PiP canvas rendering
│   ├── hooks/
│   │   ├── useCamera.ts
│   │   ├── useAudio.ts
│   │   ├── useHotkeys.ts
│   │   └── useConfig.ts
│   ├── lib/
│   │   └── tauri.ts                 # IPC wrappers
│   └── styles/
│       └── theme.css                # Dracula theme vars
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 4. Dependências para o Novo Stack

### Rust (Cargo.toml)

```toml
[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-global-shortcut = "2"
tauri-plugin-dialog = "2"
tauri-plugin-fs = "2"
nokhwa = { version = "0.14", features = ["input-native"] }
cpal = "0.15"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
image = "0.25"
tokio = { version = "1", features = ["full"] }
```

### React (package.json)

```json
{
  "dependencies": {
    "react": "^19",
    "react-dom": "^19",
    "react-router-dom": "^7",
    "@tauri-apps/api": "^2",
    "@tauri-apps/plugin-global-shortcut": "^2",
    "@tauri-apps/plugin-dialog": "^2",
    "@tauri-apps/plugin-fs": "^2",
    "zustand": "^5"
  },
  "devDependencies": {
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "typescript": "^5.7",
    "vite": "^6",
    "@tauri-apps/cli": "^2"
  }
}
```

---

## 5. Tabela de Complexidade por Funcionalidade

| Funcionalidade                 | Complexidade | Risco   | Dependências                             |
|--------------------------------|--------------|---------|------------------------------------------|
| Enumeração de câmeras          | Baixa        | Baixo   | `nokhwa`                                 |
| Captura de frames (streaming)  | **Alta**     | **Médio**| IPC binário, `nokhwa`                    |
| Zoom/Pan/Crop                  | Média        | Baixo   | `image` crate, Canvas API                |
| Máscaras (círculo/retângulo)   | Média        | Baixo   | Canvas 2D `clip()`                       |
| Borda reativa a áudio          | Média        | Baixo   | Canvas 2D `stroke()`, evento IPC         |
| Janela frameless transparente  | Média        | **Médio**| WebView2 quirks (Windows)               |
| Multi-janelas (multi-câmera)   | **Alta**     | **Médio**| Gerenciamento de múltiplos WebViews      |
| Hotkeys globais                | Baixa        | Baixo   | `tauri-plugin-global-shortcut`           |
| Captura de áudio (RMS)         | Média        | Baixo   | `cpal`, IPC eventos                      |
| Config JSON                    | Baixa        | Baixo   | `serde_json`, `app_data_dir()`           |
| Filtros de dispositivo         | Baixa        | Baixo   | React state, checkboxes                  |
| Avatar (upload + exibição)     | Baixa        | Baixo   | `tauri-plugin-dialog`, Canvas            |
| Drag-to-move                   | Média        | Baixo   | Eventos JS mousedown/mousemove           |
| Tema Dracula                   | Baixa        | Baixo   | CSS custom properties                    |

---

## 6. Estimativa de Esforço de Desenvolvimento

| Fase                     | Atividades                                           | Estimativa   |
|--------------------------|------------------------------------------------------|--------------|
| Setup do projeto Tauri   | Inicialização, configs, CI/CD, estrutura de pastas   | 2-3 dias     |
| Backend: câmera          | CameraManager (enumeração, captura, streaming IPC)   | 5-7 dias     |
| Backend: áudio           | AudioAnalyzer (cpal, RMS, smoothing, IPC eventos)    | 3-4 dias     |
| Backend: configuração    | ConfigManager (load/save/migrate, serde, debounce)   | 2-3 dias     |
| Backend: hotkeys         | HotkeyManager (tauri-plugin-global-shortcut)         | 1-2 dias     |
| Backend: processamento   | VideoProcessor (zoom/crop/flip em Rust)              | 3-4 dias     |
| Frontend: Launcher       | Página de setup (todos os controles + preview)       | 5-7 dias     |
| Frontend: PiP Widget     | Canvas, máscaras, bordas, toolbar flutuante          | 5-7 dias     |
| Frontend: multi-instância| Roteamento, gerenciamento de múltiplas janelas       | 3-4 dias     |
| Integração e testes      | Testes manuais, correção de bugs, performance tuning | 5-7 dias     |
| **Total**                |                                                      | **~6-8 semanas** |

---

## 7. Riscos e Mitigações

| Risco                                               | Probabilidade | Impacto | Mitigação                                                       |
|-----------------------------------------------------|---------------|---------|-----------------------------------------------------------------|
| Latência alta no streaming de frames                | Média         | Alto    | Usar IPC binário (raw bytes), evitar base64; testar com JPEG leve|
| Transparência de janela falha no Windows 10         | Média         | Médio   | Documentar requisito de WebView2 moderno; fallback para opaco   |
| Multi-janelas consomem muita memória                | Média         | Médio   | Limitar número de janelas; reutilizar WebView se possível       |
| `nokhwa` não suporta câmera específica do usuário  | Baixa         | Alto    | Fallback para OpenCV via `opencv-rust` crate                    |
| `cpal` sem suporte a dispositivo específico         | Baixa         | Médio   | Fallback para gravação via arquivo WAV temporário               |
| Regressão de performance vs Python/PyQt6            | Média         | Médio   | Profiling com `perf`/`tracy`; otimizar loop de captura          |
| Perda das 125+ configurações de teste existentes    | Alta          | Baixo   | Escrever novo test suite do zero (Rust test + Vitest)           |

---

## 8. Conclusão

**Sim, é viável reescrever o PiP Cam em Tauri + React.**

### Pontos fortes da migração

- **Binário final muito menor** (5-15 MB vs 60-100 MB do PyInstaller)
- **Startup mais rápido** (sem runtime Python)
- **UI moderna e flexível** (CSS, animações, responsividade)
- **Ecossistema web** para o frontend (maior disponibilidade de desenvolvedores)
- **Manutenção de longo prazo** mais simples (TypeScript, tipagem forte)

### Pontos de atenção

- O streaming de frames da câmera é o **gargalo técnico** principal — requer IPC otimizado
- Cada janela PiP em modo multi-câmera carrega um WebView completo (~50-80 MB cada), diferentemente do PyQt onde cada widget é leve (~5-10 MB)
- O projeto atual tem **142 testes com 93% de cobertura** — será preciso reescrever todo o test suite
- Funcionalidades como "pausar preview durante drag" exigirão implementação customizada no frontend

### Recomendação

Iniciar com um **prova de conceito (PoC)** focado em:

1. Captura de câmera via `nokhwa` + streaming IPC para Canvas
2. Janela frameless transparente com always-on-top
3. Máscara circular no Canvas 2D com borda colorida

Se o PoC atingir latência ≤40ms e transparência funcional, prosseguir com a migração completa.

---

## Apêndice A: Estratégia de Streaming de Frames (Baixa Latência)

O gargalo central da migração é que no PyQt6 o frame vai do OpenCV direto para o `QPainter` (mesmo processo, zero serialização), enquanto no Tauri o frame precisa cruzar a barreira Rust ↔ WebView via IPC. Abaixo, as abordagens que eliminam esse gargalo.

### A.1 Raw RGBA + `putImageData` (recomendada para frames ≤ 400px)

**Pipeline:**

```
Rust: nokhwa → zoom/crop/flip → RGBA bytes Vec<u8>
                                      ↓
                               Tauri IPC (binary response)
                                      ↓
React: Uint8ClampedArray → ImageData → ctx.putImageData()
```

O PiP Cam usa tamanhos pequenos (200–800px). Uma frame 400×400 RGBA tem ~640KB — cabe em uma única chamada IPC. `putImageData` copia bytes diretamente para a GPU sem decodificação alguma.

```rust
// Rust
#[tauri::command]
fn get_frame(state: State<CameraState>) -> Vec<u8> {
    let frame = state.latest_frame.lock().unwrap();
    frame.rgba_bytes.clone()
}
```

```typescript
// Frontend
const resp = await invoke<number[]>('get_frame', {}, { responseType: 'binary' });
const imageData = new ImageData(new Uint8ClampedArray(resp), width, height);
ctx.putImageData(imageData, 0, 0);
```

**Latência estimada:** ~2–5ms round-trip para 400×400. Folga num loop de 33ms (30 FPS).

**Limitação:** Acima de 600×600 o payload fica grande (~1.4MB+), aumentando o custo de transferência IPC.

### A.2 JPEG + Custom Protocol (recomendada para frames > 400px)

**Pipeline:**

```
Rust: nokhwa → zoom/crop/flip → JPEG encode (quality 75, ~50KB)
                                      ↓
                              Tauri custom protocol (fetch)
                                      ↓
React: response.blob() → createImageBitmap() → ctx.drawImage()
```

O browser decodifica JPEG em hardware (GPU/decoder dedicado). O payload IPC é pequeno (~50KB vs 2.5MB de RGBA). `drawImage` com `ImageBitmap` é otimizado para zero-copy.

```rust
// Rust - custom protocol handler
tauri::Builder::default()
    .register_asynchronous_uri_scheme_protocol("camera", move |_app, req, resp| {
        let frame = state.latest_jpeg.lock().unwrap();
        resp.data = frame.clone();
        resp.mine_type = "image/jpeg".to_string();
        Ok(());
    });
```

```typescript
// Frontend
const blob = await fetch('tauri://camera/frame').then(r => r.blob());
const bitmap = await createImageBitmap(blob);
ctx.drawImage(bitmap, 0, 0);
```

**Latência estimada:** ~3–8ms (encode JPEG + transferência + decode hardware). Browser costuma decodificar JPEG em ~0.5–2ms para frames pequenos.

### A.3 Estratégia Adaptativa Híbrida (recomendação final)

Combinar as duas abordagens baseado no tamanho do frame:

```rust
fn get_frame_bytes(frame: &ProcessedFrame, target_size: u32) -> Vec<u8> {
    if target_size <= 400 {
        frame.rgba_bytes()
    } else {
        frame.jpeg_bytes(75)
    }
}
```

```typescript
const resp = await invoke('get_frame', { size: currentSize });
if (currentSize <= 400) {
    const data = new Uint8ClampedArray(resp as number[]);
    ctx.putImageData(new ImageData(data, w, h), 0, 0);
} else {
    const blob = new Blob([resp], { type: 'image/jpeg' });
    const bitmap = await createImageBitmap(blob);
    ctx.drawImage(bitmap, 0, 0, w, h);
}
```

### A.4 Técnicas Complementares

| Técnica | Descrição | Ganho |
| --------- | ----------- | ------- |
| **Frame skipping** | Rust guarda só o frame mais recente; descarta se frontend não consumiu | Elimina fila |
| **Double buffering** | `Arc<Mutex<Vec<u8>>>` — câmera escreve no buffer B, frontend lê do A, swap atômico | Evita tearing |
| **Pré-processamento no Rust** | Zoom, crop, flip, BGR→RGBA tudo em Rust antes do IPC | Frontend só desenha |
| **Downscale antes do IPC** | Reduzir para o tamanho exato do widget antes de enviar | Menos bytes trafegados |
| **requestAnimationFrame** | Sincroniza `invoke()` com o ciclo de renderização do browser | Evita draws órfãos |

### A.5 Loop Final Recomendado

```rust
// Rust — thread de captura dedicada
loop {
    let frame = camera.frame();                               // nokhwa
    let processed = process(frame, zoom, pan, w, h);          // crop, flip, RGB
    let (bytes, is_rgba) = encode(processed, target_w);       // adaptativo
    *state.latest.lock() = (bytes, is_rgba, target_w, target_h);
    thread::sleep(Duration::from_millis(30));                  // ~33 FPS
}
```

```typescript
// Frontend
async function renderLoop(ctx: CanvasRenderingContext2D) {
    const [bytes, isRgba, w, h] = await invoke('poll_frame');
    if (isRgba) {
        ctx.putImageData(new ImageData(new Uint8ClampedArray(bytes), w, h), 0, 0);
    } else {
        const bitmap = await createImageBitmap(new Blob([bytes], { type: 'image/jpeg' }));
        ctx.drawImage(bitmap, 0, 0, w, h);
    }
    ctx.save();
    clipMask(ctx, mode);
    strokeBorder(ctx, color, width);
    ctx.restore();
    requestAnimationFrame(() => renderLoop(ctx));
}
```

**Latência total estimada:** 3–8ms por frame — dentro do budget de 33ms para 30 FPS. O maior vilão não é o IPC, mas enviar raw sem zoom/crop (desperdício de largura de banda). Processamento no backend + encoding adaptativo resolve o gargalo.
