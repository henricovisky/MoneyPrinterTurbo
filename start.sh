#!/usr/bin/env bash

# Diretório atual do repositório
CURRENT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$CURRENT_DIR"

# Identifica o Python do ambiente virtual (.venv) ou do sistema
if [ -x "$CURRENT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$CURRENT_DIR/.venv/bin/python"
elif command -v uv >/dev/null 2>&1; then
    PYTHON_CMD="uv run python"
else
    PYTHON_CMD="python3"
fi

echo "=========================================="
echo "🚀 Iniciando Servidor API (FastAPI)..."
echo "=========================================="

# Inicia o servidor API em segundo plano
$PYTHON_CMD "$CURRENT_DIR/main.py" &
API_PID=$!

# Função para encerrar o processo da API ao fechar o script (Ctrl+C)
cleanup() {
    echo ""
    echo "=========================================="
    echo "🛑 Encerrando Servidor API (PID: $API_PID)..."
    echo "=========================================="
    kill "$API_PID" 2>/dev/null
    wait "$API_PID" 2>/dev/null
    exit 0
}

# Captura os sinais de interrupção (Ctrl+C), cancelamento e saída
trap cleanup INT TERM EXIT

# Aguarda 2 segundos para a API subir
sleep 2

echo "=========================================="
echo "🌐 Iniciando WebUI (Streamlit)..."
echo "=========================================="

# Executa o WebUI
sh "$CURRENT_DIR/webui.sh"
