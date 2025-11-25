import pygame
import random

def tint_image(image, color):
    base = image.convert_alpha()
    w, h = base.get_size()

    r, g, b = color
    tinted = pygame.Surface((w, h), pygame.SRCALPHA)

    for x in range(w):
        for y in range(h):
            pr, pg, pb, pa = base.get_at((x, y))
            if pa == 0:
                # Tam şeffaf piksel → ghost yok, dokunma
                continue
            # Ghost şeklinin olduğu yerde rengi değiştir, alpha'yı koru
            tinted.set_at((x, y), (r, g, b, pa))

    return tinted


class Ghost:
    """
    Pac-Man'deki hayaletleri temsil eden sınıf.
    Kendi hızına, rengine ve frightened (kaçma) moduna sahip.
    """

    def __init__(self, col, row, color,
                 tile_size,
                 hud_height,
                 wall_rects,
                 frightened_color=(0, 0, 255),
                 base_sprite=None):

        self.tile_size = tile_size
        self.hud_height = hud_height
        self.wall_rects = wall_rects

        # Tile koordinatından piksel koordinatına dönüşüm
        self.x = col * tile_size
        self.y = hud_height + row * tile_size
        self.home_x = self.x    # yenildiğinde döneceği konum
        self.home_y = self.y

        self.size = tile_size - 4
        self.base_color = color
        self.frightened_color = frightened_color
        self.state = "normal"   # "normal" veya "frightened" yani mavi mod

        # Hızlar
        self.speed_normal = 90
        self.speed_frightened = 60

        # Başlangıç yönü rastgele
        self.dir_x, self.dir_y = random.choice(
            [(1, 0), (-1, 0), (0, 1), (0, -1)]
        )

        # Sprite'lar
        self.sprite_normal = None
        self.sprite_fright = None
        self.sprite_current = None

        if base_sprite is not None:
            # Normal renkli sprite
            self.sprite_normal = tint_image(base_sprite, self.base_color)
            # Power modunda mavi sprite
            self.sprite_fright = tint_image(base_sprite, self.frightened_color)
            self.sprite_current = self.sprite_normal

    # Çarpışma yardımcı fonksiyonları
    def rect(self):
        #Ghost'un çarpışma rect'i.
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def collides_with_wall(self, x=None, y=None):
        #"Verilen (x, y) konumu duvara çarpıyor mu?
        if x is None:
            x = self.x
        if y is None:
            y = self.y

        r = pygame.Rect(x, y, self.size, self.size)
        return any(r.colliderect(w) for w in self.wall_rects)

    def possible_dirs(self):
        """
        Ghost'un bulunduğu tile'ın merkezine yakınsa
        gidebileceği yönleri (sağ, sol, yukarı, aşağı) döndürür.
        U-dönüş davranışını ghost house içinde/dışında farklı ele alıyoruz.
        """
        col = int(self.x // self.tile_size)
        row = int((self.y - self.hud_height) // self.tile_size)

        center_x = col * self.tile_size + self.tile_size / 2
        center_y = self.hud_height + row * self.tile_size + self.tile_size / 2
        dist = ((self.x + self.size / 2 - center_x) ** 2 +
                (self.y + self.size / 2 - center_y) ** 2) ** 0.5

        # Tile merkezinden çok uzaksa yeni yön seçme
        if dist > 3:
            return []

        dirs = []
        inside_house = (13 <= row <= 17)

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            # Ghost house dışındayken U-dönüşe izin vermeyelim
            if not inside_house:
                if dx == -self.dir_x and dy == -self.dir_y:
                    continue

            test_x = self.x + dx * (self.tile_size / 2)
            test_y = self.y + dy * (self.tile_size / 2)
            if not self.collides_with_wall(test_x, test_y):
                dirs.append((dx, dy))

        return dirs

    # Hareket & durum güncelleme
    def update(self, dt):
        """
        Ghost'un konumunu günceller.
        Ghost house içindeyken öncelik yukarı çıkıp labirente dağılmak olmalıdır buna göre yazdık.
        """
        speed = self.speed_normal if self.state == "normal" else self.speed_frightened

        # Satır hesabı (ghost house tespiti için)
        row = int((self.y - self.hud_height) // self.tile_size)
        inside_house = (13 <= row <= 16)

        # 1) Ghost house içindeysek kapıdan yukarı çıkmaya çalışsın
        if inside_house:
            test_x = self.x
            test_y = self.y - speed * dt
            if not self.collides_with_wall(test_x, test_y):
                # Kapı açıksa yukarı çıksın
                self.dir_x, self.dir_y = 0, -1
            else:
                # Kapalıysa normal yön seçimi
                dirs = self.possible_dirs()
                if dirs:
                    self.dir_x, self.dir_y = random.choice(dirs)
        else:
            # 2) Labirent içinde normal random hareket
            dirs = self.possible_dirs()
            if dirs:
                self.dir_x, self.dir_y = random.choice(dirs)

        # 3) Pozisyonu güncelleme kısmı
        old_x, old_y = self.x, self.y
        self.x += self.dir_x * speed * dt
        self.y += self.dir_y * speed * dt

        # Duvara çarparsa geri dön ve yönü ters çevir
        if self.collides_with_wall():
            self.x, self.y = old_x, old_y
            self.dir_x, self.dir_y = -self.dir_x, -self.dir_y

    def set_frightened(self):
        #Power pellet sonrası korkmuş moda geç (mavi).
        self.state = "frightened"
        if self.sprite_fright is not None:
            self.sprite_current = self.sprite_fright

    def set_normal(self):
        #Power süresi bitince normale dön.
        self.state = "normal"
        if self.sprite_normal is not None:
            self.sprite_current = self.sprite_normal

    def to_home(self):
        #Hayalet yenildiğinde ghost house'a geri gönderilsin.
        self.x, self.y = self.home_x, self.home_y
        self.set_normal()

    # ÇİZİM
    def draw(self, surf):
        #Ghost'u ekrana çizer.
        if self.sprite_current is not None:
            surf.blit(self.sprite_current, (int(self.x), int(self.y)))
        else:
            # Sprite yoksa basit renkli daire ile göster
            pygame.draw.circle(
                surf, self.base_color,
                (int(self.x + self.size / 2), int(self.y + self.size / 2)),
                self.size // 2
            )
