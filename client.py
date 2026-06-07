from pygame import *
import socket
import json
from threading import Thread

# --- PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг з Лаунчером")

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)
font_menu = font.Font(None, 50)

# --- СИСТЕМА СКІНІВ (Локальна) ---
# Замість реальних текстур використовуємо кольори, щоб код працював без скачування файлів.
# Ти можеш замінити кольори на image.load("шлях") пізніше.
SKINS = {
    "Зелений / Пурпур": {"p0": (0, 255, 0), "p1": (255, 0, 255), "ball": (255, 255, 255)},
    "Кіберпанк Неон": {"p0": (0, 240, 255), "p1": (255, 0, 128), "ball": (255, 255, 0)},
    "Ретро Класика": {"p0": (255, 255, 255), "p1": (255, 255, 255), "ball": (200, 200, 200)}
}
skin_names = list(SKINS.keys())
current_skin_idx = 0

# --- СТАН ИГРЫ ---
STATE_MENU = "menu"
STATE_SETTINGS = "settings"
STATE_GAME = "game"
current_state = STATE_MENU

# Сетевые переменные
client = None
my_id = None
game_state = {}
buffer = ""
game_over = False
you_winner = None

# --- СЕРВЕР ---
def connect_to_server():
    global my_id, game_state, buffer, client
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 8080)) 
        buffer = ""
        game_state = {}
        my_id = int(client.recv(24).decode())
        Thread(target=receive, daemon=True).start()
        return True
    except:
        return False

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- ФУНКЦІЇ МАЛЮВАННЯ КНОПОК ---
def draw_button(text, x, y, w, h, hover_color=(100, 100, 100), default_color=(50, 50, 50)):
    mouse_pos = mouse.get_pos()
    rect_btn = Rect(x, y, w, h)
    
    if rect_btn.collidepoint(mouse_pos):
        draw.rect(screen, hover_color, rect_btn)
        is_hovered = True
    else:
        draw.rect(screen, default_color, rect_btn)
        is_hovered = True # Для простоты логики возвращаем коодинаты
        
    draw.rect(screen, (255, 255, 255), rect_btn, 2)
    txt = font_main.render(text, True, (255, 255, 255))
    screen.blit(txt, (x + (w - txt.get_width()) // 2, y + (h - txt.get_height()) // 2))
    return rect_btn

# --- ГОЛОВНИЙ ЦИКЛ ---
while True:
    events = event.get()
    for e in events:
        if e.type == QUIT:
            exit()
            
        if e.type == MOUSEBUTTONDOWN and e.button == 1:
            if current_state == STATE_MENU:
                if btn_play.collidepoint(e.pos):
                    # Пытаемся подключиться только при нажатии "Грати"
                    if connect_to_server():
                        current_state = STATE_GAME
                    else:
                        print("Сервер не знайдено! Запусти спочатку server.py")
                elif btn_settings.collidepoint(e.pos):
                    current_state = STATE_SETTINGS
                elif btn_exit.collidepoint(e.pos):
                    exit()
                    
            elif current_state == STATE_SETTINGS:
                if btn_next_skin.collidepoint(e.pos):
                    current_state_idx = (current_skin_idx + 1) % len(skin_names)
                    current_skin_idx = current_state_idx
                elif btn_back.collidepoint(e.pos):
                    current_state = STATE_MENU

    # --- ЛОГІКА ЕКРАНІВ ---
    if current_state == STATE_MENU:
        screen.fill((15, 15, 25))
        title = font_win.render("ПІНГ-ПОНГ ЛАУНЧЕР", True, (0, 255, 200))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        
        btn_play = draw_button("Грати", WIDTH // 2 - 100, 220, 200, 50)
        btn_settings = draw_button("Налаштування скінів", WIDTH // 2 - 150, 300, 300, 50)
        btn_exit = draw_button("Вихід", WIDTH // 2 - 100, 380, 200, 50)

    elif current_state == STATE_SETTINGS:
        screen.fill((25, 20, 30))
        title = font_menu.render("Магазин Скінів (Безкоштовно)", True, (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        
        # Показываем текущий скин
        active_skin_name = skin_names[current_skin_idx]
        skin_txt = font_main.render(f"Обрано: {active_skin_name}", True, (255, 255, 255))
        screen.blit(skin_txt, (WIDTH // 2 - skin_txt.get_width() // 2, 200))
        
        # Демонстрация цветов скина
        colors = SKINS[active_skin_name]
        draw.rect(screen, colors["p0"], (WIDTH // 2 - 60, 260, 20, 60))
        draw.rect(screen, colors["p1"], (WIDTH // 2 + 40, 260, 20, 60))
        draw.circle(screen, colors["ball"], (WIDTH // 2, 290), 10)
        
        btn_next_skin = draw_button("Змінити Скін", WIDTH // 2 - 100, 380, 200, 50)
        btn_back = draw_button("Назад в Меню", WIDTH // 2 - 100, 460, 200, 50)

    elif current_state == STATE_GAME:
        if "countdown" in game_state and game_state["countdown"] > 0:
            screen.fill((0, 0, 0))
            countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
            screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
            display.update()
            continue

        if "winner" in game_state and game_state["winner"] is not None:
            screen.fill((20, 20, 20))
            if you_winner is None:
                you_winner = game_state["winner"] == my_id

            text = "Ти переміг!" if you_winner else "Пощастить наступним разом!"
            win_text = font_win.render(text, True, (255, 215, 0))
            screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            
            text_restart = font_main.render('Перезапусти лаунчер для нової гри', True, (150, 150, 150))
            screen.blit(text_restart, text_restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))
            display.update()
            continue

        if game_state:
            screen.fill((30, 30, 30))
            
            # --- ЗАСТОСУВАННЯ ОБРАНОГО СКІНУ ---
            current_colors = SKINS[skin_names[current_skin_idx]]
            
            # Ракетка левая (Игрок 0)
            draw.rect(screen, current_colors["p0"], (20, game_state['paddles']['0'], 20, 100))
            # Ракетка правая (Игрок 1)
            draw.rect(screen, current_colors["p1"], (WIDTH - 40, game_state['paddles']['1'], 20, 100))
            # Мяч
            draw.circle(screen, current_colors["ball"], (game_state['ball']['x'], game_state['ball']['y']), 10)
            
            score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH // 2 - 25, 20))
        else:
            screen.fill((10, 10, 15))
            waiting_text = font_main.render("Очікування другого гравця...", True, (255, 255, 255))
            screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2))

        keys = key.get_pressed()
        if keys[K_w]:
            client.send(b"UP")
        elif keys[K_s]:
            client.send(b"DOWN")

    display.update()
    clock.tick(60)