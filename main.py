import pygame
import sys
import random
from pygame import mixer
from pacman import Pacman
from ghost import Ghost

pygame.init()
mixer.init()

# GENEL AYARLAR
TILE_SIZE = 24
GRID_WIDTH = 28
GRID_HEIGHT = 31

HUD_HEIGHT = 40  # üstte skor / süre barı

SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = HUD_HEIGHT + GRID_HEIGHT * TILE_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man (Utility Agent)")

clock = pygame.time.Clock()

# Renkler
BLACK = (0, 0, 0)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 0)
WHITE = (240, 240, 240)
GREY = (40, 40, 40)
RED = (220, 0, 0)
PINK = (255, 105, 180)
CYAN = (0, 200, 200)
ORANGE = (255, 165, 0)
FRIGHT_BLUE = (0, 0, 255)

# Yazı tipleri
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 48)

# Menü için daha büyük fontlar
menu_title_font = pygame.font.SysFont(None, 64)  # başlık
menu_sub_font   = pygame.font.SysFont(None, 32)  # alt başlık
menu_opt_font   = pygame.font.SysFont(None, 28)  # seçenekler, info

POWER_DURATION = 7.0  # power pellet süresi saniye cinsinden


# SES DOSYALARI
chomp_sound      = mixer.Sound("assets/sounds/chomp.wav")       # küçük nokta
power_sound      = mixer.Sound("assets/sounds/power.wav")       # büyük nokta
eat_ghost_sound  = mixer.Sound("assets/sounds/eat_ghost.wav")   # hayalet yeme
death_sound      = mixer.Sound("assets/sounds/death.wav")       # ölüm
start_sound      = mixer.Sound("assets/sounds/start.wav")       # yeni oyun

# Ses seviyeleri
chomp_sound.set_volume(0.4)
power_sound.set_volume(0.5)
eat_ghost_sound.set_volume(0.7)
death_sound.set_volume(0.7)
start_sound.set_volume(0.6)


# PAC-MAN SPRITE YÜKLEME
pacman_images = None
try:
    base_img = pygame.image.load("assets/pacman_right.png").convert_alpha()
    base_img = pygame.transform.scale(base_img, (TILE_SIZE - 4, TILE_SIZE - 4))
    pacman_images = {
        "RIGHT": base_img,
        "LEFT": pygame.transform.flip(base_img, True, False),
        "UP": pygame.transform.rotate(base_img, 90),
        "DOWN": pygame.transform.rotate(base_img, -90),
    }
except Exception as e:
    pacman_images = None


# GHOST SPRITE YÜKLEME
ghost_base_sprite = None
try:
    gimg = pygame.image.load("assets/ghost.png").convert_alpha()

    # PNG'nin arka planını şeffaf yapıyoruz
    w, h = gimg.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = gimg.get_at((x, y))
            if r > 230 and g > 230 and b > 230: 
                gimg.set_at((x, y), (r, g, b, 0))

    # Labirentteki tile boyutuna göre ölçekle
    gimg = pygame.transform.smoothscale(gimg, (TILE_SIZE - 4, TILE_SIZE - 4))
    ghost_base_sprite = gimg
except Exception as e:
    print("Ghost sprite yüklenemedi, daire kullanılacak:", e)

# LEVEL MAP (pac-man haritasi)
LEVEL_MAP = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "######.##..........##.######",
    "######.##.###--###.##.######",
    "######.##.#      #.##.######",
    "######.##.#      #.##.######",
    "######.##.#      #.##.######",
    "######.##.#      #.##.######",
    "######.##.########.##.######",
    "######.##..........##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#..........................#",
    "#.##########.##.##########.#",
    "#..........................#",
    "#o########################o#",
    "############################"
]

# grid = 2D list formu
grid = [list(row) for row in LEVEL_MAP]

