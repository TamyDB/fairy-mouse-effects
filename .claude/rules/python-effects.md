---
paths:
  - "fairy_mouse/**"
  - "tests/**"
  - "main.py"
---
# Python, cursor e efeitos

- Preserve o desenho aprovado; não adicionar blur, imagens, capturas contínuas de tela ou novos efeitos sem escopo definido pelo usuário.
- `particles.py` é independente de GTK e recebe tempo monotônico do chamador. Preserve limites de emissão e quantidade total compartilhada entre monitores.
- `rendering.py` serve à demonstração e ao overlay. Mudanças devem considerar ambos.
- `cursor.py` usa metadados EXT, não deltas evdev para estimar posição. O leitor bloqueia em uma thread; GTK recebe apenas a posição mais recente, limitado pelo FPS.
- Trate pixels transformados e unidades lógicas sem reaplicar rotação ou subtrair hotspot. O overlay deve cobrir a saída inteira: zona -1 e quatro âncoras.
- Mantenha carga de Gtk4LayerShell anterior ao import GTK/GDK e operações GTK na thread principal.
- Para clique, preserve O_RDONLY, máscara EVIOCSMASK obrigatória antes de ler, recuperação SYN_DROPPED e limpeza de fontes/descritores. Sem grab, reinjeção ou leitura de teclas extras.
- Classifique ponteiros por BTN_LEFT + eixos X/Y; KEY_ENTER extra não transforma um Logitech em teclado comum.
- Teste limites, expiração, coordenadas, perda de dispositivos e fim da sessão conforme a mudança. Não apresente resultados simulados como comprovação gráfica real.
