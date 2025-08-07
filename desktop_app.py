import threading
import os
import sys
import webbrowser

# Adiciona o diretório pai ao sys.path para que 'app' possa ser importado
# Isso é crucial para PyInstaller encontrar o módulo 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Define a porta para o aplicativo Flask
# É bom usar uma porta que não seja comumente usada ou uma porta aleatória
# Para simplicidade, vamos manter 8000 por enquanto, mas você pode mudar.
FLASK_PORT = 8000
FLASK_HOST = '127.0.0.1' # Apenas acessível localmente

def start_flask_app():
    """Função para iniciar o aplicativo Flask."""
    # Certifique-se de que o modo de depuração esteja desativado para o executável
    # A sua configuração em app/__init__.py já lida com isso via FLASK_DEBUG env var.
    # Apenas garanta que FLASK_DEBUG não esteja definido como 'true' ao construir.
    app = create_app()
    print(f"Iniciando Flask app em http://{FLASK_HOST}:{FLASK_PORT}")
    # Usamos app.run() aqui porque é mais simples para um contexto de desktop
    # do que Gunicorn em uma thread.
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Inicia o Flask em uma thread separada
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True # Permite que a thread seja encerrada quando o programa principal termina
    flask_thread.start()

    # Dá um pequeno tempo para o Flask iniciar
    import time
    time.sleep(3) # Ajuste conforme necessário

    # Abre o navegador padrão para a URL do aplicativo Flask
    webbrowser.open(f'http://{FLASK_HOST}:{FLASK_PORT}')

    # Mantém o programa principal rodando para que o servidor Flask continue ativo
    # até que o usuário o encerre manualmente (ex: Ctrl+C no terminal)
    flask_thread.join()
