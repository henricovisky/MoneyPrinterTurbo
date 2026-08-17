# Regras de negócio e invariantes

Estas regras definem o comportamento esperado. Ao alterar o código, preserve-as ou atualize este documento e os testes correspondentes.

## Tarefa e pipeline

1. Toda solicitação cria um `task_id` e um estado antes de entrar na fila.
2. A fila respeita `max_concurrent_tasks` e `max_queued_tasks`; quando cheia, a API retorna `429` e remove o estado recém-criado.
3. O pipeline pode parar em `audio`, `subtitle` ou `video`. Um estágio posterior não deve rodar quando o anterior falha ou quando o `stop_at` foi atingido.
4. Falhas devem preservar o maior progresso já alcançado e informar `failed_stage` e `error`.
5. Uma tarefa em geração ou em publicação não pode ser excluída, pois ainda pode ler/gravar arquivos do diretório dela.

## Roteiro e materiais

1. Roteiro fornecido pelo usuário tem precedência; o LLM só é chamado se ele estiver vazio.
2. Termos fornecidos têm precedência; sem eles, o LLM os cria a partir do assunto/roteiro.
3. Quando `match_materials_to_script` está ativo, os termos, download e concatenação seguem a ordem narrativa; a concatenação é necessariamente sequencial.
4. Sem correspondência ao roteiro, múltiplos vídeos usam modo aleatório para aumentar a diferença entre versões.
5. Materiais remotos precisam respeitar a proporção solicitada e materiais locais precisam ser válidos antes da composição.

## Áudio, legendas e música

1. `custom_audio_file` substitui TTS; ainda pode servir para gerar legendas por transcrição.
2. Modo sem voz cria silêncio com duração estimada para que a linha do tempo continue válida.
3. Legenda é opcional. Quando ativa, fonte, cor e fundo precisam ser aplicáveis e legíveis; o serviço verifica suporte da fonte e combinação de cores.
4. Música é usada somente se o tipo estiver habilitado e o volume for maior que zero.
5. Música de IA não pode fazer a tarefa inteira falhar depois que vídeo, voz e legenda já existem: a saída final deve ser gerada sem BGM e registrar um aviso.
6. Música local enviada pelo usuário é validada antes de ser persistida ou usada pelo FFmpeg.

## Segurança e dados

1. Arquivos enviados, caminhos de áudio/mídia e URLs de download devem permanecer no diretório permitido; `..`, caminhos absolutos externos e nomes inválidos são rejeitados.
2. Dados internos de coordenação, como `cross_post_owner`, não podem aparecer na resposta pública da API.
3. URLs/credenciais sensíveis não devem ser persistidas em cache de materiais ou incluídas em erros.
4. O endpoint de streaming aceita somente uma faixa HTTP por requisição; faixas inválidas retornam `416`.

## Publicação e recuperação

1. Publicação em redes sociais roda fora do limite de concorrência da geração de vídeos, em pool próprio e com limite de pendências.
2. A publicação tem estados `pending`, `processing`, `completed` e `failed` (conforme constantes do projeto) e não pode ficar ativa indefinidamente após reinício.
3. No início da API, tarefas de publicação cujo processo dono não existe são marcadas como falhas; em instalação multi-host o código é conservador para não interromper trabalho de outro host.

## Compatibilidade e configuração

1. Campos novos devem ter defaults compatíveis com tarefas históricas e CLI/WebUI existentes. Exemplo: `video_music_prompt` convive com `sonilo_bgm_prompt` legado.
2. Configuração é lida/escrita com lock. Não escreva `config.toml` diretamente em fluxos concorrentes.
3. Redis é opcional: o comportamento básico deve continuar possível com estado/fila em memória.
