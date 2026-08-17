# Catálogo de funções de código

Este é um índice funcional para humanos e IAs. Cada grupo informa **onde está o código**, quais são as funções que uma alteração normalmente deve considerar e seu efeito. Nomes iniciados por `_` são detalhes internos do módulo; não devem ser chamados por uma interface nova sem uma razão clara.

## Orquestração, interfaces e infraestrutura

| Arquivo | Funções/classes principais | Responsabilidade |
| --- | --- | --- |
| `main.py` | bloco `__main__` | Sobe o Uvicorn com a configuração atual. |
| `app/asgi.py` | `application_lifespan`, `exception_handler`, `validation_exception_handler`, `get_application` | Cria o FastAPI, recupera publicações interrompidas e padroniza erros HTTP. |
| `app/controllers/base.py` | `get_task_id`, `get_api_key`, `verify_token` | Lê identificação/chave e valida token quando a rota usar a dependência. |
| `app/controllers/v1/base.py` | `new_router` | Cria router versionado. |
| `app/controllers/v1/video.py` | `create_video`, `create_subtitle`, `create_audio`, `create_task`, `get_all_tasks`, `get_task`, `delete_video`, `get_bgm_list`, `upload_bgm_file`, `get_video_materials_list`, `upload_video_material_file`, `stream_video`, `download_video` | Contrato HTTP de criação, consulta, exclusão, upload e entrega de arquivos. Helpers `_sanitize_*`, `_resolve_*`, `_task_file_to_uri` e `_parse_byte_range` protegem caminhos e streaming. |
| `app/controllers/v1/llm.py` | `generate_video_script`, `generate_video_terms`, `generate_video_social_metadata` | Expõe geração textual do LLM sem criar vídeo. |
| `app/controllers/manager/base_manager.py` | `TaskManager` (`add_task`, `execute_task`, `run_task`, `check_queue`) | Limita concorrência e tamanho da fila. |
| `app/controllers/manager/memory_manager.py` / `redis_manager.py` | `InMemoryTaskManager` / `RedisTaskManager` | Implementam a fila em memória ou Redis. |
| `app/services/state.py` | `BaseState`, `MemoryState`, `RedisState`; `update_task`, `get_task`, `get_all_tasks`, `patch_task`, `delete_task` | Fonte de verdade do estado e progresso das tarefas. |
| `app/services/webui_task.py` | `submit_generation`, `_run_generation`, `get_task_logs` | Submete a geração pela WebUI e armazena logs mostrados nela. |
| `cli.py` | `parse_args`, `build_video_params`, `prepare_cli_files`, `run_cli` | Valida argumentos, converte-os em `VideoParams` e dispara o pipeline. Validadores `_positive_*`, `_hex_color`, `_task_id`, `_bgm_type` rejeitam entradas inválidas. |
| `webui/Main.py` | `_render_application`, `_render_*`, `stable_selectbox`, `tr`, `submit_generation` | Renderiza a aplicação; os métodos `_render_*` são componentes de tela, e os `_get/_set/_normalize_*` estabilizam estado e uploads. |
| `webui/Main.py` | `_render_lofi_factory`, `_save_lofi_upload` | Renderiza a fábrica Lofi/Jazz integrada, valida uploads, apresenta progresso e disponibiliza o vídeo longo para download. |

## Pipeline de geração

| Arquivo | Funções | Responsabilidade |
| --- | --- | --- |
| `app/services/task.py` | `start`, `_run_pipeline`, `generate_script`, `generate_terms`, `save_script_data`, `generate_audio`, `generate_subtitle`, `get_video_materials`, `generate_final_videos` | Orquestra os estágios e atualiza progresso/erros. |
| `app/services/task.py` | `resolve_custom_audio_file`, `_resolve_reusable_voice_preview` | Reutiliza áudio ou prévia de voz apenas se for seguro e compatível. |
| `app/services/task.py` | `is_task_busy`, `_mark_task_failed` | Centraliza bloqueio de exclusão e falha estruturada. |
| `app/services/task.py` | `_schedule_cross_post`, `_run_cross_post`, `recover_interrupted_cross_posts` e helpers `_patch/_record/_ensure/_register/_unregister` | Agenda publicação em rede social, controla slots e recupera estados abandonados. |
| `app/services/task_artifacts.py` | `write_script_data`, `patch_script_data` | Grava e atualiza atomica e seguramente os metadados do roteiro. |

## Conteúdo, áudio e mídia

