import math

import pygame


CHARACTER_ORDER = ("soldier", "scout", "engineer", "tank")
DIFFICULTY_ORDER = ("easy", "normal", "hard", "nightmare")
MAP_ORDER_FALLBACK = ("warehouse", "crossfire", "split")
SETUP_STEPS = ("difficulty", "map", "character")


class UIManager:
    """Small UI rendering coordinator.

    The gameplay screens still live on the Game object for now because they read
    a lot of game state directly. This manager owns the reusable drawing
    primitives and dispatches each high-level UI screen, so later steps can move
    screen bodies here without changing the main loop again.
    """

    def _colors(self, state):
        colors = getattr(state, "COLORS", None)
        if colors is not None:
            return colors
        return {
            "text": (230, 234, 226),
            "muted": (149, 157, 154),
            "gold": (245, 196, 66),
            "red": (225, 73, 66),
            "green": (96, 205, 119),
            "blue": (93, 156, 236),
            "cyan": (89, 215, 205),
            "orange": (246, 144, 66),
            "purple": (166, 116, 224),
            "hud_line": (70, 75, 86),
        }

    def draw_main_menu(self, screen, state):
        sw, sh = screen.get_size()
        scale = getattr(state, "ui_scale", 1.0)
        colors = self._colors(state)

        self._draw_survival_menu_background(screen, state, scale)

        title_y = int(sh * 0.17)
        title_rect = pygame.Rect(0, title_y, sw, max(70, int(110 * scale)))
        title = state.t("title") if hasattr(state, "t") else "PIXEL ZOMBIE SIEGE"
        self._draw_glow_text(screen, title, title_rect, colors["gold"], state.title_font, glow_color=(124, 34, 28))

        subtitle_rect = pygame.Rect(0, title_rect.bottom + int(8 * scale), sw, max(30, int(42 * scale)))
        self.draw_text_center(screen, "Survive. Build. Defend.", subtitle_rect, (214, 219, 210), state.font)
        pygame.draw.line(
            screen,
            (168, 52, 48),
            (sw // 2 - int(190 * scale), subtitle_rect.bottom + int(10 * scale)),
            (sw // 2 + int(190 * scale), subtitle_rect.bottom + int(10 * scale)),
            max(1, int(2 * scale)),
        )

        button_w = min(int(390 * scale), sw - getattr(state, "margin", 16) * 2)
        button_h = max(52, int(68 * scale))
        bx = sw // 2 - button_w // 2
        y0 = int(sh * 0.39)
        gap = max(14, int(18 * scale))
        panel = pygame.Rect(
            bx - int(38 * scale),
            y0 - int(32 * scale),
            button_w + int(76 * scale),
            button_h * 3 + gap * 2 + int(64 * scale),
        )
        self.draw_panel(screen, panel, color=(10, 12, 16), alpha=172, border=True, border_color=(112, 42, 43))

        buttons = (
            ("menu_start", state.t("start"), (142, 34, 38)),
            ("menu_options", state.t("options"), (57, 61, 70)),
            ("menu_exit", state.t("exit"), (86, 34, 37)),
        )
        for index, (key, label, accent) in enumerate(buttons):
            rect = pygame.Rect(bx, y0 + index * (button_h + gap), button_w, button_h)
            self.draw_menu_button(screen, state.ui_buttons, key, rect, label, accent=accent, colors=colors, font=state.font)

    def _draw_survival_menu_background(self, screen, state, scale):
        image = getattr(state, "menu_background", None)
        if image is not None:
            self._draw_cover_image(screen, image)
        else:
            self._draw_procedural_survival_background(screen, scale)

        sw, sh = screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((3, 5, 8, 118))
        screen.blit(overlay, (0, 0))

        vignette = pygame.Surface((sw, sh), pygame.SRCALPHA)
        max_radius = math.hypot(sw, sh) / 2
        center = (sw // 2, sh // 2)
        for i in range(22):
            pct = i / 21
            radius = int(max_radius * pct)
            alpha = int(95 * pct * pct)
            pygame.draw.circle(vignette, (0, 0, 0, alpha), center, radius, max(14, int(40 * scale)))
        screen.blit(vignette, (0, 0))

    def _draw_cover_image(self, screen, image):
        sw, sh = screen.get_size()
        iw, ih = image.get_size()
        scale = max(sw / iw, sh / ih)
        size = (max(1, math.ceil(iw * scale)), max(1, math.ceil(ih * scale)))
        scaled = pygame.transform.smoothscale(image, size)
        screen.blit(scaled, scaled.get_rect(center=(sw // 2, sh // 2)))

    def _draw_procedural_survival_background(self, screen, scale):
        sw, sh = screen.get_size()
        screen.fill((7, 9, 13))
        for y in range(sh):
            pct = y / max(1, sh - 1)
            color = (7 + int(10 * pct), 9 + int(8 * pct), 13 + int(6 * pct))
            pygame.draw.line(screen, color, (0, y), (sw, y))

        ticks = pygame.time.get_ticks() * 0.001
        for i in range(9):
            x = int((i * 283 + math.sin(ticks * 0.35 + i) * 22) % max(1, sw))
            y = int(sh * (0.18 + (i % 4) * 0.15))
            length = int((180 + i * 23) * scale)
            color = (120 + i * 7, 39 + i * 3, 26)
            pygame.draw.line(screen, color, (x, y), (x + length, y + int(18 * scale)), max(1, int(2 * scale)))

        ground = pygame.Rect(0, int(sh * 0.72), sw, int(sh * 0.28))
        pygame.draw.rect(screen, (7, 8, 10), ground)
        for i in range(12):
            x = int((i * 167 + 41) % max(1, sw))
            base_y = int(sh * (0.76 + (i % 3) * 0.055))
            height = int((42 + (i % 4) * 12) * scale)
            width = int((16 + (i % 3) * 4) * scale)
            self._draw_zombie_silhouette(screen, x, base_y, width, height)

        for i in range(52):
            x = int((i * 97 + 53) % max(1, sw))
            y = int((i * 193 + 71) % max(1, sh))
            alpha = 34 + (i % 4) * 12
            pygame.draw.rect(screen, (170, 76, 45, alpha), (x, y, max(1, int(2 * scale)), max(1, int(2 * scale))))

    def _draw_zombie_silhouette(self, screen, x, base_y, width, height):
        color = (4, 5, 6)
        head_r = max(4, width // 2)
        body = pygame.Rect(x - width // 2, base_y - height, width, height - head_r)
        pygame.draw.rect(screen, color, body)
        pygame.draw.circle(screen, color, (x, body.top - head_r // 2), head_r)
        pygame.draw.line(screen, color, (body.left, body.top + height // 4), (body.left - width, body.top + height // 2), 3)
        pygame.draw.line(screen, color, (body.right, body.top + height // 5), (body.right + width, body.top + height // 3), 3)
        pygame.draw.line(screen, color, (body.centerx - width // 4, body.bottom), (body.centerx - width, base_y), 4)
        pygame.draw.line(screen, color, (body.centerx + width // 4, body.bottom), (body.centerx + width, base_y), 4)

    def _draw_glow_text(self, screen, text, rect, color, font, glow_color):
        for offset, alpha in ((5, 42), (3, 58), (1, 82)):
            glow = font.render(text, True, glow_color)
            glow.set_alpha(alpha)
            glow_rect = glow.get_rect(center=(rect.centerx + offset, rect.centery + offset))
            screen.blit(glow, glow_rect)
        self.draw_text_center(screen, text, rect, color, font)

    def draw_menu_button(self, screen, buttons, key, rect, label, *, accent, colors, font):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        pressed = hover and pygame.mouse.get_pressed(num_buttons=3)[0]
        dx = int(2 if pressed else 0)
        draw_rect = rect.move(dx, dx)
        base = (28, 30, 36)
        if hover:
            fill = (47, 42, 43)
            border = (226, 80, 72)
            text = (245, 238, 226)
        else:
            fill = base
            border = (104, 55, 57)
            text = colors["text"]

        shadow = pygame.Surface((draw_rect.w + 10, draw_rect.h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 118), shadow.get_rect(), border_radius=10)
        screen.blit(shadow, (draw_rect.x + 5, draw_rect.y + 6))

        pygame.draw.rect(screen, fill, draw_rect, border_radius=8)
        pygame.draw.rect(screen, border, draw_rect, 2, border_radius=8)
        pygame.draw.line(
            screen,
            accent,
            (draw_rect.left + 14, draw_rect.centery),
            (draw_rect.left + max(46, int(draw_rect.w * 0.20)), draw_rect.centery),
            max(2, draw_rect.h // 18),
        )
        self.draw_text_center(screen, label, draw_rect, text, font)
        if hover:
            pygame.draw.rect(screen, (255, 120, 102), draw_rect.inflate(6, 6), 1, border_radius=10)
        buttons[key] = rect

    def draw_options_menu(self, screen, state):
        state.draw_options()

    def draw_prepare_screen(self, screen, state):
        sw, sh = screen.get_size()
        scale = getattr(state, "ui_scale", 1.0)
        colors = self._colors(state)
        margin = getattr(state, "margin", max(12, int(18 * scale)))
        step = getattr(state, "setup_step", "difficulty")
        if step not in SETUP_STEPS:
            step = "difficulty"

        draw_background = getattr(state, "draw_menu_background", None)
        if draw_background is not None:
            draw_background(getattr(state, "map_id", "warehouse"))
        else:
            self._draw_procedural_survival_background(screen, scale)

        title_rect = pygame.Rect(0, int(28 * scale), sw, max(54, int(72 * scale)))
        self._draw_glow_text(screen, state.t("setup_title"), title_rect, colors["gold"], state.big_font, (91, 30, 28))
        self.draw_text_center(
            screen,
            state.t("title"),
            pygame.Rect(0, title_rect.bottom - int(4 * scale), sw, max(28, int(38 * scale))),
            colors["cyan"],
            state.small_font,
        )

        box_w = min(int(1540 * scale), sw - margin * 2)
        box_h = min(int(805 * scale), sh - int(178 * scale))
        box = pygame.Rect(sw // 2 - box_w // 2, int(150 * scale), box_w, box_h)
        self.draw_panel(screen, box, color=(9, 12, 17), alpha=226, border=True, border_color=(72, 78, 91), border_radius=10)

        pad = max(14, int(24 * scale))
        progress_h = max(76, int(92 * scale))
        actions_h = max(86, int(98 * scale))
        summary_h = max(28, int(36 * scale))
        progress_rect = pygame.Rect(box.x + pad, box.y + pad, box.w - pad * 2, progress_h)
        content = pygame.Rect(
            box.x + pad,
            progress_rect.bottom + int(12 * scale),
            box.w - pad * 2,
            box.h - pad * 3 - progress_h - actions_h - summary_h,
        )
        summary_rect = pygame.Rect(box.x + pad, content.bottom + int(10 * scale), box.w - pad * 2, summary_h)

        self._draw_setup_progress(screen, state, progress_rect, step, colors, scale)
        self._draw_setup_step_content(screen, state, content, step, colors, scale)
        self._draw_setup_summary(screen, state, summary_rect, colors, scale)
        self._draw_setup_actions(screen, state, box, step, colors, scale)

    def _draw_setup_progress(self, screen, state, rect, step, colors, scale):
        self.draw_panel(screen, rect, color=(14, 17, 23), alpha=220, border=True, border_color=(55, 61, 74), border_radius=8)
        title = f"{SETUP_STEPS.index(step) + 1}/3  {self._setup_step_label(state, step)}"
        self.draw_text_center(screen, title, pygame.Rect(rect.x, rect.y + int(8 * scale), rect.w, max(30, int(40 * scale))), colors["gold"], state.font)

        node_y = rect.bottom - max(24, int(28 * scale))
        line_x0 = rect.x + int(rect.w * 0.22)
        line_x1 = rect.right - int(rect.w * 0.22)
        pygame.draw.line(screen, (57, 62, 74), (line_x0, node_y), (line_x1, node_y), max(2, int(3 * scale)))
        active_index = SETUP_STEPS.index(step)
        for index, setup_step in enumerate(SETUP_STEPS):
            x = int(line_x0 + (line_x1 - line_x0) * index / (len(SETUP_STEPS) - 1))
            done = index < active_index
            active = index == active_index
            color = colors["green"] if done else (colors["cyan"] if active else (78, 84, 98))
            radius = max(9, int((13 if active else 10) * scale))
            pygame.draw.circle(screen, color, (x, node_y), radius)
            pygame.draw.circle(screen, (12, 14, 18), (x, node_y), max(4, radius - 5))
            label = self._setup_step_label(state, setup_step)
            self.draw_text_center(
                screen,
                self.fit_text(label, state.tiny_font, int(170 * scale)),
                pygame.Rect(x - int(85 * scale), node_y + int(12 * scale), int(170 * scale), int(20 * scale)),
                color,
                state.tiny_font,
            )

    def _draw_setup_step_content(self, screen, state, rect, step, colors, scale):
        if step == "difficulty":
            self._draw_difficulty_focus(screen, state, rect, colors, scale)
        elif step == "map":
            self._draw_map_focus(screen, state, rect, colors, scale)
        else:
            self._draw_character_focus(screen, state, rect, colors, scale)

    def _draw_difficulty_focus(self, screen, state, rect, colors, scale):
        difficulty_defs = getattr(state, "difficulty_defs", {})
        order = [key for key in DIFFICULTY_ORDER if key in difficulty_defs] or list(difficulty_defs)
        gap = max(16, int(22 * scale))
        cols = 2
        card_w = (rect.w - gap) // cols
        card_h = max(160, (rect.h - gap) // 2)
        for index, difficulty_id in enumerate(order):
            x = rect.x + (index % cols) * (card_w + gap)
            y = rect.y + (index // cols) * (card_h + gap)
            self._draw_difficulty_card(screen, state, pygame.Rect(x, y, card_w, card_h), difficulty_id, difficulty_defs[difficulty_id], colors, scale)

    def _draw_map_focus(self, screen, state, rect, colors, scale):
        map_rows = getattr(state, "map_rows_by_id", {})
        order = [key for key in getattr(state, "map_order", MAP_ORDER_FALLBACK) if key in map_rows] or list(map_rows)
        gap = max(16, int(22 * scale))
        card_w = (rect.w - gap * max(0, len(order) - 1)) // max(1, len(order))
        for index, map_id in enumerate(order):
            card = pygame.Rect(rect.x + index * (card_w + gap), rect.y, card_w, rect.h)
            self._draw_map_card(screen, state, card, map_id, colors, scale)

    def _draw_character_focus(self, screen, state, rect, colors, scale):
        character_defs = getattr(state, "character_defs", {})
        order = [key for key in CHARACTER_ORDER if key in character_defs] or list(character_defs)
        gap = max(16, int(22 * scale))
        cols = 2
        card_w = (rect.w - gap) // cols
        card_h = max(170, (rect.h - gap) // 2)
        for index, character_id in enumerate(order):
            x = rect.x + (index % cols) * (card_w + gap)
            y = rect.y + (index // cols) * (card_h + gap)
            self._draw_character_card(screen, state, pygame.Rect(x, y, card_w, card_h), character_id, character_defs[character_id], colors, scale)

    def _draw_setup_summary(self, screen, state, rect, colors, scale):
        pygame.draw.rect(screen, (13, 16, 22), rect, border_radius=7)
        pygame.draw.rect(screen, (55, 61, 74), rect, 1, border_radius=7)
        summary = f"{state.difficulty_name()}  |  {state.map_name()}  |  {state.character_name()}"
        self.draw_text_center(screen, self.fit_text(summary, state.small_font, rect.w - int(32 * scale)), rect, colors["muted"], state.small_font)

    def _setup_step_label(self, state, step):
        if step == "difficulty":
            return state.t("select_difficulty")
        if step == "map":
            return state.t("select_map")
        return state.t("select_character")

    def _draw_setup_column(self, screen, rect, title, colors, scale, font):
        self.draw_panel(screen, rect, color=(15, 18, 24), alpha=205, border=True, border_color=(55, 61, 74), border_radius=8)
        header = pygame.Rect(rect.x + int(14 * scale), rect.y + int(10 * scale), rect.w - int(28 * scale), max(34, int(42 * scale)))
        pygame.draw.rect(screen, (24, 28, 35), header, border_radius=7)
        pygame.draw.line(screen, colors["cyan"], (header.x + 14, header.bottom - 2), (header.right - 14, header.bottom - 2), 2)
        self.draw_text_center(screen, title, header, colors["text"], font)

    def _draw_character_column(self, screen, state, column, colors, scale):
        character_defs = getattr(state, "character_defs", {})
        order = [key for key in CHARACTER_ORDER if key in character_defs] or list(character_defs)
        area = self._column_body(column, scale)
        gap = max(8, int(10 * scale))
        card_h = max(96, (area.h - gap * max(0, len(order) - 1)) // max(1, len(order)))
        for index, character_id in enumerate(order):
            rect = pygame.Rect(area.x, area.y + index * (card_h + gap), area.w, card_h)
            self._draw_character_card(screen, state, rect, character_id, character_defs[character_id], colors, scale)

    def _draw_difficulty_column(self, screen, state, column, colors, scale):
        difficulty_defs = getattr(state, "difficulty_defs", {})
        order = [key for key in DIFFICULTY_ORDER if key in difficulty_defs] or list(difficulty_defs)
        area = self._column_body(column, scale)
        gap = max(9, int(12 * scale))
        card_h = max(98, (area.h - gap * max(0, len(order) - 1)) // max(1, len(order)))
        for index, difficulty_id in enumerate(order):
            rect = pygame.Rect(area.x, area.y + index * (card_h + gap), area.w, card_h)
            self._draw_difficulty_card(screen, state, rect, difficulty_id, difficulty_defs[difficulty_id], colors, scale)

    def _draw_map_column(self, screen, state, column, colors, scale):
        map_rows = getattr(state, "map_rows_by_id", {})
        order = [key for key in getattr(state, "map_order", MAP_ORDER_FALLBACK) if key in map_rows] or list(map_rows)
        area = self._column_body(column, scale)
        gap = max(10, int(14 * scale))
        card_h = max(142, (area.h - gap * max(0, len(order) - 1)) // max(1, len(order)))
        for index, map_id in enumerate(order):
            rect = pygame.Rect(area.x, area.y + index * (card_h + gap), area.w, card_h)
            self._draw_map_card(screen, state, rect, map_id, colors, scale)

    def _column_body(self, column, scale):
        top = column.y + max(58, int(66 * scale))
        pad = max(10, int(14 * scale))
        return pygame.Rect(column.x + pad, top, column.w - pad * 2, column.bottom - top - pad)

    def _draw_setup_actions(self, screen, state, box, step, colors, scale):
        button_w = min(int(310 * scale), max(180, box.w // 4))
        button_h = max(48, int(60 * scale))
        gap = max(18, int(26 * scale))
        total_w = button_w * 2 + gap
        y = box.bottom - max(72, int(86 * scale))
        x = box.centerx - total_w // 2
        next_key = "setup_begin" if step == "character" else "setup_next"
        next_label = state.t("begin_run") if step == "character" else state.t("next")
        self.draw_menu_button(
            screen,
            state.ui_buttons,
            "setup_back",
            pygame.Rect(x, y, button_w, button_h),
            state.t("back"),
            accent=(77, 82, 96),
            colors=colors,
            font=state.font,
        )
        self.draw_menu_button(
            screen,
            state.ui_buttons,
            next_key,
            pygame.Rect(x + button_w + gap, y, button_w, button_h),
            next_label,
            accent=(180, 45, 48),
            colors=colors,
            font=state.font,
        )

    def _draw_character_card(self, screen, state, rect, character_id, cfg, colors, scale):
        active = character_id == getattr(state, "character_id", "soldier")
        accent = (89, 215, 205) if character_id != "tank" else (245, 196, 66)
        draw_rect = self._draw_choice_card(screen, state.ui_buttons, f"character_{character_id}", rect, active, accent, colors, scale)

        preview = pygame.Rect(draw_rect.x + int(14 * scale), draw_rect.y + int(12 * scale), max(72, int(86 * scale)), draw_rect.h - int(24 * scale))
        self._draw_character_sprite(screen, state, preview, character_id)

        text_x = preview.right + int(12 * scale)
        text_w = draw_rect.right - text_x - int(12 * scale)
        name = state.character_name(character_id)
        desc = state.character_description(character_id)
        self.draw_text(screen, self.fit_text(name, state.small_font, text_w), text_x, draw_rect.y + int(12 * scale), colors["gold"], state.small_font)
        self.draw_text(screen, self.fit_text(desc, state.tiny_font, text_w), text_x, draw_rect.y + int(40 * scale), colors["muted"], state.tiny_font)

        stats = (
            ("HP", cfg.get("hp", 100), cfg.get("hp", 100) / 170),
            ("SPD", cfg.get("speed", 150), cfg.get("speed", 150) / 190),
            ("ARM", cfg.get("armor", 0), cfg.get("armor", 0) / 3),
        )
        bar_y = draw_rect.y + int(70 * scale)
        bar_h = max(8, int(10 * scale))
        for index, (label, value, pct) in enumerate(stats):
            row_y = bar_y + index * max(17, int(20 * scale))
            label_rect = pygame.Rect(text_x, row_y - 4, int(42 * scale), max(14, int(18 * scale)))
            self.draw_text_center(screen, label, label_rect, colors["text"], state.tiny_font)
            self._draw_stat_bar(
                screen,
                pygame.Rect(label_rect.right + int(8 * scale), row_y, max(50, text_w - label_rect.w - int(54 * scale)), bar_h),
                pct,
                accent,
                colors,
            )
            value_rect = pygame.Rect(draw_rect.right - int(42 * scale), row_y - 4, int(34 * scale), max(14, int(18 * scale)))
            self.draw_text_center(screen, self._format_stat_value(value), value_rect, colors["muted"], state.tiny_font)

    def _draw_difficulty_card(self, screen, state, rect, difficulty_id, cfg, colors, scale):
        active = difficulty_id == getattr(state, "difficulty_id", "normal")
        accent_by_id = {
            "easy": (96, 205, 119),
            "normal": (89, 215, 205),
            "hard": (245, 142, 66),
            "nightmare": (225, 73, 66),
        }
        accent = accent_by_id.get(difficulty_id, colors["gold"])
        draw_rect = self._draw_choice_card(screen, state.ui_buttons, f"difficulty_{difficulty_id}", rect, active, accent, colors, scale)
        title = state.difficulty_name(difficulty_id)
        self.draw_text(screen, title, draw_rect.x + int(16 * scale), draw_rect.y + int(12 * scale), accent, state.small_font)

        hp = cfg.get("hp", 1.0)
        damage = cfg.get("damage", 1.0)
        speed = cfg.get("speed", 1.0)
        count = cfg.get("count", 1.0)
        reward = cfg.get("reward", 1.0)
        threat = min(1.0, (hp + damage + speed + count) / 6.2)
        label = f"HP x{hp:.2f}  DMG x{damage:.2f}  SPD x{speed:.2f}"
        self.draw_text(screen, self.fit_text(label, state.tiny_font, draw_rect.w - int(32 * scale)), draw_rect.x + int(16 * scale), draw_rect.y + int(43 * scale), colors["text"], state.tiny_font)
        self._draw_labeled_bar(screen, state, draw_rect, int(72 * scale), "Threat", threat, accent, colors)
        self._draw_labeled_bar(screen, state, draw_rect, int(99 * scale), "Reward", min(1.0, reward / 1.15), colors["gold"], colors)

        warning = self._difficulty_warning(difficulty_id, getattr(state, "language", "en"))
        if warning:
            self.draw_text_center(
                screen,
                self.fit_text(warning, state.tiny_font, draw_rect.w - int(28 * scale)),
                pygame.Rect(draw_rect.x + int(10 * scale), draw_rect.bottom - int(26 * scale), draw_rect.w - int(20 * scale), int(20 * scale)),
                colors["red"],
                state.tiny_font,
            )

    def _draw_map_card(self, screen, state, rect, map_id, colors, scale):
        active = map_id == getattr(state, "map_id", "warehouse")
        theme = getattr(state, "map_themes", {}).get(map_id, {})
        accent = theme.get("accent", colors["gold"])
        draw_rect = self._draw_choice_card(screen, state.ui_buttons, f"map_{map_id}", rect, active, accent, colors, scale)

        preview_h = max(96, int(draw_rect.h * 0.54))
        preview = pygame.Rect(draw_rect.x + int(14 * scale), draw_rect.y + int(12 * scale), draw_rect.w - int(28 * scale), preview_h)
        self._draw_map_preview_fallback(screen, state, preview, map_id, accent)

        title_y = preview.bottom + int(10 * scale)
        self.draw_text_center(screen, state.map_name(map_id), pygame.Rect(draw_rect.x + 12, title_y, draw_rect.w - 24, max(24, int(30 * scale))), accent, state.small_font)
        self.draw_text_center(
            screen,
            self.fit_text(state.map_description(map_id), state.tiny_font, draw_rect.w - int(32 * scale)),
            pygame.Rect(draw_rect.x + int(16 * scale), title_y + max(28, int(34 * scale)), draw_rect.w - int(32 * scale), max(24, int(30 * scale))),
            colors["muted"],
            state.tiny_font,
        )

    def _draw_choice_card(self, screen, buttons, key, rect, active, accent, colors, scale):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        inflate = int(6 * scale) if active else (int(3 * scale) if hover else 0)
        draw_rect = rect.inflate(inflate, inflate)
        fill = (35, 39, 47) if active else ((31, 34, 42) if hover else (22, 25, 31))
        shadow = pygame.Surface((draw_rect.w + 14, draw_rect.h + 14), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 132), shadow.get_rect(), border_radius=11)
        screen.blit(shadow, (draw_rect.x + 5, draw_rect.y + 7))
        if active:
            glow = pygame.Surface((draw_rect.w + 18, draw_rect.h + 18), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*accent, 42), glow.get_rect(), border_radius=14)
            screen.blit(glow, (draw_rect.x - 9, draw_rect.y - 9))
        pygame.draw.rect(screen, fill, draw_rect, border_radius=8)
        pygame.draw.rect(screen, accent if active else colors["hud_line"], draw_rect, 2, border_radius=8)
        pygame.draw.line(screen, accent, (draw_rect.x + 10, draw_rect.y + 1), (draw_rect.right - 10, draw_rect.y + 1), 1)
        buttons[key] = rect
        return draw_rect

    def _draw_character_sprite(self, screen, state, rect, character_id):
        pygame.draw.rect(screen, (9, 11, 15), rect, border_radius=7)
        pygame.draw.ellipse(screen, (2, 3, 5), (rect.x + 8, rect.bottom - 20, rect.w - 16, 18))
        sprites = getattr(state, "sprites", {})
        ticks = pygame.time.get_ticks()
        facing = ("down", "right", "up", "left")[(ticks // 1000) % 4]
        frame = (ticks // 140) % 4
        sprite = sprites.get(f"player_{character_id}_{facing}_{frame}") or sprites.get(f"player_{character_id}") or sprites.get("player")
        if sprite is None:
            pygame.draw.rect(screen, (74, 126, 190), rect.inflate(-rect.w // 3, -rect.h // 3))
            return
        scale = max(2, int(min(rect.w * 0.66 / sprite.get_width(), rect.h * 0.68 / sprite.get_height())))
        preview = pygame.transform.scale(sprite, (sprite.get_width() * scale, sprite.get_height() * scale))
        screen.blit(preview, preview.get_rect(center=(rect.centerx, rect.centery - 4)))

    def _draw_stat_bar(self, screen, rect, pct, accent, colors):
        pct = max(0, min(1, pct))
        pygame.draw.rect(screen, (11, 13, 17), rect, border_radius=4)
        fill = pygame.Rect(rect.x, rect.y, int(rect.w * pct), rect.h)
        pygame.draw.rect(screen, accent, fill, border_radius=4)
        pygame.draw.rect(screen, colors["hud_line"], rect, 1, border_radius=4)

    def _draw_labeled_bar(self, screen, state, rect, y_offset, label, pct, accent, colors):
        x = rect.x + int(16 * getattr(state, "ui_scale", 1.0))
        y = rect.y + y_offset
        label_w = int(76 * getattr(state, "ui_scale", 1.0))
        self.draw_text(screen, label, x, y - 4, colors["muted"], state.tiny_font)
        self._draw_stat_bar(screen, pygame.Rect(x + label_w, y, rect.w - label_w - int(32 * getattr(state, "ui_scale", 1.0)), max(8, int(10 * getattr(state, "ui_scale", 1.0)))), pct, accent, colors)

    def _difficulty_warning(self, difficulty_id, language):
        if difficulty_id == "hard":
            return "Cảnh báo: áp lực cao." if language == "vi" else "Warning: high pressure."
        if difficulty_id == "nightmare":
            return "Cực khó: phòng thủ bị giới hạn." if language == "vi" else "Extreme: limited defense."
        return ""

    def _format_stat_value(self, value):
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.2f}".rstrip("0").rstrip(".")
        return str(int(round(value)))

    def _draw_map_preview_fallback(self, screen, state, rect, map_id, accent):
        theme = getattr(state, "map_themes", {}).get(map_id, {})
        rows = getattr(state, "map_rows_by_id", {}).get(map_id)
        pygame.draw.rect(screen, theme.get("bg", (15, 18, 22)), rect, border_radius=6)
        if not rows:
            pygame.draw.rect(screen, accent, rect.inflate(-rect.w // 3, -rect.h // 3), border_radius=4)
            return
        grid_w = max(1, len(rows[0]))
        grid_h = max(1, len(rows))
        inner = rect.inflate(-10, -10)
        cell_w = inner.w / grid_w
        cell_h = inner.h / grid_h
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                if value == "#":
                    color = theme.get("wall", accent)
                else:
                    color = theme.get("floor_a", (34, 38, 42)) if (x + y) % 2 == 0 else theme.get("floor_b", (28, 31, 36))
                tile = pygame.Rect(
                    int(inner.x + x * cell_w),
                    int(inner.y + y * cell_h),
                    max(1, int(math.ceil(cell_w))),
                    max(1, int(math.ceil(cell_h))),
                )
                pygame.draw.rect(screen, color, tile)
        pygame.draw.rect(screen, accent, rect, 1, border_radius=6)

    def draw_hud(self, screen, game_state):
        state = game_state
        colors = self._colors(state)
        scale = getattr(state, "ui_scale", 1.0)
        sw, sh = screen.get_size()
        margin = getattr(state, "margin", max(12, int(16 * scale)))

        self._draw_player_status(screen, state, pygame.Rect(margin, margin, min(int(470 * scale), sw // 2 - margin), max(104, int(116 * scale))), colors, scale)
        right_w = min(int(440 * scale), sw // 2 - margin)
        self._draw_wave_status(screen, state, pygame.Rect(sw - margin - right_w, margin, right_w, max(104, int(116 * scale))), colors, scale)
        self._draw_combat_hotbar(screen, state, colors, scale)

    def _draw_player_status(self, screen, state, rect, colors, scale):
        player = getattr(state, "player", None)
        if player is None:
            return
        self.draw_panel(screen, rect, color=(12, 15, 21), alpha=218, border=True, border_color=(58, 64, 78), border_radius=9)
        icon = pygame.Rect(rect.x + int(12 * scale), rect.y + int(12 * scale), max(58, int(70 * scale)), rect.h - int(24 * scale))
        self._draw_class_icon(screen, state, icon)

        text_x = icon.right + int(14 * scale)
        title_y = rect.y + int(12 * scale)
        class_name = state.character_name(getattr(player, "character_id", getattr(state, "character_id", "soldier")))
        title = f"{class_name}  {state.t('level_short')} {getattr(player, 'level', 1)}"
        self.draw_text(screen, self.fit_text(title, state.small_font, rect.right - text_x - int(12 * scale)), text_x, title_y, colors["gold"], state.small_font)

        bar_w = max(120, rect.right - text_x - int(18 * scale))
        hp_rect = pygame.Rect(text_x + int(42 * scale), rect.y + int(46 * scale), bar_w - int(42 * scale), max(12, int(16 * scale)))
        xp_rect = pygame.Rect(hp_rect.x, hp_rect.bottom + int(12 * scale), hp_rect.w, max(8, int(12 * scale)))
        hp_pct = getattr(player, "hp", 0) / max(1, getattr(player, "max_hp", 1))
        xp_pct = getattr(player, "xp", 0) / max(1, getattr(player, "next_xp", 1))
        hp_color = colors["red"] if hp_pct < 0.3 else colors["green"]
        self.draw_text(screen, state.t("hp"), text_x, hp_rect.y - 4, colors["text"], state.tiny_font)
        self.draw_progress_bar(screen, hp_rect, hp_pct, hp_color, (48, 29, 34), colors["hud_line"])
        hp_text = f"{max(0, int(getattr(player, 'hp', 0)))}/{int(getattr(player, 'max_hp', 1))}"
        self.draw_text_center(screen, hp_text, hp_rect, (244, 248, 240), state.tiny_font)
        self.draw_text(screen, state.t("xp"), text_x, xp_rect.y - 5, colors["text"], state.tiny_font)
        self.draw_progress_bar(screen, xp_rect, xp_pct, colors["cyan"], (28, 35, 45), colors["hud_line"])

    def _draw_wave_status(self, screen, state, rect, colors, scale):
        self.draw_panel(screen, rect, color=(12, 15, 21), alpha=218, border=True, border_color=(58, 64, 78), border_radius=9)
        alive, queued = self._enemy_counts(state)
        wave = getattr(state, "wave", 0) or 1
        rows = [
            (state.t("gold"), state.gold_text(), colors["gold"]),
            (state.t("wave"), str(wave), colors["cyan"]),
            (state.t("enemies"), f"{alive} (+{queued})" if queued else str(alive), colors["text"]),
        ]
        if not getattr(state, "wave_active", False) and getattr(state, "wave", 0) > 0 and getattr(state, "wave_break_timer", 0) > 0:
            rows.append((state.t("next_wave"), f"{math.ceil(state.wave_break_timer)}s", colors["orange"]))

        x = rect.x + int(18 * scale)
        y = rect.y + int(12 * scale)
        label_w = int(140 * scale)
        for label, value, color in rows[:4]:
            row = pygame.Rect(x, y, rect.w - int(36 * scale), max(20, int(24 * scale)))
            self.draw_text(screen, label, row.x, row.y, colors["muted"], state.tiny_font)
            self.draw_text(screen, self.fit_text(value, state.small_font, row.w - label_w), row.x + label_w, row.y - 2, color, state.small_font)
            y += max(22, int(25 * scale))

        pause_w = max(74, int(92 * scale))
        pause_h = max(30, int(34 * scale))
        pause_rect = pygame.Rect(rect.right - pause_w - int(12 * scale), rect.bottom - pause_h - int(10 * scale), pause_w, pause_h)
        self.draw_button(screen, state.ui_buttons, "pause_toggle", pause_rect, state.t("pause"), colors=colors, active=False, font=state.tiny_font)

    def _draw_combat_hotbar(self, screen, state, colors, scale):
        sw, sh = screen.get_size()
        bottom_h = getattr(state, "bottom_ui_h", max(118, int(140 * scale)))
        slot_h = max(92, min(int(112 * scale), bottom_h - int(24 * scale)))
        gap = max(7, int(10 * scale))
        slot_count = 7
        slot_w = min(int(126 * scale), max(92, (sw - getattr(state, "margin", 16) * 2 - gap * (slot_count - 1)) // slot_count))
        total_w = slot_w * slot_count + gap * (slot_count - 1)
        x = sw // 2 - total_w // 2
        y = sh - bottom_h + (bottom_h - slot_h) // 2
        back = pygame.Rect(x - int(14 * scale), y - int(10 * scale), total_w + int(28 * scale), slot_h + int(20 * scale))
        self.draw_panel(screen, back, color=(10, 12, 17), alpha=196, border=True, border_color=(48, 54, 67), border_radius=10)

        player = state.player
        weapon = player.weapon
        can_afford = getattr(state, "can_afford", lambda cost: True)
        upgrade_cost = getattr(weapon, "upgrade_cost", 0)
        repair_cost = state.repair_cost()
        turret_cost = state.structure_cost("turret")
        fence_cost = state.structure_cost("fence")
        turret_full = state.turret_count() >= state.turret_limit()
        slots = [
            {
                "key": "hotbar_upgrade",
                "shortcut": "1",
                "label": state.t("upgrade"),
                "value": state.t("max") if weapon.is_maxed else (state.t("free") if state.dev_mode else f"{upgrade_cost}g"),
                "accent": colors["gold"],
                "icon": "upgrade",
                "active": False,
                "disabled": (not weapon.is_maxed and not can_afford(upgrade_cost)),
            },
            {
                "key": "hotbar_turret",
                "shortcut": "2",
                "label": state.t("turret"),
                "value": f"{state.t('free') if state.dev_mode else str(turret_cost) + 'g'} {state.turret_count()}/{state.turret_limit()}",
                "accent": colors["cyan"],
                "icon": "turret",
                "active": state.build_mode == "turret",
                "disabled": turret_full or not can_afford(turret_cost),
            },
            {
                "key": "hotbar_fence",
                "shortcut": "3",
                "label": state.t("fence"),
                "value": f"{state.t('free') if state.dev_mode else str(fence_cost) + 'g'} L{state.structure_stats('fence')['level']}",
                "accent": colors["orange"],
                "icon": "fence",
                "active": state.build_mode == "fence",
                "disabled": not can_afford(fence_cost),
            },
            {
                "key": "hotbar_reload",
                "shortcut": "R",
                "label": state.t("reload"),
                "value": f"{weapon.ammo}/{weapon.magazine_size}" if not weapon.is_reloading else f"{weapon.reload_timer:.1f}s",
                "accent": colors["blue"],
                "icon": "reload",
                "active": weapon.is_reloading,
                "disabled": False,
                "cooldown": max(0, weapon.reload_timer),
            },
            {
                "key": "hotbar_repair",
                "shortcut": "E",
                "label": state.t("repair"),
                "value": state.t("free") if state.dev_mode else f"{repair_cost}g",
                "accent": (105, 188, 255),
                "icon": "repair",
                "active": False,
                "disabled": not can_afford(repair_cost),
            },
            {
                "key": "hotbar_dash",
                "shortcut": "Sh",
                "label": state.t("dash"),
                "value": state.t("ready") if player.dash_cooldown <= 0 else f"{player.dash_cooldown:.1f}s",
                "accent": colors["purple"],
                "icon": "dash",
                "active": getattr(player, "dash_time", 0) > 0,
                "disabled": player.dash_cooldown > 0,
                "cooldown": max(0, player.dash_cooldown),
            },
            {
                "key": "auto_toggle_game",
                "shortcut": "F",
                "label": state.t("auto_fire"),
                "value": state.t("on") if state.auto_fire else state.t("off"),
                "accent": colors["green"],
                "icon": "auto",
                "active": state.auto_fire,
                "disabled": False,
            },
        ]
        for index, slot in enumerate(slots):
            rect = pygame.Rect(x + index * (slot_w + gap), y, slot_w, slot_h)
            self._draw_action_slot(screen, state, rect, slot, colors, scale)

    def _draw_class_icon(self, screen, state, rect):
        pygame.draw.rect(screen, (8, 10, 14), rect, border_radius=8)
        pygame.draw.rect(screen, (54, 62, 75), rect, 1, border_radius=8)
        sprites = getattr(state, "sprites", {})
        character_id = getattr(getattr(state, "player", None), "character_id", getattr(state, "character_id", "soldier"))
        sprite = sprites.get(f"player_{character_id}") or sprites.get("player")
        if sprite is None:
            pygame.draw.rect(screen, (70, 120, 170), rect.inflate(-rect.w // 3, -rect.h // 3))
            return
        scale = max(2, int(min(rect.w * 0.62 / sprite.get_width(), rect.h * 0.70 / sprite.get_height())))
        image = pygame.transform.scale(sprite, (sprite.get_width() * scale, sprite.get_height() * scale))
        pygame.draw.ellipse(screen, (0, 0, 0, 120), (rect.centerx - rect.w // 3, rect.bottom - 16, rect.w * 2 // 3, 12))
        screen.blit(image, image.get_rect(center=(rect.centerx, rect.centery - 4)))

    def _enemy_counts(self, state):
        alive = sum(1 for zombie in getattr(state, "zombies", []) if getattr(zombie, "alive", False))
        queued = len(getattr(state, "spawn_queue", []) or [])
        return alive, queued

    def _draw_action_slot(self, screen, state, rect, slot, colors, scale):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        active = slot.get("active", False)
        disabled = slot.get("disabled", False)
        accent = slot["accent"]
        fill = (38, 43, 52) if active else ((35, 39, 47) if hover else (24, 28, 36))
        if disabled and not active:
            fill = (24, 25, 30)

        shadow = pygame.Surface((rect.w + 10, rect.h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 128), shadow.get_rect(), border_radius=10)
        screen.blit(shadow, (rect.x + 4, rect.y + 5))
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, accent if active else colors["hud_line"], rect, 2, border_radius=8)
        if active:
            pygame.draw.rect(screen, (*accent, 255), rect.inflate(5, 5), 1, border_radius=10)

        key_rect = pygame.Rect(rect.x + 8, rect.y + 8, max(34, int(38 * scale)), max(24, int(28 * scale)))
        pygame.draw.rect(screen, accent, key_rect, border_radius=6)
        self.draw_text_center(screen, slot["shortcut"], key_rect, (10, 12, 16), state.tiny_font)

        icon_rect = pygame.Rect(rect.centerx - int(22 * scale), rect.y + int(34 * scale), int(44 * scale), int(34 * scale))
        self._draw_hotbar_icon(screen, icon_rect, slot["icon"], accent, disabled)

        label = self.fit_text(slot["label"], state.tiny_font, rect.w - 14)
        value = self.fit_text(slot["value"], state.tiny_font, rect.w - 14)
        label_color = colors["text"] if not disabled else (112, 118, 126)
        value_color = accent if not disabled else colors["red"]
        self.draw_text_center(screen, label, pygame.Rect(rect.x + 7, rect.bottom - int(42 * scale), rect.w - 14, int(18 * scale)), label_color, state.tiny_font)
        self.draw_text_center(screen, value, pygame.Rect(rect.x + 7, rect.bottom - int(24 * scale), rect.w - 14, int(18 * scale)), value_color, state.tiny_font)

        cooldown = slot.get("cooldown", 0)
        if cooldown and cooldown > 0:
            veil = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 82))
            screen.blit(veil, rect)
            self.draw_text_center(screen, f"{cooldown:.1f}s", rect, colors["text"], state.small_font)
        elif disabled:
            mark = pygame.Rect(rect.right - int(24 * scale), rect.y + int(8 * scale), int(16 * scale), int(16 * scale))
            pygame.draw.circle(screen, colors["red"], mark.center, max(6, mark.w // 2))
            self.draw_text_center(screen, "!", mark, (255, 238, 232), state.tiny_font)

        state.ui_buttons[slot["key"]] = rect

    def _draw_hotbar_icon(self, screen, rect, icon, accent, disabled):
        color = (90, 92, 98) if disabled else accent
        dark = (11, 13, 17)
        cx, cy = rect.center
        if icon == "upgrade":
            points = [(cx, rect.y), (rect.right, cy), (cx + rect.w // 6, cy), (cx + rect.w // 6, rect.bottom), (cx - rect.w // 6, rect.bottom), (cx - rect.w // 6, cy), (rect.x, cy)]
            pygame.draw.polygon(screen, color, points)
        elif icon == "turret":
            pygame.draw.rect(screen, color, (rect.x + rect.w // 4, rect.y + rect.h // 3, rect.w // 2, rect.h // 2), border_radius=4)
            pygame.draw.rect(screen, color, (cx, rect.y + 4, rect.w // 2, max(5, rect.h // 6)))
            pygame.draw.circle(screen, dark, (cx, cy), max(4, rect.w // 8))
        elif icon == "fence":
            for offset in (0, rect.w // 3, rect.w * 2 // 3):
                pygame.draw.rect(screen, color, (rect.x + offset, rect.y + 3, max(5, rect.w // 8), rect.h - 6), border_radius=2)
            pygame.draw.rect(screen, color, (rect.x + 2, cy - 5, rect.w - 4, 5))
            pygame.draw.rect(screen, color, (rect.x + 2, cy + 7, rect.w - 4, 5))
        elif icon == "reload":
            mag = pygame.Rect(rect.x + rect.w // 3, rect.y + 3, rect.w // 3, rect.h - 6)
            pygame.draw.rect(screen, color, mag, border_radius=3)
            pygame.draw.rect(screen, dark, mag.inflate(-6, -8), border_radius=2)
            for i in range(3):
                y = mag.y + 7 + i * max(5, mag.h // 5)
                pygame.draw.line(screen, color, (mag.x + 5, y), (mag.right - 5, y), 2)
            pygame.draw.arc(screen, color, (rect.x + 4, rect.y + 2, rect.w - 8, rect.h - 4), math.radians(35), math.radians(245), 3)
            pygame.draw.polygon(screen, color, [(rect.x + 5, cy), (rect.x + 15, cy - 5), (rect.x + 15, cy + 5)])
        elif icon == "repair":
            pygame.draw.line(screen, color, (rect.x + 8, rect.bottom - 6), (rect.right - 7, rect.y + 7), max(5, rect.w // 8))
            pygame.draw.circle(screen, color, (rect.x + 10, rect.bottom - 8), max(5, rect.w // 7))
            pygame.draw.circle(screen, dark, (rect.x + 10, rect.bottom - 8), max(2, rect.w // 13))
        elif icon == "dash":
            pygame.draw.polygon(screen, color, [(rect.x + 5, cy), (rect.centerx, rect.y + 4), (rect.centerx, rect.y + rect.h // 3), (rect.right - 5, rect.h // 2 + rect.y), (rect.centerx, rect.bottom - 4), (rect.centerx, rect.bottom - rect.h // 3)])
        else:
            pygame.draw.circle(screen, color, (cx, cy), max(8, rect.w // 4), 3)
            pygame.draw.line(screen, color, (cx - rect.w // 3, cy), (cx + rect.w // 3, cy), 2)
            pygame.draw.line(screen, color, (cx, cy - rect.h // 3), (cx, cy + rect.h // 3), 2)

    def draw_hotbar(self, screen, player, build_state):
        draw = getattr(build_state, "draw_hotbar", None)
        if draw is not None:
            draw()

    def draw_stats_panel(self, screen, player, weapon, buildings, wave):
        draw = getattr(buildings, "draw_info_panel", None)
        if draw is not None:
            draw()

    def draw_overlay(self, screen, game_state):
        game_state.draw_overlay()
        if not getattr(game_state, "game_over", False) and not getattr(game_state, "paused", False):
            self._draw_event_banners(screen, game_state)
        self._draw_low_hp_warning(screen, game_state)

    def _draw_event_banners(self, screen, state):
        colors = self._colors(state)
        scale = getattr(state, "ui_scale", 1.0)
        sw, _ = screen.get_size()
        y = getattr(state, "top_ui_h", 120) + int(44 * scale)
        if getattr(state, "wave_banner_timer", 0) > 0 and getattr(state, "wave_banner_text", ""):
            self._draw_banner(screen, state.wave_banner_text, pygame.Rect(sw // 2 - int(260 * scale), y, int(520 * scale), int(58 * scale)), colors["gold"], state.font)
            y += int(68 * scale)
        if getattr(state, "titan_banner_timer", 0) > 0:
            self._draw_banner(screen, state.t("titan_approaching"), pygame.Rect(sw // 2 - int(300 * scale), y, int(600 * scale), int(62 * scale)), colors["red"], state.font)

    def _draw_banner(self, screen, text, rect, accent, font):
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        panel.fill((11, 13, 18, 222))
        screen.blit(panel, rect)
        pygame.draw.rect(screen, accent, rect, 2, border_radius=8)
        pygame.draw.line(screen, accent, (rect.x + 20, rect.centery), (rect.x + 92, rect.centery), 3)
        pygame.draw.line(screen, accent, (rect.right - 92, rect.centery), (rect.right - 20, rect.centery), 3)
        self.draw_text_center(screen, text, rect, accent, font)

    def _draw_low_hp_warning(self, screen, state):
        player = getattr(state, "player", None)
        if player is None or getattr(state, "game_over", False):
            return
        hp_pct = getattr(player, "hp", 0) / max(1, getattr(player, "max_hp", 1))
        if hp_pct >= 0.3:
            return
        sw, sh = screen.get_size()
        pulse = 0.65 + 0.35 * math.sin(pygame.time.get_ticks() * 0.008)
        alpha = int((55 + (0.3 - hp_pct) * 130) * pulse)
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        edge = max(12, int(22 * getattr(state, "ui_scale", 1.0)))
        red = (225, 42, 40, max(36, min(125, alpha)))
        pygame.draw.rect(overlay, red, (0, 0, sw, edge))
        pygame.draw.rect(overlay, red, (0, sh - edge, sw, edge))
        pygame.draw.rect(overlay, red, (0, 0, edge, sh))
        pygame.draw.rect(overlay, red, (sw - edge, 0, edge, sh))
        screen.blit(overlay, (0, 0))

    def draw_text(self, screen, text, x, y, color, font):
        screen.blit(font.render(text, True, color), (x, y))

    def draw_text_center(self, screen, text, rect, color, font):
        image = font.render(text, True, color)
        screen.blit(image, image.get_rect(center=rect.center))

    def draw_panel(self, screen, rect, *, color=(18, 20, 25), alpha=210, border=True, border_color=(70, 75, 86), border_radius=8):
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        panel.fill((*color, alpha))
        screen.blit(panel, rect)
        if border:
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=border_radius)

    def draw_button(self, screen, buttons, key, rect, label, *, colors, active=False, disabled=False, font):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse) and not disabled
        if disabled:
            fill = (44, 47, 54)
            text_color = (118, 124, 130)
        elif active:
            fill = (58, 105, 104)
            text_color = colors["text"]
        elif hover:
            fill = (64, 68, 78)
            text_color = colors["gold"]
        else:
            fill = (35, 38, 46)
            text_color = colors["text"]
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, colors["hud_line"], rect, 2, border_radius=8)
        self.draw_text_center(screen, label, rect, text_color, font)
        buttons[key] = rect

    def draw_progress_bar(self, surface, rect, pct, fill, back, border_color):
        pygame.draw.rect(surface, back, rect)
        pygame.draw.rect(surface, fill, (rect.x, rect.y, int(rect.w * max(0, min(1, pct))), rect.h))
        pygame.draw.rect(surface, border_color, rect, 1)

    def draw_hotbar_slot(self, screen, buttons, key, rect, number, label, value, accent, *, active, colors, font, small_font):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        fill = (47, 55, 62) if active else ((45, 48, 58) if hover else (30, 34, 42))
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, accent if active else colors["hud_line"], rect, 2, border_radius=8)
        badge = pygame.Rect(rect.centerx - 22, rect.y + 10, 44, 34)
        pygame.draw.rect(screen, accent, badge, border_radius=6)
        self.draw_text_center(screen, number, badge, (15, 18, 22), font)
        self.draw_text_center(screen, label, pygame.Rect(rect.x + 8, rect.y + 48, rect.w - 16, 26), colors["text"], small_font)
        self.draw_text_center(screen, value, pygame.Rect(rect.x + 8, rect.y + 76, rect.w - 16, 22), accent, small_font)
        buttons[key] = rect

    def draw_select_card(self, screen, buttons, key, rect, title, subtitle="", *, active=False, accent, colors, small_font, tiny_font, ui_scale=1.0):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        fill = (48, 67, 68) if active else ((42, 46, 54) if hover else (27, 30, 37))
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, accent if active else colors["hud_line"], rect, 2, border_radius=8)
        title = self.fit_text(title, small_font, rect.w - 18)
        title_rect = pygame.Rect(rect.x + 8, rect.y + 8, rect.w - 16, max(22, int(26 * ui_scale)))
        self.draw_text_center(screen, title, title_rect, colors["text"], small_font)
        if subtitle:
            subtitle = self.fit_text(subtitle, tiny_font, rect.w - 18)
            subtitle_rect = pygame.Rect(rect.x + 8, rect.bottom - max(30, int(34 * ui_scale)), rect.w - 16, max(20, int(24 * ui_scale)))
            self.draw_text_center(screen, subtitle, subtitle_rect, accent if active else colors["muted"], tiny_font)
        buttons[key] = rect

    def fit_text(self, text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        trimmed = text
        while len(trimmed) > 4 and font.size(trimmed + "...")[0] > max_width:
            trimmed = trimmed[:-1].rstrip()
        return trimmed + "..."
