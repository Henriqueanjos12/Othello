import socket
import threading

clients = []  # Lista de clientes conectados
player_turn = 1  # Turno atual do jogador (1 ou 2)

# Tabuleiro inicial do jogo
board = [[" " for _ in range(8)] for _ in range(8)]
board[3][3], board[3][4] = "W", "B"
board[4][3], board[4][4] = "B", "W"


def broadcast(message):
    """
    Envia uma mensagem para todos os clientes conectados.
    """
    for client in clients:
        try:
            client.sendall(message.encode())
        except:
            clients.remove(client)


def board_to_string():
    """
    Converte o tabuleiro em uma string para exibição.
    """
    header = "  " + " ".join(map(str, range(8)))
    rows = [f"{i} " + " ".join(row) for i, row in enumerate(board)]
    return f"{header}\n" + "\n".join(rows)


def calculate_score():
    """
    Calcula o número de peças brancas e pretas no tabuleiro.
    """
    white = sum(row.count("W") for row in board)
    black = sum(row.count("B") for row in board)
    return white, black


def broadcast_score():
    """
    Envia o placar atual para todos os clientes conectados.
    """
    white, black = calculate_score()
    broadcast(f"SCORE {white} {black}")


def is_valid_move(player, x, y):
    """
    Verifica se uma jogada é válida.
    """
    opponent = "B" if player == "W" else "W"
    if board[x][y] != " ":
        return False

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        found_opponent = False

        while 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == opponent:
            nx += dx
            ny += dy
            found_opponent = True

        if found_opponent and 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == player:
            return True

    return False


def make_move(player, x, y):
    """
    Realiza uma jogada, alterando o estado do tabuleiro.
    """
    opponent = "B" if player == "W" else "W"
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    board[x][y] = player

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        path = []

        while 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == opponent:
            path.append((nx, ny))
            nx += dx
            ny += dy

        if path and 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == player:
            for px, py in path:
                board[px][py] = player

    broadcast(f"Current Board:\n{board_to_string()}\n")
    broadcast_score()  # Atualiza o placar imediatamente


def is_game_over():
    """
    Verifica se o jogo terminou.
    """
    for x in range(8):
        for y in range(8):
            if board[x][y] == " ":
                if is_valid_move("B", x, y) or is_valid_move("W", x, y):
                    return False
    return True


def handle_client(client, player_id):
    """
    Lida com a comunicação de um cliente.
    """
    global player_turn
    try:
        player_symbol = "B" if player_id == 1 else "W"
        client.sendall(f"You are Player {player_id} ({player_symbol})\n".encode())
        client.sendall(f"Current Board:\n{board_to_string()}\n".encode())
        broadcast_score()

        while True:
            message = client.recv(1024).decode()

            if not message:
                break

            if message == "QUIT":
                broadcast(f"Player {player_id} has left the game.")
                clients.remove(client)
                break
            elif message.startswith("MOVE"):
                if player_turn == player_id:
                    try:
                        _, x, y = message.split()
                        x, y = int(x), int(y)

                        if is_valid_move(player_symbol, x, y):
                            make_move(player_symbol, x, y)

                            player_turn = 3 - player_id

                            if is_game_over():
                                broadcast("Game over!")
                                white, black = calculate_score()
                                broadcast(f"Final Score: Branco {white} - Preto {black}")
                                for c in clients:
                                    c.close()
                                clients.clear()
                                break
                        else:
                            client.sendall("Invalid move. Try again.\n".encode())
                    except Exception as e:
                        client.sendall(f"Error processing move: {e}\n".encode())
                else:
                    client.sendall("It's not your turn.\n".encode())
            elif message.startswith("CHAT"):
                broadcast(f"Player {player_id}: {message[5:]}")
    except ConnectionResetError:
        broadcast(f"Player {player_id} has disconnected.")
        clients.remove(client)
    finally:
        client.close()


def start_server():
    """
    Inicia o servidor.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 12345))
    server.listen(2)
    print("Server started. Waiting for players...")

    while True:
        client, _ = server.accept()
        if len(clients) >= 2:
            client.sendall("Server full. Try again later.\n".encode())
            client.close()
            continue

        clients.append(client)
        threading.Thread(target=handle_client, args=(client, len(clients))).start()

        if len(clients) == 2:
            broadcast("Game started!")


if __name__ == "__main__":
    start_server()