| Arquivo | Funções | Responsabilidade |
| --- | --- | --- |
| `app/services/llm.py` | `test_connection`, `build_script_prompt`, `generate_script`, `generate_terms`, `build_social_metadata_prompt`, `generate_social_metadata` | Normaliza respostas de múltiplos LLMs e gera roteiro, termos e metadados sociais. Helpers `_normalize/_extract/_parse/_fallback` tratam formatos e respostas ruins. |
| `app/services/material.py` | `search_videos_pexels`, `search_videos_pixabay`, `search_videos_coverr`, `download_videos`, `save_video` | Busca, filtra por proporção, baixa e prepara clipes locais/remotos. |
| `app/services/material_cache.py` | `load_material_search_cache`, `save_material_search_cache`, `cleanup_expired_material_search_cache` | Mantém cache de pesquisas de materiais, sem vazar URLs/segredos impróprios. |
| `app/services/twelvelabs.py` | `is_enabled`, `embed_text`, `rerank_terms_by_subject`, `analyze_clip` | Usa embeddings/análise para melhorar ordem e relevância de termos quando configurado. |
| `app/services/voice.py` | `tts`, `azure_tts_v1/v2`, `siliconflow_tts`, `gemini_tts`, `mimo_tts`, `elevenlabs_tts`, `chatterbox_tts` | Seleciona o provedor TTS e gera fala. |
| `app/services/voice.py` | `get_*_voices`, `is_*_voice`, `create_subtitle`, `get_audio_duration`, `generate_silent_audio` | Lista/identifica vozes, gera legendas temporizadas e lida com modo sem voz. |
| `app/services/subtitle.py` | `create`, `file_to_subtitles`, `correct`, `similarity`, `levenshtein_distance` | Transcreve áudio e corrige/combina legenda com roteiro. |
| `app/services/bgm.py` | `should_use_bgm`, `validate_bgm_upload`, `save_bgm_upload`, `list_bgm_files`, `resolve_bgm_file` | Valida, armazena e resolve música de fundo local. |
| `app/services/sonilo.py` / `elevenlabs_music.py` | `is_enabled`, `test_connection`, `generate_bgm` | Integrações pagas/externas para criar música a partir do vídeo. |
| `app/services/video.py` | `combine_videos`, `generate_video`, `preprocess_video`, `concat_video_clips_with_ffmpeg` | Monta clipes, aplica transições, voz, legenda e BGM; tem fallback de codec/FFmpeg. |
| `app/services/video.py` | `get_bgm_file`, `wrap_text`, `subtitle_font_supports_text`, `subtitle_colors_are_indistinguishable` | Escolhe BGM e protege legibilidade/compatibilidade visual da legenda. |
| `app/services/long_video.py` | `probe_duration`, `calculate_render_duration`, `build_filter_complex`, `build_ffmpeg_command`, `render_long_video` | Mede a playlist e renderiza o loop 1080p com crossfade e watermark usando FFmpeg diretamente. |
| `app/services/upload_post.py` | `UploadPostService.upload_video`, `check_status`, `cross_post_video` | Envia o resultado a serviço externo de publicação e consulta o processamento. |

## Configuração, modelos e utilitários

| Arquivo | Funções/classes | Responsabilidade |
| --- | --- | --- |
| `app/models/schema.py` | `VideoParams`, requests/responses, `VideoAspect.to_resolution`, enums | Contratos de dados e limites de validação. |
| `app/models/llm_provider.py` | `LLMProviderSpec`, `get_llm_provider`, `normalize_provider_override` | Catálogo e resolução de configuração de provedores LLM. |
| `app/models/const.py` | constantes de estado e publicação | Vocabulário compartilhado de estados. |
| `app/config/config.py` | `load_config`, `save_config`, `runtime_config_lock`, `get_default_ollama_base_url` | Lê/grava configuração com exclusão mútua e descobre gateway em container. |
| `app/utils/utils.py` | `task_dir`, `storage_dir`, `resource_dir`, `get_uuid`, `get_response`, `get_ffmpeg_binary`, `normalize_clip_speed`, `load_locales` | Caminhos, respostas, IDs, FFmpeg, idioma e normalizações compartilhadas. |
| `app/utils/file_security.py` | `resolve_path_within_directory` | Impede path traversal antes de ler/servir arquivos. |
| `app/utils/logging_utils.py` | `format_log_record`, `configure_terminal_logger` | Configura logs do terminal. |

### Como localizar uma função que não está nomeada acima

O índice lista os pontos de decisão e todas as famílias de funções. Para encontrar a definição exata, use `rg -n 'def nome_da_funcao' app webui cli.py`. Em especial, funções internas pequenas aparecem junto à família descrita na mesma linha/tabela; isso evita transformar este arquivo em uma cópia frágil do código.
