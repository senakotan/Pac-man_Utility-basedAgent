import pygame

class Pacman:
    """
    Bu sınıf bizim Pac-Man karakterimizi temsil ediyor.
    - Konum, hız, yön bilgisi
    - Skor ve power-mode gibi durumlar
    - Çarpışma ve hareket fonksiyonlarını burada yazdık.
    """
    def __init__(self, col, row,
                 tile_size,
                 hud_height,
                 grid,
                 wall_rects,
                 pacman_images=None,
                 color=(255, 255, 0)):

        # Harita / çizim parametreleri
        self.tile_size = tile_size              
        self.hud_height = hud_height           
        self.grid = grid                        
        self.wall_rects = wall_rects            
        self.pacman_images = pacman_images     
        self.color = color                      

        # Pac-Man başlangıç pozisyonu (tile → pixel)
        self.x = col * tile_size
        self.y = hud_height + row * tile_size
        self.size = tile_size - 4               
        self.speed = 120                      

        # Hareket yönleri
        self.dir_x = 0          
        self.dir_y = 0          
        self.next_dir_x = 0    
        self.next_dir_y = 0     
        self.dir_name = "RIGHT" # Sprite için yön ismi

        # Oyun durumları
        self.score = 0         
        self.alive = True       
        self.power_mode = False 
        self.power_timer = 0.0  
        self.just_ate_power = False  


    # Yardımcı fonksiyonlar
    def center_on_grid(self):
        """
        Pac-Man bazen duvarla çarpışırken tile ortasından kayabiliyor.
        Bu fonksiyon Pac-Man'i en yakın tile merkezine hizalıyor.
        """
        col = int((self.x + self.size / 2) // self.tile_size)
        row = int(((self.y + self.size / 2) - self.hud_height) // self.tile_size)

        self.x = col * self.tile_size + (self.tile_size - self.size) / 2
        self.y = self.hud_height + row * self.tile_size + (self.tile_size - self.size) / 2

    def rect(self):
        """Pac-Man'in çarpışma dikdörtgenini döndürür."""
        return pygame.Rect(self.x, self.y, self.size, self.size)

    # Kullanıcıdan gelen yön bilgisi (HUMAN mode)
    def set_direction_from_keys(self, keys):
        """
        Klavyeden gelen tuşlara göre bir SONRAKİ yön belirlenir.
        Hemen dönmüyor, can_move() kontrolü yapıp uygunsa o yöne geçiyoruz.
        """
        if keys[pygame.K_LEFT]:
            self.next_dir_x, self.next_dir_y = -1, 0
            self.dir_name = "LEFT"

        elif keys[pygame.K_RIGHT]:
            self.next_dir_x, self.next_dir_y = 1, 0
            self.dir_name = "RIGHT"

        elif keys[pygame.K_UP]:
            self.next_dir_x, self.next_dir_y = 0, -1
            self.dir_name = "UP"

        elif keys[pygame.K_DOWN]:
            self.next_dir_x, self.next_dir_y = 0, 1
            self.dir_name = "DOWN"

    # Ana update fonksiyonu (her frame çağrılıyor)
    def update(self, dt):
        """
        dt: Frame süresi (saniye cinsinden).
        - Yön değiştirme
        - Hareket
        - Yem/power pellet yeme
        - Power mod süresinin yönetimi
        """
        if not self.alive:
            return

        # Bu frame'de power pellet yedi mi? Başta sıfırla
        self.just_ate_power = False

        # 1) Yeni yön duvara çarpmıyorsa, o yöne dön
        if self.can_move(self.next_dir_x, self.next_dir_y):
            self.dir_x, self.dir_y = self.next_dir_x, self.next_dir_y

        # 2) Mevcut yönde ilerle
        old_x, old_y = self.x, self.y

        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt

        # Duvara çarparsa eski yere dön ve tile merkezine hizala
        if self.collides_with_wall():
            self.x, self.y = old_x, old_y
            self.center_on_grid()

        # 3) Bulunduğu tile'da yem/power pellet var mı?
        col = int((self.x + self.size / 2) // self.tile_size)
        row = int(((self.y + self.size / 2) - self.hud_height) // self.tile_size)

        if 0 <= row < len(self.grid) and 0 <= col < len(self.grid[0]):
            tile = self.grid[row][col]

            # Normal küçük nokta
            if tile == '.':
                self.grid[row][col] = ' '   # yemi sil
                self.score += 10

            # Power pellet
            elif tile == 'o':
                self.grid[row][col] = ' '   # power'ı sil
                self.score += 50
                self.just_ate_power = True  # main.py tarafında power_mode başlatılıyor hayaletler mavi olacak ve yavaslayacaklar.

        # 4) Power mod aktifse zamanını geri say 7 sn sonra power mode inaktif olur
        if self.power_mode:
            self.power_timer -= dt
            if self.power_timer <= 0:
                self.power_mode = False

    # Hareket ve çarpışma fonksiyonları
    def can_move(self, dir_x, dir_y):
        """
        Verilen yönde (dir_x, dir_y) ilerleyebilir miyiz?
        - 0,0 verilirse zaten hareket yoktur, False.
        - Yarım tile ileriye test rect oluşturup duvara çarpıyor mu diye bakıyoruz.
        """
        if dir_x == 0 and dir_y == 0:
            return False

        test_x = self.x + dir_x * self.tile_size / 2
        test_y = self.y + dir_y * self.tile_size / 2
        test_rect = pygame.Rect(test_x, test_y, self.size, self.size)

        for wall in self.wall_rects:
            if test_rect.colliderect(wall):
                return False

        return True

    def collides_with_wall(self):
        #Şu anki konumda Pac-Man herhangi bir duvara çarpıyor mu?
        rect = self.rect()
        for wall in self.wall_rects:
            if rect.colliderect(wall):
                return True
        return False
    
    # Çizim
    def draw(self, surface):
        """
        Pac-Man'i ekrana çizer.
        - Eğer sprite yüklüyse yönüne göre o resmi kullanır,
        - Aksi halde sarı daire olarak çizer.
        """
        if self.pacman_images is not None:
            img = self.pacman_images.get(self.dir_name, self.pacman_images["RIGHT"])
            surface.blit(img, (self.x, self.y))
        else:
            pygame.draw.circle(
                surface,
                self.color,
                (int(self.x + self.size / 2), int(self.y + self.size / 2)),
                self.size // 2
            )
