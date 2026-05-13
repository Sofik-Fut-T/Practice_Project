"""
ui/app.py — головний інтерфейс застосунку
Сучасний темний дизайн на Tkinter + ttk
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data import storage
from core.bmp_generator import METHODS, PALETTES, read_bmp_info, generate_bmp
from core.steganography import embed_message, extract_message


# ════════════════════════════════════════════════
#   КОЛЬОРОВА СХЕМА (темна, сучасна)
# ════════════════════════════════════════════════
C = {
    "bg":        "#1a1a2e",   # фон вікна
    "surface":   "#16213e",   # фон карток
    "surface2":  "#0f3460",   # фон виділених елементів
    "accent":    "#e94560",   # акцент (рожево-червоний)
    "accent2":   "#533483",   # другорядний акцент (фіолетовий)
    "text":      "#eaeaea",   # основний текст
    "text_dim":  "#8892a4",   # приглушений текст
    "success":   "#2ecc71",   # зелений
    "warning":   "#f39c12",   # помаранчевий
    "error":     "#e74c3c",   # червоний
    "entry_bg":  "#0d1b2a",   # фон полів введення
    "border":    "#2d3561",   # колір рамок
}


# ════════════════════════════════════════════════
#   ДОПОМІЖНІ КОМПОНЕНТИ
# ════════════════════════════════════════════════

def styled_button(parent, text, command, color=None, width=18, **kw):
    bg = color or C["accent"]
    # Hover-ефект
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=C["text"],
        activebackground=C["surface2"], activeforeground=C["text"],
        relief=tk.FLAT, cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        width=width, pady=7, padx=4,
        bd=0, **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=C["surface2"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def card_frame(parent, title="", **kw):
    outer = tk.Frame(parent, bg=C["border"], padx=1, pady=1)
    inner = tk.Frame(outer, bg=C["surface"], padx=14, pady=12, **kw)
    inner.pack(fill=tk.BOTH, expand=True)
    if title:
        tk.Label(
            inner, text=title,
            bg=C["surface"], fg=C["accent"],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 6))
    return outer, inner


def status_label(parent, textvariable=None, **kw):
    lbl = tk.Label(
        parent, textvariable=textvariable,
        bg=C["surface"], fg=C["text_dim"],
        font=("Segoe UI", 9), **kw
    )
    return lbl


# ════════════════════════════════════════════════
#   ГОЛОВНИЙ КЛАС
# ════════════════════════════════════════════════

class BMPApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BMP Editor")
        self.root.geometry("820x620")
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg"])

        # Намагаємось задати іконку (якщо є)
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        # ── Стан ──
        self.current_user: str | None = None
        self.current_bmp:  str | None = None

        self.method_var  = tk.StringVar(value="mandelbrot")
        self.palette_var = tk.StringVar(value="rainbow")
        self.status_var  = tk.StringVar(value="")

        self._setup_ttk_styles()
        self._build_ui()

    # ──────────────────────────────────────────
    #   TTK СТИЛІ
    # ──────────────────────────────────────────

    def _setup_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dark.TNotebook",
            background=C["bg"],
            borderwidth=0,
            tabmargins=[2, 4, 0, 0],
        )
        style.configure(
            "Dark.TNotebook.Tab",
            background=C["surface"],
            foreground=C["text_dim"],
            padding=[18, 8],
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.map(
            "Dark.TNotebook.Tab",
            background=[("selected", C["surface2"])],
            foreground=[("selected", C["text"])],
        )
        style.configure(
            "Dark.TFrame",
            background=C["bg"],
        )

    # ──────────────────────────────────────────
    #   ПОБУДОВА UI
    # ──────────────────────────────────────────

    def _build_ui(self):
        # ── Хедер ──
        header = tk.Frame(self.root, bg=C["surface2"], height=54)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="⬡  BMP Editor",
            bg=C["surface2"], fg=C["text"],
            font=("Segoe UI", 15, "bold")
        ).pack(side=tk.LEFT, padx=20, pady=8)

        self.lbl_user_badge = tk.Label(
            header, text="Не авторизовано",
            bg=C["accent2"], fg=C["text"],
            font=("Segoe UI", 9),
            padx=10, pady=3
        )
        self.lbl_user_badge.pack(side=tk.RIGHT, padx=14, pady=12)

        # ── Меню ──
        menubar = tk.Menu(self.root, bg=C["surface"], fg=C["text"],
                          activebackground=C["surface2"],
                          activeforeground=C["text"],
                          relief=tk.FLAT, bd=0)

        file_menu = tk.Menu(menubar, tearoff=0,
                            bg=C["surface"], fg=C["text"],
                            activebackground=C["surface2"],
                            activeforeground=C["text"])
        file_menu.add_command(label="📂  Відкрити BMP…", command=self.open_bmp)
        file_menu.add_separator()
        file_menu.add_command(label="🚪  Вийти",          command=self._on_close)
        menubar.add_cascade(label="Файл", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0,
                            bg=C["surface"], fg=C["text"],
                            activebackground=C["surface2"],
                            activeforeground=C["text"])
        help_menu.add_command(label="📖  Інструкція",    command=self._show_manual)
        help_menu.add_command(label="ℹ️   Про програму", command=self._show_about)
        help_menu.add_command(label="👥  Про авторів",   command=self._show_authors)
        menubar.add_cascade(label="Довідка", menu=help_menu)
        self.root.config(menu=menubar)

        # ── Notebook ──
        self.nb = ttk.Notebook(self.root, style="Dark.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.tab_auth  = tk.Frame(self.nb, bg=C["bg"])
        self.tab_gen   = tk.Frame(self.nb, bg=C["bg"])
        self.tab_stego = tk.Frame(self.nb, bg=C["bg"])
        self.tab_hist  = tk.Frame(self.nb, bg=C["bg"])

        self.nb.add(self.tab_auth,  text="  👤 Авторизація  ")
        self.nb.add(self.tab_gen,   text="  🎨 Генерація BMP  ")
        self.nb.add(self.tab_stego, text="  🔒 Стеганографія  ")
        self.nb.add(self.tab_hist,  text="  📋 Історія  ")

        self._build_auth_tab()
        self._build_gen_tab()
        self._build_stego_tab()
        self._build_hist_tab()

        # ── Статус-рядок ──
        status_bar = tk.Frame(self.root, bg=C["surface"], height=26)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        tk.Label(
            status_bar, textvariable=self.status_var,
            bg=C["surface"], fg=C["text_dim"],
            font=("Segoe UI", 8), anchor="w", padx=12
        ).pack(fill=tk.X, pady=4)

        self._lock_tabs()

    # ──────────────────────────────────────────
    #   ВКЛАДКА: АВТОРИЗАЦІЯ
    # ──────────────────────────────────────────

    def _build_auth_tab(self):
        f = self.tab_auth

        # Центрований контейнер
        center = tk.Frame(f, bg=C["bg"])
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Логотип
        tk.Label(
            center, text="⬡",
            bg=C["bg"], fg=C["accent"],
            font=("Segoe UI", 38)
        ).pack(pady=(0, 2))
        tk.Label(
            center, text="BMP Editor",
            bg=C["bg"], fg=C["text"],
            font=("Segoe UI", 22, "bold")
        ).pack()
        tk.Label(
            center, text="Авторизуйтесь для початку роботи",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 10)
        ).pack(pady=(2, 20))

        # Форма
        form_outer, form = card_frame(center)
        form_outer.pack(ipadx=30, ipady=10)

        def entry_row(parent, label_text):
            row = tk.Frame(parent, bg=C["surface"])
            row.pack(fill=tk.X, pady=5)
            tk.Label(
                row, text=label_text, width=16, anchor="e",
                bg=C["surface"], fg=C["text_dim"],
                font=("Segoe UI", 10)
            ).pack(side=tk.LEFT)
            e = tk.Entry(
                row, width=24,
                bg=C["entry_bg"], fg=C["text"],
                insertbackground=C["text"],
                relief=tk.FLAT,
                font=("Segoe UI", 10),
                bd=4
            )
            e.pack(side=tk.LEFT, padx=(6, 0))
            return e

        self.entry_username = entry_row(form, "Ім'я користувача:")
        self.entry_password = entry_row(form, "Пароль:")
        self.entry_password.config(show="●")

        # Кнопки
        btn_row = tk.Frame(form, bg=C["surface"])
        btn_row.pack(pady=(14, 4))

        styled_button(btn_row, "  Увійти  ",
                      self.do_login, color=C["accent"], width=12).pack(
            side=tk.LEFT, padx=6)
        styled_button(btn_row, "  Реєстрація  ",
                      self.do_register, color=C["accent2"], width=14).pack(
            side=tk.LEFT, padx=6)

        self.lbl_auth_msg = tk.Label(
            form, text="", bg=C["surface"],
            font=("Segoe UI", 9)
        )
        self.lbl_auth_msg.pack(pady=(4, 0))

        # Кнопка виходу (знизу)
        self.btn_logout = styled_button(
            center, "  Вийти з облікового запису  ",
            self.do_logout, color=C["surface2"], width=26
        )
        self.btn_logout.pack(pady=(14, 0))
        self.btn_logout.config(state=tk.DISABLED)

        # Enter = вхід
        self.entry_password.bind("<Return>", lambda e: self.do_login())
        self.entry_username.bind("<Return>", lambda e: self.entry_password.focus())

    # ──────────────────────────────────────────
    #   ВКЛАДКА: ГЕНЕРАЦІЯ BMP
    # ──────────────────────────────────────────

    def _build_gen_tab(self):
        f = self.tab_gen

        # ── Рядок файлу ──
        file_outer, file_inner = card_frame(f, "📂  Вихідний BMP-файл")
        file_outer.pack(fill=tk.X, padx=18, pady=(16, 8))

        file_row = tk.Frame(file_inner, bg=C["surface"])
        file_row.pack(fill=tk.X)

        self.lbl_gen_file = tk.Label(
            file_row, text="Файл не вибрано",
            bg=C["surface"], fg=C["text_dim"],
            font=("Segoe UI", 10), anchor="w"
        )
        self.lbl_gen_file.pack(side=tk.LEFT, fill=tk.X, expand=True)

        styled_button(
            file_row, "Вибрати…",
            self.open_bmp, color=C["surface2"], width=10
        ).pack(side=tk.RIGHT)

        # ── Два стовпці: метод + палітра ──
        columns = tk.Frame(f, bg=C["bg"])
        columns.pack(fill=tk.X, padx=18, pady=4)
        columns.columnconfigure(0, weight=1)
        columns.columnconfigure(1, weight=1)

        # Метод
        m_outer, m_inner = card_frame(columns, "🔧  Метод генерації")
        m_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        for key, (label, _) in METHODS.items():
            rb = tk.Radiobutton(
                m_inner, text=label,
                variable=self.method_var, value=key,
                bg=C["surface"], fg=C["text"],
                selectcolor=C["surface2"],
                activebackground=C["surface"],
                activeforeground=C["accent"],
                font=("Segoe UI", 10),
                cursor="hand2"
            )
            rb.pack(anchor="w", pady=4)

        # Палітра
        p_outer, p_inner = card_frame(columns, "🎨  Кольорова палітра")
        p_outer.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        for key, (label, _) in PALETTES.items():
            rb = tk.Radiobutton(
                p_inner, text=label,
                variable=self.palette_var, value=key,
                bg=C["surface"], fg=C["text"],
                selectcolor=C["surface2"],
                activebackground=C["surface"],
                activeforeground=C["accent"],
                font=("Segoe UI", 10),
                cursor="hand2"
            )
            rb.pack(anchor="w", pady=4)

        # ── Кнопка генерації ──
        gen_btn_frame = tk.Frame(f, bg=C["bg"])
        gen_btn_frame.pack(pady=14)

        styled_button(
            gen_btn_frame,
            "  🎨  Згенерувати та зберегти BMP  ",
            self.do_generate,
            color=C["accent"],
            width=34
        ).pack()

        self.lbl_gen_status = tk.Label(
            f, text="",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 9)
        )
        self.lbl_gen_status.pack()

    # ──────────────────────────────────────────
    #   ВКЛАДКА: СТЕГАНОГРАФІЯ
    # ──────────────────────────────────────────

    def _build_stego_tab(self):
        f = self.tab_stego

        # ── Файл ──
        file_outer, file_inner = card_frame(f, "📂  BMP-файл для стеганографії")
        file_outer.pack(fill=tk.X, padx=18, pady=(16, 8))

        file_row = tk.Frame(file_inner, bg=C["surface"])
        file_row.pack(fill=tk.X)

        self.lbl_stego_file = tk.Label(
            file_row, text="Файл не вибрано",
            bg=C["surface"], fg=C["text_dim"],
            font=("Segoe UI", 10), anchor="w"
        )
        self.lbl_stego_file.pack(side=tk.LEFT, fill=tk.X, expand=True)

        styled_button(
            file_row, "Вибрати…",
            self.open_bmp, color=C["surface2"], width=10
        ).pack(side=tk.RIGHT)

        # ── Повідомлення ──
        msg_outer, msg_inner = card_frame(f, "✉️  Повідомлення")
        msg_outer.pack(fill=tk.BOTH, expand=True, padx=18, pady=4)

        self.text_msg = tk.Text(
            msg_inner, height=6,
            bg=C["entry_bg"], fg=C["text"],
            insertbackground=C["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            padx=8, pady=6,
            bd=0
        )
        self.text_msg.pack(fill=tk.BOTH, expand=True)

        # Обмеження довжини — підказка
        tk.Label(
            msg_inner,
            text="💡 Повідомлення зберігається у молодших бітах пікселів (LSB-метод)",
            bg=C["surface"], fg=C["text_dim"],
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(4, 0))

        # ── Кнопки ──
        btn_row = tk.Frame(f, bg=C["bg"])
        btn_row.pack(pady=10)

        styled_button(
            btn_row, "  📥  Вкласти повідомлення  ",
            self.do_embed, color=C["accent"], width=24
        ).pack(side=tk.LEFT, padx=8)

        styled_button(
            btn_row, "  📤  Витягти повідомлення  ",
            self.do_extract, color=C["accent2"], width=24
        ).pack(side=tk.LEFT, padx=8)

        self.lbl_stego_status = tk.Label(
            f, text="",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 9)
        )
        self.lbl_stego_status.pack()

    # ──────────────────────────────────────────
    #   ВКЛАДКА: ІСТОРІЯ
    # ──────────────────────────────────────────

    def _build_hist_tab(self):
        f = self.tab_hist

        tk.Label(
            f, text="📋  Остання активність",
            bg=C["bg"], fg=C["text"],
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(16, 8), anchor="w", padx=20)

        # 4 картки
        self.hist_boxes: dict[str, tk.Text] = {}
        grid = tk.Frame(f, bg=C["bg"])
        grid.pack(fill=tk.BOTH, expand=True, padx=18)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        sections = [
            ("files",     "📁 Останні файли",               0, 0),
            ("modes",     "🎨 Режими генерації",             0, 1),
            ("embedded",  "📥 Вкладені повідомлення",        1, 0),
            ("extracted", "📤 Витягнуті повідомлення",       1, 1),
        ]

        for key, title, row, col in sections:
            outer, inner = card_frame(grid, title)
            outer.grid(row=row, column=col, sticky="nsew",
                       padx=5, pady=5, ipadx=2, ipady=2)

            box = tk.Text(
                inner, height=5,
                bg=C["entry_bg"], fg=C["text"],
                relief=tk.FLAT, font=("Segoe UI", 9),
                wrap=tk.WORD, state=tk.DISABLED,
                bd=0, padx=6, pady=4
            )
            box.pack(fill=tk.BOTH, expand=True)
            self.hist_boxes[key] = box

        # ── Кнопки завантаження останніх налаштувань ──
        bottom = tk.Frame(f, bg=C["bg"])
        bottom.pack(fill=tk.X, padx=18, pady=(4, 10))

        styled_button(
            bottom, "🔄 Оновити",
            self.refresh_history,
            color=C["surface2"], width=14
        ).pack(side=tk.LEFT, padx=(0, 8))

        styled_button(
            bottom, "↩️ Завантажити останній режим",
            self.load_last_mode,
            color=C["accent2"], width=26
        ).pack(side=tk.LEFT)

    # ──────────────────────────────────────────
    #   ЛОГІКА: АВТОРИЗАЦІЯ
    # ──────────────────────────────────────────

    def do_login(self):
        user = self.entry_username.get().strip()
        pwd  = self.entry_password.get()
        if not user or not pwd:
            self._auth_msg("Заповніть усі поля", C["warning"])
            return
        if storage.login(user, pwd):
            self.current_user = user
            self._auth_msg(f"✅  Вітаємо, {user}!", C["success"])
            self.lbl_user_badge.config(text=f"👤  {user}", bg=C["accent"])
            self.btn_logout.config(state=tk.NORMAL)
            self.status_var.set(f"Авторизовано як: {user}")
            self._unlock_tabs()
            self._restore_session()
            self.refresh_history()
            self.nb.select(self.tab_gen)
        else:
            self._auth_msg("❌  Невірний логін або пароль", C["error"])

    def do_register(self):
        user = self.entry_username.get().strip()
        pwd  = self.entry_password.get()
        if not user or not pwd:
            self._auth_msg("Заповніть усі поля", C["warning"])
            return
        if len(user) < 3:
            self._auth_msg("Ім'я мінімум 3 символи", C["warning"])
            return
        if len(pwd) < 4:
            self._auth_msg("Пароль мінімум 4 символи", C["warning"])
            return
        if storage.register(user, pwd):
            self._auth_msg(
                f"✅  Зареєстровано! Тепер увійдіть.", C["success"])
        else:
            self._auth_msg("❌  Користувач вже існує", C["error"])

    def do_logout(self):
        if self.current_user:
            self._save_session()
        self.current_user = None
        self.lbl_user_badge.config(text="Не авторизовано", bg=C["accent2"])
        self.btn_logout.config(state=tk.DISABLED)
        self.status_var.set("")
        self._auth_msg("Виконано вихід", C["text_dim"])
        self._lock_tabs()
        self.nb.select(self.tab_auth)

    def _auth_msg(self, text, color):
        self.lbl_auth_msg.config(text=text, fg=color)

    # ──────────────────────────────────────────
    #   ЛОГІКА: ФАЙЛ
    # ──────────────────────────────────────────

    def open_bmp(self):
        path = filedialog.askopenfilename(
            title="Відкрити 24-бітний BMP-файл",
            filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            read_bmp_info(path)
        except ValueError as e:
            messagebox.showerror("Помилка файлу", str(e))
            return

        self.current_bmp = path
        name = os.path.basename(path)

        self.lbl_gen_file.config(text=f"📄  {name}", fg=C["text"])
        self.lbl_stego_file.config(text=f"📄  {name}", fg=C["text"])
        self.status_var.set(f"Відкрито: {path}")

        if self.current_user:
            storage.save_file(self.current_user, path)
            self.refresh_history()

    # ──────────────────────────────────────────
    #   ЛОГІКА: ГЕНЕРАЦІЯ
    # ──────────────────────────────────────────

    def do_generate(self):
        if not self.current_bmp:
            messagebox.showwarning("Увага", "Спочатку виберіть вихідний BMP-файл")
            return

        out = filedialog.asksaveasfilename(
            title="Зберегти згенерований BMP",
            defaultextension=".bmp",
            filetypes=[("BMP files", "*.bmp")]
        )
        if not out:
            return

        method  = self.method_var.get()
        palette = self.palette_var.get()

        self.lbl_gen_status.config(text="⏳  Генерація…", fg=C["warning"])
        self.root.update()

        try:
            generate_bmp(self.current_bmp, out, method, palette)

            name = os.path.basename(out)
            self.lbl_gen_status.config(
                text=f"✅  Збережено: {name}", fg=C["success"])
            self.status_var.set(f"Збережено: {out}")

            if self.current_user:
                storage.save_mode(
                    self.current_user,
                    {"method": method, "palette": palette}
                )
                storage.save_file(self.current_user, out)
                self.refresh_history()

        except Exception as e:
            messagebox.showerror("Помилка генерації", str(e))
            self.lbl_gen_status.config(text="❌  Помилка", fg=C["error"])

    # ──────────────────────────────────────────
    #   ЛОГІКА: СТЕГАНОГРАФІЯ
    # ──────────────────────────────────────────

    def do_embed(self):
        if not self.current_bmp:
            messagebox.showwarning("Увага", "Спочатку виберіть BMP-файл")
            return
        msg = self.text_msg.get("1.0", tk.END).strip()
        if not msg:
            messagebox.showwarning("Увага", "Введіть повідомлення")
            return

        out = filedialog.asksaveasfilename(
            title="Зберегти BMP з прихованим повідомленням",
            defaultextension=".bmp",
            filetypes=[("BMP files", "*.bmp")]
        )
        if not out:
            return

        try:
            embed_message(self.current_bmp, out, msg)
            name = os.path.basename(out)
            self.lbl_stego_status.config(
                text=f"✅  Повідомлення вкладено → {name}", fg=C["success"])

            if self.current_user:
                storage.save_embedded(self.current_user, msg)
                storage.save_file(self.current_user, out)
                self.refresh_history()

        except Exception as e:
            messagebox.showerror("Помилка", str(e))
            self.lbl_stego_status.config(text="❌  Помилка", fg=C["error"])

    def do_extract(self):
        if not self.current_bmp:
            messagebox.showwarning("Увага", "Спочатку виберіть BMP-файл")
            return

        try:
            msg = extract_message(self.current_bmp)
            if msg:
                self.text_msg.delete("1.0", tk.END)
                self.text_msg.insert("1.0", msg)
                self.lbl_stego_status.config(
                    text="✅  Повідомлення успішно витягнуто!", fg=C["success"])

                if self.current_user:
                    storage.save_extracted(self.current_user, msg)
                    self.refresh_history()
            else:
                self.lbl_stego_status.config(
                    text="⚠️  У цьому файлі немає прихованого повідомлення",
                    fg=C["warning"])

        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    # ──────────────────────────────────────────
    #   ЛОГІКА: ІСТОРІЯ ТА СЕСІЯ
    # ──────────────────────────────────────────

    def refresh_history(self):
        if not self.current_user:
            return
        hist = storage.get_history(self.current_user)

        def to_text(items, key):
            if not items:
                return "—  немає записів"
            lines = []
            for i, item in enumerate(items, 1):
                if key == "modes" and isinstance(item, dict):
                    m = METHODS.get(item.get("method", ""), ("?",))[0]
                    p = PALETTES.get(item.get("palette", ""), ("?",))[0]
                    lines.append(f"{i}.  {m}  +  {p}")
                else:
                    s = str(item)
                    if key == "files":
                        s = os.path.basename(s)
                    lines.append(f"{i}.  {s[:55]}{'…' if len(s) > 55 else ''}")
            return "\n".join(lines)

        for key, box in self.hist_boxes.items():
            box.config(state=tk.NORMAL)
            box.delete("1.0", tk.END)
            box.insert("1.0", to_text(hist.get(key, []), key))
            box.config(state=tk.DISABLED)

    def load_last_mode(self):
        """Завантажує останній використаний режим генерації."""
        if not self.current_user:
            return
        hist = storage.get_history(self.current_user)
        modes = hist.get("modes", [])
        if not modes:
            messagebox.showinfo("Інформація", "Немає збережених режимів")
            return
        mode = modes[0]
        self.method_var.set(mode.get("method", "mandelbrot"))
        self.palette_var.set(mode.get("palette", "rainbow"))
        self.nb.select(self.tab_gen)
        self.lbl_gen_status.config(
            text="✅  Режим відновлено", fg=C["success"])

    def _save_session(self):
        if not self.current_user:
            return
        storage.save_session(self.current_user, {
            "bmp_path": self.current_bmp,
            "method":   self.method_var.get(),
            "palette":  self.palette_var.get(),
        })

    def _restore_session(self):
        sess = storage.get_session(self.current_user)
        if not sess:
            return
        if sess.get("method"):
            self.method_var.set(sess["method"])
        if sess.get("palette"):
            self.palette_var.set(sess["palette"])
        bmp = sess.get("bmp_path")
        if bmp and os.path.isfile(bmp):
            self.current_bmp = bmp
            name = os.path.basename(bmp)
            self.lbl_gen_file.config(text=f"📄  {name}", fg=C["text"])
            self.lbl_stego_file.config(text=f"📄  {name}", fg=C["text"])

    # ──────────────────────────────────────────
    #   ДОВІДКА
    # ──────────────────────────────────────────

    def _show_manual(self):
        win = self._popup("📖  Інструкція користувача", 500, 400)
        text = (
            "ІНСТРУКЦІЯ КОРИСТУВАЧА\n"
            "══════════════════════════════════════\n\n"
            "1. АВТОРИЗАЦІЯ\n"
            "   • Введіть ім'я та пароль → «Увійти».\n"
            "   • Перший раз — натисніть «Реєстрація».\n\n"
            "2. ГЕНЕРАЦІЯ BMP\n"
            "   • Відкрийте 24-бітний BMP через Файл → Відкрити.\n"
            "   • Оберіть метод генерації (3 варіанти):\n"
            "       🔮 Фрактал Мандельброта\n"
            "       ✨ Плазмовий ефект\n"
            "       💧 Концентричні хвилі\n"
            "   • Оберіть палітру (3 варіанти).\n"
            "   • Натисніть «Згенерувати та зберегти BMP».\n\n"
            "3. СТЕГАНОГРАФІЯ (LSB)\n"
            "   • Вкласти: відкрийте BMP, введіть текст\n"
            "     → «Вкласти повідомлення».\n"
            "   • Витягти: відкрийте BMP з повідомленням\n"
            "     → «Витягти повідомлення».\n\n"
            "4. ІСТОРІЯ\n"
            "   • Програма пам'ятає 3 останні файли,\n"
            "     режими та повідомлення для кожного користувача.\n"
            "   • «Завантажити останній режим» відновлює\n"
            "     останні налаштування генерації.\n\n"
            "5. При повторному вході — автоматично\n"
            "   відновлюються останні налаштування."
        )
        self._popup_text(win, text)

    def _show_about(self):
        win = self._popup("ℹ️  Про програму", 420, 300)
        text = (
            "BMP Editor  v1.0\n"
            "══════════════════════════════════════\n\n"
            "Застосунок для генерації та обробки\n"
            "24-бітних BMP-зображень.\n\n"
            "Можливості:\n"
            "  • 3 унікальні методи генерації\n"
            "  • 3 кольорові палітри\n"
            "  • Стеганографія (метод LSB)\n"
            "  • Авторизація та збереження сесій\n"
            "  • Журнал останніх дій\n\n"
            "Розроблено у межах командного проєкту.\n"
            "Python 3.10+  |  Tkinter  |  No dependencies"
        )
        self._popup_text(win, text)

    def _show_authors(self):
        win = self._popup("👥  Про авторів", 400, 280)
        text = (
            "АВТОРИ ПРОЄКТУ\n"
            "══════════════════════════════════════\n\n"
            "Учасник 1 — [Ваше ім'я]\n"
            "  Відповідає за: Генерацію BMP\n"
            "  (bmp_generator.py)\n\n"
            "Учасник 2 — [Ваше ім'я]\n"
            "  Відповідає за: Стеганографію\n"
            "  (steganography.py)\n\n"
            "Учасник 3 — [Ваше ім'я]\n"
            "  Відповідає за: Авторизацію та UI\n"
            "  (storage.py, app.py)\n\n"
            "GitHub: https://github.com/your-team/bmp-editor"
        )
        self._popup_text(win, text)

    def _popup(self, title: str, w: int, h: int) -> tk.Toplevel:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(f"{w}x{h}")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.grab_set()
        return win

    def _popup_text(self, win: tk.Toplevel, text: str):
        t = tk.Text(
            win, bg=C["entry_bg"], fg=C["text"],
            font=("Segoe UI", 10), relief=tk.FLAT,
            wrap=tk.WORD, padx=16, pady=12,
            bd=0, state=tk.NORMAL
        )
        t.insert("1.0", text)
        t.config(state=tk.DISABLED)
        t.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        styled_button(win, "Закрити", win.destroy,
                      color=C["surface2"], width=10).pack(pady=(0, 10))

    # ──────────────────────────────────────────
    #   УТИЛІТИ
    # ──────────────────────────────────────────

    def _lock_tabs(self):
        for i in (1, 2, 3):
            self.nb.tab(i, state="disabled")

    def _unlock_tabs(self):
        for i in (1, 2, 3):
            self.nb.tab(i, state="normal")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self._save_session()
        self.root.destroy()
