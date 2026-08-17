# Funções do produto

## O que o produto entrega

O sistema automatiza a produção de vídeos curtos: recebe um assunto ou roteiro, obtém/gera a narração, reúne imagens ou clipes, cria legendas, mistura música e exporta uma ou mais versões do vídeo.

| Função para o usuário | Entrada | Saída | Componentes principais |
| --- | --- | --- | --- |
| Gerar roteiro | Tema, idioma, número de parágrafos e instruções | Texto narrável | API/CLI/WebUI → `services.llm.generate_script` |
| Criar termos de busca | Tema/roteiro e quantidade | Palavras-chave para mídia | `services.llm.generate_terms` |
| Usar roteiro próprio | Texto fornecido | Pula a geração por LLM | `VideoParams.video_script` e `task.generate_script` |
| Obter mídia | Termos, fonte, proporção ou arquivos locais | Clipes válidos | `services.material` e cache |
| Gerar narração | Roteiro, voz, volume e velocidade | Arquivo de áudio e marcas de fala | `services.voice` |
| Usar áudio próprio | Caminho de arquivo autorizado | Narração existente, opcionalmente transcrita | `custom_audio_file` |
| Criar/corrigir legendas | Áudio e roteiro | Arquivo `.srt` | `services.subtitle` e `services.voice` |
| Montar vídeo | Clipes, proporção, duração, ordem e transição | Vídeo combinado | `services.video.combine_videos` |
| Finalizar vídeo | Vídeo combinado, áudio, legenda, música e estilo | `final-*.mp4` | `services.video.generate_video` |
| Produzir variações | `video_count > 1` | Várias versões finais | `task.generate_final_videos` |
| Gerar música por IA | Vídeo, prompt e volume | BGM Sonilo ou ElevenLabs | `services.sonilo` / `elevenlabs_music` |
| Publicar | Vídeo final e credenciais configuradas | Estado e resultado por plataforma | `services.upload_post` |
| Criar vídeo longo Lofi/Jazz | Vídeos, playlist e watermark | MP4 1080p com a duração da playlist | Seção da WebUI e `services.long_video` |

## Formas de usar

- **WebUI:** melhor para configuração interativa, prévia de voz e histórico.
- **API:** melhor para outra aplicação automatizar. A documentação interativa está em `/docs` com o servidor em execução.
- **CLI:** melhor para scripts e execução reprodutível.
- **Skill:** melhor para agentes que podem operar o projeto localmente.

## Estados que a pessoa vê

Uma tarefa recebe `task_id` imediatamente. O cliente consulta `/tasks/{task_id}` ou o histórico da WebUI até que ela termine. O retorno inclui progresso, vídeos e, em falhas, `failed_stage` e `error`. A publicação em rede social é posterior à geração e tem estado próprio (`cross_post_state`), por isso um vídeo pronto pode ainda estar sendo publicado.

## Configurações mais importantes

- Proporção: `16:9`, `9:16` ou `1:1`.
- Ordem dos clipes: aleatória ou sequencial; o modo de correspondência ao roteiro força ordem sequencial.
- Voz: fornecedor, voz, volume e velocidade; também há modo sem voz.
- Legenda: ativação, posição, fonte, cores, contorno e fundo.
- Música: aleatória, arquivo local, nenhuma ou geração por fornecedor habilitado.
- Escala: número de vídeos, threads e limites de fila/concorrência.
