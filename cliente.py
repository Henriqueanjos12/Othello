import socket
import threading
import tkinter as tk

def send_chat(event=None):
    """
    Envia uma mensagem de chat ao servidor.
    """
    message = chat_entry.get().strip()
    if message:
        try:
            client_socket.sendall(f"CHAT {message}".encode())
            chat_entry.delete(0, tk.END)
        except (ConnectionResetError, BrokenPipeError):
            display_message("Erro: conexão com o servidor perdida.")

def make_move(row, col):
    """
    Envia uma jogada ao servidor.
    """
    if not validate_move(row, col):
        display_message("Jogada inválida. Tente novamente.")
        return

    try:
        client_socket.sendall(f"MOVE {row} {col}".encode())
    except (ConnectionResetError, BrokenPipeError):
        display_message("Erro: conexão com o servidor perdida.")

def validate_move(row, col):
    """
    Valida se a jogada é permitida (somente no cliente).
    """
    # Verifica se o botão ainda está disponível (não jogado)
    if board_buttons[row][col].cget("state") == tk.DISABLED:
        return False
    return True

def receive_messages():
    """
    Recebe mensagens do servidor e atualiza a interface.
    """
    while True:
        try:
            message = client_socket.recv(1024).decode()
            print(f"Mensagem recebida: {message}")  # Log para depuração
            if not message:
                break

            if message.startswith("CHAT"):
                display_message(message[5:])
            elif message.startswith("MOVE"):
                _, row, col, color = message.split()
                update_board(int(row), int(col), color)
            elif message.startswith("SCORE"):
                _, white, black = message.split()
                print(f"Atualizando placar: Branco={white}, Preto={black}")  # Log de placar
                update_score(int(white), int(black))
            elif message.startswith("STATUS"):
                display_message(message[7:])
            else:
                display_message(message)
        except Exception as e:
            display_message(f"Erro ao receber mensagem do servidor: {e}")
            break


def display_message(message):
    """
    Exibe mensagens no chat.
    """
    chat_text.config(state=tk.NORMAL)
    chat_text.insert(tk.END, f"{message}\n")
    chat_text.config(state=tk.DISABLED)

def update_board(row, col, color):
    """
    Atualiza o tabuleiro com a jogada recebida e altera a cor do botão.
    """
    color_mapping = {
        "W": "white",
        "B": "black"
    }
    board_buttons[row][col].config(
        text=color,
        bg=color_mapping.get(color, "gray"),  # Use 'gray' como padrão para erros
        state=tk.DISABLED  # Desabilita o botão após a jogada
    )

def update_score(white, black):
    """
    Atualiza o placar exibido na interface.
    """
    score_label.config(text=f"Placar: Branco {white} - Preto {black}")

def on_closing():
    """
    Fecha o cliente e desconecta do servidor.
    """
    try:
        client_socket.close()
    except:
        pass
    root.destroy()

# Configuração da interface Tkinter
root = tk.Tk()
root.title("Othello")

# Área do chat
chat_frame = tk.Frame(root)
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
chat_text = tk.Text(chat_frame, state=tk.DISABLED, width=30)
chat_text.pack(fill=tk.BOTH, expand=True)
chat_entry = tk.Entry(chat_frame)
chat_entry.pack(fill=tk.X)
chat_entry.bind("<Return>", send_chat)

# Tabuleiro do jogo
board_frame = tk.Frame(root)
board_frame.pack(side=tk.RIGHT)
board_buttons = [[None for _ in range(8)] for _ in range(8)]
for row in range(8):
    for col in range(8):
        button = tk.Button(board_frame, width=4, height=2, command=lambda r=row, c=col: make_move(r, c))
        button.grid(row=row, column=col)
        board_buttons[row][col] = button

# Placar
score_frame = tk.Frame(root)
score_frame.pack(side=tk.TOP, fill=tk.X)
score_label = tk.Label(score_frame, text="Placar: Branco 2 - Preto 2")
score_label.pack()

# Configuração do cliente socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect(("localhost", 12345))
except ConnectionRefusedError:
    print("Servidor indisponível. Verifique se ele está rodando e tente novamente.")
    exit(1)

threading.Thread(target=receive_messages, daemon=True).start()

# Configuração para fechar o cliente corretamente
root.protocol("WM_DELETE_WINDOW", on_closing)

# Inicia a interface Tkinter
root.mainloop()
