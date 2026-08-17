# Fábrica de vídeos longos Lofi/Jazz

## Instalação

Requer Python 3.11+, FFmpeg e FFprobe disponíveis no `PATH`.

```bash
pip install -r requirements.txt
ffmpeg -version
ffprobe -version
```

No Ubuntu/Debian, os binários podem ser instalados com `sudo apt install ffmpeg`. No macOS, use `brew install ffmpeg`. No Windows, instale uma distribuição oficial do FFmpeg e adicione a pasta `bin` ao `PATH`.

## Execução

Na raiz do projeto:

```bash
./webui.sh
```

O script inicia a WebUI principal, que inclui a seção **Fábrica de vídeos Lofi/Jazz**, e configura até 2 GB por upload.

O limite acima aceita até 2 GB por upload. Ajuste-o conforme o tamanho dos WAVs e a memória disponível na máquina.

Envie um ou mais `.mp4`, faixas `.mp3`/`.wav`, uma marca `.png`; escolha duração, transição, brilho e X/Y; depois clique em **Gerar Vídeo Longo**.

## Pipeline

O backend usa `subprocess` com uma lista de argumentos, sem shell e sem MoviePy. O FFprobe mede as mídias; o FFmpeg sorteia vídeos e músicas até cobrir a duração escolhida, normaliza para 1920×1080, aplica transições, brilho, crossfades e a marca com 80% de opacidade, e codifica em H.264 `veryfast` com áudio AAC a 320 kbps.

Um crossfade de 5 segundos sobrepõe 5 segundos entre duas faixas. O sorteio considera essa redução e adiciona músicas até a mixagem cobrir a duração solicitada; `-t` realiza o corte exato. Para limitar custo e complexidade, os vídeos formam um ciclo aleatório de até cinco minutos, que é repetido até o final.