# Duvarların rect listesi (çarpışma için)
wall_rects = []
for r, row in enumerate(grid):
    for c, t in enumerate(row):
        if t == "#":
            wall_rects.append(
                pygame.Rect(c * TILE_SIZE, HUD_HEIGHT + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            )


def draw_wall(surface, row, col):
    #Labirentteki duvar çizimi
    x = col * TILE_SIZE
    y = HUD_HEIGHT + row * TILE_SIZE

    inset = 4
    thick = 3

    up = (row > 0 and grid[row - 1][col] == '#')
    down = (row < GRID_HEIGHT - 1 and grid[row + 1][col] == '#')
    left = (col > 0 and grid[row][col - 1] == '#')
    right = (col < GRID_WIDTH - 1 and grid[row][col + 1] == '#')

    if not up:
        pygame.draw.line(surface, BLUE, (x, y + inset), (x + TILE_SIZE, y + inset), thick)
    if not down:
        pygame.draw.line(surface, BLUE, (x, y + TILE_SIZE - inset), (x + TILE_SIZE, y + TILE_SIZE - inset), thick)
    if not left:
        pygame.draw.line(surface, BLUE, (x + inset, y), (x + inset, y + TILE_SIZE), thick)
    if not right:
        pygame.draw.line(surface, BLUE, (x + TILE_SIZE - inset, y), (x + TILE_SIZE - inset, y + TILE_SIZE), thick)


# Utility-based Agent
def agent_choose_direction(pacman, ghosts):
    """
    Utility-temelli yön seçimi:
    ANA HEDEFLER:
    1) Her zaman ÖNCE hayatta kal (NORMAL + POWER modda)
    2) En kısa ve mantıklı yollardan pellet'leri yiyip oyunu bitirmeye çalış
    3) Power pellet varsa ve güvenliyse ona yönel
    4) POWER modda ise hayaletleri yeme eğilimi (yakındaysa + güvenliyse yenir)
    Ekstra:
    - Boş ve uzun koridorlara girip zaman kaybetme eğilimini azaltır
    - Loop history ile aynı bölgede dönüp durmayı azaltır
    """

    # Pac-Man'in merkez koordinatları (piksel cinsinden)
    px = pacman.x + pacman.size / 2
    py = pacman.y + pacman.size / 2

    # Grid (satır/sütun) koordinatı
    col = int(px // TILE_SIZE)
    row = int((py - HUD_HEIGHT) // TILE_SIZE)

    cur_dx, cur_dy = pacman.dir_x, pacman.dir_y
    cur_dir = (cur_dx, cur_dy)
    reverse_dir = (-cur_dx, -cur_dy)

    # Ekran dışı durum
    if not (0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH):
        return cur_dir

    # LOOP HISTORY (dönüp durmayı engellemek için)
    if not hasattr(pacman, "last_positions"):
        pacman.last_positions = []          # sadece (col,row) tutacağız

    pacman.last_positions.append((col, row))
    # Son 20 adımı saklıyoruz(loop'ları görebilmesi icin)
    if len(pacman.last_positions) > 20:
        pacman.last_positions.pop(0)

    # Tile merkezine çok uzaksa, önce merkeze yaklaş (yumuşak bir kilit)
    center_x = col * TILE_SIZE + TILE_SIZE / 2
    center_y = HUD_HEIGHT + row * TILE_SIZE + TILE_SIZE / 2
    dist_to_center = ((px - center_x) ** 2 + (py - center_y) ** 2) ** 0.5
    if dist_to_center > 3 and cur_dir != (0, 0):
        # Şu anki yön fena değil, merkezlenme bitmeden yön değiştirme
        return cur_dir

    # Olası yönler ve legal yönler
    all_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    legal_dirs = []

    for dx, dy in all_dirs:
        test_col = col + dx
        test_row = row + dy

        # Grid sınırı
        if not (0 <= test_row < GRID_HEIGHT and 0 <= test_col < GRID_WIDTH):
            continue
        # Duvarsa geçersiz
        if grid[test_row][test_col] == '#':
            continue
        # Pac-Man fiziksel olarak o yöne adım atabiliyor mu kontrol ediyoruz
        if not pacman.can_move(dx, dy):
            continue

        legal_dirs.append((dx, dy))

    if not legal_dirs:
        # Hiçbir yere gidemiyorsa şu anki yönü koru
        return cur_dir

    # 180° ani geri dönüşleri mümkünse engelliyoruz aynı yönü gidip gelmemesi icin
    candidate_dirs = [d for d in legal_dirs if d != reverse_dir]
    if not candidate_dirs:
        candidate_dirs = legal_dirs

    best_dir = candidate_dirs[0]
    best_score = -1e9

    # Haritadaki pellet & power pellet listeleri
    pellets = [
        (c, r)
        for r in range(GRID_HEIGHT)
        for c in range(GRID_WIDTH)
        if grid[r][c] == '.'
    ]
    powers = [
        (c, r)
        for r in range(GRID_HEIGHT)
        for c in range(GRID_WIDTH)
        if grid[r][c] == 'o'
    ]

    # Yardımcı: bir yönde ileriye bakıp
    #           kaç adım içinde kaç yem/power var?
    def pellets_ahead(start_c, start_r, dx, dy, steps=6):
        p_count = 0
        pow_count = 0
        c, r = start_c, start_r
        for _ in range(steps):
            c += dx
            r += dy
            if not (0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH):
                break
            if grid[r][c] == '#':
                break
            if grid[r][c] == '.':
                p_count += 1
            elif grid[r][c] == 'o':
                pow_count += 1
        return p_count, pow_count

    # Her aday yönde utility fayda hesabı
    for dx, dy in candidate_dirs:
        score = 0.0
        test_col = col + dx
        test_row = row + dy

        # 1) Hayalet mesafeleri
        nearest_danger = 9999  # normal (tehlikeli) hayaletler
        nearest_fright = 9999  # frightened (yenebilir) hayaletler

        for g in ghosts:
            gx = g.x + g.size / 2
            gy = g.y + g.size / 2

            ghost_col = int(gx // TILE_SIZE)
            ghost_row = int((gy - HUD_HEIGHT) // TILE_SIZE)

            dist = abs(ghost_col - test_col) + abs(ghost_row - test_row)

            if g.state == "frightened":
                if dist < nearest_fright:
                    nearest_fright = dist
            else:
                if dist < nearest_danger:
                    nearest_danger = dist

        if nearest_danger == 9999:
            nearest_danger = 9999.0
        if nearest_fright == 9999:
            nearest_fright = 9999.0

        # 1.a) NORMAL mod: hayatta kalma + kaçış
        if not pacman.power_mode:
            # Hayalet 10 tile'dan yakınsa agresif kaç
            if nearest_danger < 10:
                # Uzaklık azaldıkça ceza çok büyür
                score -= 2600.0 / (nearest_danger + 0.1)
            # Genel olarak hayaletten uzak olmak iyi, ama aşırı da abartmıyoruz
            score += nearest_danger * 1.2


        # 1.b) POWER mod: hayalet yeme İKİNCİ planda
        else:
            # Sadece çok yakın frightened hayalet varsa bonus ver
            # (yolun üstündeyse / yakınsa ye, yoksa yemlere odaklan)
            if nearest_fright < 4:
                score += 550.0 / (nearest_fright + 0.1)

            # POWER modda bile çok tehlikeli pozisyonlardan kaçın
            if nearest_danger < 3:
                score -= 600.0 / (nearest_danger + 0.1)

        # 2) Yem & power pellet utility
        #    Asıl amaç: tüm pellet'leri hızlı bir şekilde bitirmek
        # Her durumda pellet toplamak ana hedef:
        pellet_weight = 55.0 if not pacman.power_mode else 45.0

        # Power pellet:
        # - NORMAL modda: yüksek öncelik (kaçış/saldırı avantajı)
        # - POWER modda: neredeyse önemsiz (süre zaten çalışıyor)
        power_weight = 350.0 if not pacman.power_mode else 10.0

        # En yakın pellet'e göre puan
        if pellets:
            pellet_dist = min(
                abs(cx - test_col) + abs(ry - test_row) for cx, ry in pellets
            )
            if pellet_dist < 1:
                pellet_dist = 1
            score += pellet_weight / pellet_dist

        # En yakın power pellet'e göre puan
        if powers:
            power_dist = min(
                abs(cx - test_col) + abs(ry - test_row) for cx, ry in powers
            )
            if power_dist < 1:
                power_dist = 1
            score += power_weight / power_dist

        # 3) Koridor boşluğu (tamamen boş yollardan kaçınma)
        p_ahead, pow_ahead = pellets_ahead(col, row, dx, dy, steps=6)

        # İleride hiç yem yok, power da yoksa → zaman kaybı gibi davran
        if p_ahead == 0 and pow_ahead == 0:
            score -= 90.0

        # 4) Aynı yönde devam etme bonusu
        #    (gereksiz zigzag'ları azaltır)
        if (dx, dy) == cur_dir:
            score += 5

        # 5) LOOP CEZASI (aynı bölgede
        #    dönüp durmayı azaltmak için)
        if (test_col, test_row) in pacman.last_positions:
            score -= 200.0

        # En iyi yönü güncelle
        if score > best_score:
            best_score = score
            best_dir = (dx, dy)

    return best_dir


# GLOBAL STATE
PLAYER_TYPE = None # "human" veya "agent"
pacman = None
ghosts = []
start_time = 0
game_over = False
GAME_STATE = "menu"

# Son oyun sonuçlarını tutan sözlük
last_results = {
    "human_score": None,
    "human_time": None,
    "agent_score": None,
    "agent_time": None,
    "winner": ""  # "Human", "Agent" veya "Berabere"
}


# RESET / YENİ OYUN
def reset_game(mode):
    """
    Yeni oyun başlatır.
    mode: "human" → klavye ile,
          "agent" → utility-based Pac-Man
    """
    global pacman, ghosts, grid, game_over, start_time, PLAYER_TYPE

    PLAYER_TYPE = mode

    # Haritayı sıfırla (tüm pellet'ler geri gelsin)
    grid = [list(row) for row in LEVEL_MAP]

    # Pac-Man başlangıç konumu
    pacman = Pacman(1, 1, TILE_SIZE, HUD_HEIGHT, grid, wall_rects,
                    pacman_images=pacman_images, color=YELLOW)

    # Ghost'lar ghost house içinde başlıyor
    ghosts = [
        Ghost(13, 15, RED,    TILE_SIZE, HUD_HEIGHT, wall_rects, FRIGHT_BLUE, base_sprite=ghost_base_sprite),
        Ghost(14, 15, CYAN,   TILE_SIZE, HUD_HEIGHT, wall_rects, FRIGHT_BLUE, base_sprite=ghost_base_sprite),
        Ghost(13, 16, PINK,   TILE_SIZE, HUD_HEIGHT, wall_rects, FRIGHT_BLUE, base_sprite=ghost_base_sprite),
        Ghost(14, 16, ORANGE, TILE_SIZE, HUD_HEIGHT, wall_rects, FRIGHT_BLUE, base_sprite=ghost_base_sprite),
    ]

    game_over = False
    start_time = pygame.time.get_ticks()

    # Yeni oyun sesi
    start_sound.play()


# ÇİZİM FONKSİYONLARI
def draw_grid(surface):
    """Labirenti, pellet'leri ve üstteki skor/süre barını çizer."""
    surface.fill(BLACK)

    # Üst gri bar
    pygame.draw.rect(surface, GREY, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))

    # Skor ve süre
    elapsed = (pygame.time.get_ticks() - start_time) // 1000
    s1 = font.render(f"Skor: {pacman.score}", True, WHITE)
    s2 = font.render(f"Süre: {elapsed} sn", True, WHITE)
    surface.blit(s1, (10, 10))
    surface.blit(s2, (SCREEN_WIDTH - 150, 10))

    # Harita içi pellet ve power pellet'ler
    for r, row in enumerate(grid):
        for c, t in enumerate(row):
            if t == "#":
                draw_wall(surface, r, c)
            else:
                x = c * TILE_SIZE
                y = HUD_HEIGHT + r * TILE_SIZE
                if t == ".":
                    pygame.draw.circle(surface, WHITE, (x + 12, y + 12), 3)
                elif t == "o":
                    pygame.draw.circle(surface, WHITE, (x + 12, y + 12), 6)


def draw_menu(surface):
    #Ana menü ekranı cizimi
    surface.fill((10, 15, 36))  # koyu lacivert arka plan

    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    # Başlık ve alt başlık
    title = menu_title_font.render("Pac-Man", True, (255, 215, 0))
    sub   = menu_sub_font.render("Utility-based Agent Projesi", True, (0, 255, 200))

    # Seçenekler
    opt1 = menu_opt_font.render("1 - Human Player (klavye)", True, (255, 185, 100))
    opt2 = menu_opt_font.render("2 - Agent Player (yapay zeka)", True, (255, 140, 200))
    info = menu_opt_font.render("ESC - Çıkış", True, (220, 220, 255))

    surface.blit(title, (center_x - title.get_width() // 2, center_y - 120))
    surface.blit(sub,   (center_x - sub.get_width()   // 2, center_y - 70))

    surface.blit(opt1,  (center_x - opt1.get_width()  // 2, center_y))
    surface.blit(opt2,  (center_x - opt2.get_width()  // 2, center_y + 40))

    surface.blit(info,  (center_x - info.get_width()  // 2, center_y + 100))

    # Son karşılaştırma tablosu (her iki mod da en az bir kez oynandıysa)
    if last_results["human_score"] is not None and last_results["agent_score"] is not None:
        res_title = menu_opt_font.render("Son Karşılaştırma Sonucu:", True, (230, 230, 255))
        surface.blit(res_title, (center_x - res_title.get_width() // 2, center_y + 150))

        human_line = menu_opt_font.render(
            f"Human  | Skor: {last_results['human_score']}, Süre: {last_results['human_time']} sn",
            True, (140, 200, 255)
        )
        agent_line = menu_opt_font.render(
            f"Agent  | Skor: {last_results['agent_score']}, Süre: {last_results['agent_time']} sn",
            True, (255, 180, 120)
        )
        surface.blit(human_line, (center_x - human_line.get_width() // 2, center_y + 185))
        surface.blit(agent_line, (center_x - agent_line.get_width() // 2, center_y + 220))

        # Kazanan rengi
        win_color = (255, 255, 255)
        if last_results["winner"] == "Human":
            win_color = (140, 200, 255)
        elif last_results["winner"] == "Agent":
            win_color = (255, 180, 120)

        winner_text = menu_opt_font.render(f"Kazanan: {last_results['winner']}", True, win_color)
        surface.blit(winner_text, (center_x - winner_text.get_width() // 2, center_y + 255))


# MAIN GAME LOOP
def main():
    global GAME_STATE, game_over

    GAME_STATE = "menu"

    while True:
        dt = clock.tick(60) / 1000  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Menüdeyken tuşlar
            if GAME_STATE == "menu" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key in (pygame.K_1, pygame.K_KP1):
                    reset_game("human")
                    GAME_STATE = "playing"
                if event.key in (pygame.K_2, pygame.K_KP2):
                    reset_game("agent")
                    GAME_STATE = "playing"

            # Oyun bittiğinde ENTER ile menüye dön
            if GAME_STATE == "playing" and game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    GAME_STATE = "menu"

        # MENU STATE
        if GAME_STATE == "menu":
            draw_menu(screen)

        # PLAYING STATE
        elif GAME_STATE == "playing":
            keys = pygame.key.get_pressed()

            if not game_over:
                #1) Kontrol (human veya agent)
                if PLAYER_TYPE == "human":
                    pacman.set_direction_from_keys(keys)
                elif PLAYER_TYPE == "agent":
                    dx, dy = agent_choose_direction(pacman, ghosts)
                    pacman.next_dir_x = dx
                    pacman.next_dir_y = dy

                    # Agent için sprite yönünü güncelle
                    if   (dx, dy) == (1, 0):
                        pacman.dir_name = "RIGHT"
                    elif (dx, dy) == (-1, 0):
                        pacman.dir_name = "LEFT"
                    elif (dx, dy) == (0, -1):
                        pacman.dir_name = "UP"
                    elif (dx, dy) == (0, 1):
                        pacman.dir_name = "DOWN"

                # 2) Pac-Man update + sesler 
                old_score = pacman.score
                pacman.update(dt)
                score_diff = pacman.score - old_score

                # Power pellet yendiyse
                if pacman.just_ate_power:
                    pacman.power_mode = True
                    pacman.power_timer = POWER_DURATION
                    for g in ghosts:
                        g.set_frightened()
                    power_sound.play()
                else:
                    # Normal pellet ile skor arttıysa chomp sesi
                    if score_diff > 0:
                        chomp_sound.play()

                # Power süresi bittiğinde hayaletler normale dönsün
                if not pacman.power_mode:
                    for g in ghosts:
                        if g.state != "normal":
                            g.set_normal()

                #3) Ghost update
                for g in ghosts:
                    g.update(dt)

                #4) Pac-Man – Ghost çarpışma kontrolü 
                for g in ghosts:
                    if pacman.rect().colliderect(g.rect()):

                        # Power modunda → hayalet yenir
                        if pacman.power_mode and g.state == "frightened":
                            eat_ghost_sound.play()
                            pacman.score += 200
                            g.to_home()

                        # Normal mod → Pac-Man ölür
                        else:
                            death_sound.play()
                            pacman.alive = False
                            game_over = True

                            # Oyun süresini hesapla
                            elapsed_ms = pygame.time.get_ticks() - start_time
                            elapsed_sec = int(elapsed_ms / 1000)

                            # Sonuçları kaydet (human / agent)
                            if PLAYER_TYPE == "human":
                                last_results["human_score"] = pacman.score
                                last_results["human_time"] = elapsed_sec
                            elif PLAYER_TYPE == "agent":
                                last_results["agent_score"] = pacman.score
                                last_results["agent_time"] = elapsed_sec

                            # Kazananı belirle (iki mod da oynandıysa)
                            human_score = last_results["human_score"]
                            agent_score = last_results["agent_score"]
                            human_time = last_results["human_time"]
                            agent_time = last_results["agent_time"]

                            if human_score is not None and agent_score is not None:
                                if human_score > agent_score:
                                    last_results["winner"] = "Human"
                                elif agent_score > human_score:
                                    last_results["winner"] = "Agent"
                                else:
                                    # Skor eşitse süreye bak
                                    if human_time is not None and agent_time is not None:
                                        if 0 < human_time < agent_time:
                                            last_results["winner"] = "Human"
                                        elif 0 < agent_time < human_time:
                                            last_results["winner"] = "Agent"
                                        else:
                                            last_results["winner"] = "Berabere"
                                    else:
                                        last_results["winner"] = "Berabere"
                            else:
                                # Yalnızca tek taraf oynadıysa kazanan göstermiyoruz
                                last_results["winner"] = ""

                        break  # Tek çarpışma yeterli

            # 5) Oyun ekranını çizelim
            draw_grid(screen)
            pacman.draw(screen)
            for g in ghosts:
                g.draw(screen)

            # Game Over yazısı
            if game_over:
                text = big_font.render("GAME OVER", True, (255, 80, 80))
                info = font.render("Menüye dönmek için ENTER", True, (200, 200, 255))

                screen.blit(
                    text,
                    (SCREEN_WIDTH // 2 - text.get_width() // 2,
                     SCREEN_HEIGHT // 2 - text.get_height() // 2)
                )
                screen.blit(
                    info,
                    (SCREEN_WIDTH // 2 - info.get_width() // 2,
                     SCREEN_HEIGHT // 2 + 40)
                )

        pygame.display.flip()

if __name__ == "__main__":
    main()
