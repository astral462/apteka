import customtkinter as ctk
import psycopg2
from psycopg2 import Error
from datetime import datetime

broker = redis.Redis(host='localhost', port=6379, decode_responses=True)



class PharmacyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Аптека")
        self.geometry("1280x850")
        self.minsize(1100, 750)

        self.green = "#168447"
        self.light_green = "#eef8f2"
        self.border = "#d9dedb"
        self.text = "#202522"
        self.gray = "#737a76"
        self.red = "#b3261e"

        self.connection = psycopg2.connect(
            host=" ",
            port=" ",
            user=" a",
            password=" ",
            database=" "
        )

        self.cart = []
        self.search_results = []
        self.selected_symptoms = []
        self.selected_product = None
        self.payment_method = "Готівка"
        self.last_receipt = None

        # Значення фільтрів/сортування
        self.sort_value = "Популярність"
        self.price_from = None
        self.price_to = None

        # Контейнер для прокручування всього інтерфейсу.
        # Усі сторінки будуть малюватися всередині scroll_frame.
        self.main_canvas = ctk.CTkCanvas(
            self,
            highlightthickness=0,
            bg="#ffffff"
        )
        self.main_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.scrollbar = ctk.CTkScrollbar(
            self,
            orientation="vertical",
            command=self.main_canvas.yview
        )
        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.main_canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.scroll_frame = ctk.CTkFrame(
            self.main_canvas,
            fg_color="#ffffff"
        )

        self.canvas_window = self.main_canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw"
        )

        self.scroll_frame.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.main_canvas.bind(
            "<Configure>",
            self.resize_scroll_frame
        )

        self.main_canvas.bind_all(
            "<MouseWheel>",
            self.on_mousewheel
        )
        self.main_canvas.bind_all(
            "<Button-4>",
            self.on_mousewheel_linux
        )
        self.main_canvas.bind_all(
            "<Button-5>",
            self.on_mousewheel_linux
        )

        self.protocol("WM_DELETE_WINDOW", self.close_app)

        # Таблиці для чеків створюються автоматично, якщо їх ще немає.
        self.create_receipt_tables()

        self.show_search_page()

    # ---------------------------------------------------------
    # БАЗА ДАНИХ
    # ---------------------------------------------------------

    def create_receipt_tables(self):

        """Створює таблиці чеків та позицій чека, якщо їх ще немає."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pharmacy_receipts (
                        id BIGSERIAL PRIMARY KEY,
                        receipt_number VARCHAR(50) UNIQUE NOT NULL,
                        sale_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        client_phone VARCHAR(50),
                        client_name VARCHAR(255),
                        payment_method VARCHAR(50) NOT NULL,
                        total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pharmacy_receipt_items (
                        id BIGSERIAL PRIMARY KEY,
                        receipt_id BIGINT NOT NULL
                            REFERENCES pharmacy_receipts(id)
                            ON DELETE CASCADE,
                        product_id VARCHAR(255),
                        product_name VARCHAR(255) NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 1,
                        price NUMERIC(12, 2) NOT NULL DEFAULT 0,
                        total_price NUMERIC(12, 2) NOT NULL DEFAULT 0
                    )
                """)

                self.connection.commit()


        except Error as e:
            self.connection.rollback()
            # Якщо у користувача немає прав CREATE TABLE,
            # програма все одно запускається, а помилку покаже під час покупки.
            print("Не вдалося створити таблиці чеків:", e)



    # ---------------------------------------------------------
    # SCROLL
    # ---------------------------------------------------------

    def update_scroll_region(self, event=None):
        self.main_canvas.configure(
            scrollregion=self.main_canvas.bbox("all")
        )

    def resize_scroll_frame(self, event):
        self.main_canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def on_mousewheel(self, event):
        # Windows / macOS
        if event.delta:
            self.main_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

    def on_mousewheel_linux(self, event):
        # Linux
        if event.num == 4:
            self.main_canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.main_canvas.yview_scroll(3, "units")

    def scroll_to_top(self):
        self.main_canvas.yview_moveto(0)

    # ---------------------------------------------------------
    # UI HELPERS
    # ---------------------------------------------------------

    def clear_window(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.main_canvas.yview_moveto(0)

    def title_label(self, text):
        return ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=46, weight="bold"),
            text_color=self.green
        )

    def card(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color="white",
            border_width=1,
            border_color=self.border,
            corner_radius=14
        )

    def green_button(self, parent, text, command=None, height=48):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=height,
            corner_radius=9,
            fg_color=self.green,
            hover_color="#116d3a",
            font=ctk.CTkFont(size=16, weight="bold")
        )

    def outline_button(self, parent, text, command=None, height=42):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=height,
            corner_radius=9,
            fg_color="white",
            hover_color=self.light_green,
            border_width=1,
            border_color="#72b88e",
            text_color=self.green,
            font=ctk.CTkFont(size=15, weight="bold")
        )

    def show_message(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("520x240")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.green
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=450,
            justify="center",
            font=ctk.CTkFont(size=15),
            text_color=self.text
        ).pack(padx=25, pady=10)

        self.green_button(
            dialog,
            "OK",
            command=dialog.destroy,
            height=42
        ).pack(pady=15)

    # ---------------------------------------------------------
    # ПОШУК
    # ---------------------------------------------------------

    def show_search_page(self):
        self.clear_window()
        page_parent = self.scroll_frame
        self.scroll_to_top()

        header = ctk.CTkFrame(page_parent, fg_color="transparent")
        header.pack(fill="x", padx=35, pady=(25, 5))

        ctk.CTkLabel(header, text="Аптека", font=ctk.CTkFont(size=46, weight="bold"), text_color=self.green).pack()

        search_card = self.card(page_parent)
        search_card.pack(fill="x", padx=35, pady=(25, 12))

        ctk.CTkLabel(
            search_card,
            text="Пошук препарату",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=35, pady=(25, 12))

        self.medicine_entry = ctk.CTkEntry(
            search_card,
            placeholder_text="Введіть назву препарату...",
            height=58,
            font=ctk.CTkFont(size=18),
            border_color="#cfd5d1"
        )
        self.medicine_entry.pack(fill="x", padx=35, pady=(0, 25))
        self.medicine_entry.bind("<Return>", lambda event: self.search_medicines())

        symptoms_card = self.card(page_parent)
        symptoms_card.pack(fill="x", padx=35, pady=12)

        ctk.CTkLabel(
            symptoms_card,
            text="Симптоми",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=35, pady=(25, 12))

        self.symptom_entry = ctk.CTkEntry(
            symptoms_card,
            placeholder_text="Пошук симптомів...",
            height=55,
            font=ctk.CTkFont(size=17),
            border_color="#cfd5d1"
        )
        self.symptom_entry.pack(fill="x", padx=35, pady=(0, 20))

        symptoms = [
            "Головний біль", "Температура", "Кашель", "Нежить",
            "Біль у горлі", "Алергія", "Біль у животі", "Спазми"
        ]

        buttons_frame = ctk.CTkFrame(symptoms_card, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=35, pady=(0, 28))

        self.symptom_buttons = {}

        for index, symptom in enumerate(symptoms):
            button = self.outline_button(
                buttons_frame,
                symptom,
                command=lambda s=symptom: self.select_symptom(s),
                height=52
            )
            button.grid(
                row=index // 4,
                column=index % 4,
                padx=7,
                pady=7,
                sticky="ew"
            )
            self.symptom_buttons[symptom] = button

        for column in range(4):
            buttons_frame.grid_columnconfigure(column, weight=1)

        bottom = ctk.CTkFrame(page_parent, fg_color="transparent")
        bottom.pack(fill="x", padx=35, pady=(10, 25))

        self.green_button(
            bottom,
            "Пошук",
            command=self.search_medicines,
            height=58
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.outline_button(
            bottom,
            f"Кошик ({len(self.cart)})",
            command=self.show_checkout_page,
            height=58
        ).pack(side="right", padx=(8, 0))

    def select_symptom(self, symptom):
        button = self.symptom_buttons[symptom]

        if symptom in self.selected_symptoms:
            self.selected_symptoms.remove(symptom)
            button.configure(
                fg_color="white",
                text_color=self.green
            )
        else:
            self.selected_symptoms.append(symptom)
            button.configure(
                fg_color=self.light_green,
                text_color=self.green
            )

    def search_medicines(self):
        start = time.perf_counter()
        search_text = self.medicine_entry.get().strip()
        symptom_text = self.symptom_entry.get().strip()

        conditions = []
        params = []

        if search_text:
            value = f"%{search_text}%"
            conditions.append("""
                (
                    product_name ILIKE %s
                    OR active_ingredients ILIKE %s
                    OR manufacturer_name ILIKE %s
                    OR diseases ILIKE %s
                )
            """)
            params.extend([value, value, value, value])

        if symptom_text:
            conditions.append("diseases ILIKE %s")
            params.append(f"%{symptom_text}%")

        for symptom in self.selected_symptoms:
            conditions.append("diseases ILIKE %s")
            params.append(f"%{symptom}%")

        # Якщо нічого не введено — показуємо всі препарати.
        where = ("WHERE " + " OR ".join(conditions)) if conditions else ""

        query = f"""
            SELECT DISTINCT ON (product_id)
                id,
                product_id,
                product_name,
                product_category,
                product_description,
                manufacturer_name,
                manufacturer_country,
                price,
                quantity_in_stock,
                diseases,
                active_ingredients,
                dosage,
                contraindications,
                prescription_required
            FROM pharmacy
            {where}
            ORDER BY product_id, sale_date DESC NULLS LAST, id DESC
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.search_results = cursor.fetchall()

            # Після пошуку застосовуємо сортування/ціну.
            self.apply_filters_and_sort()
            self.show_results_page()

        except Error as e:
            self.show_database_error(e)

        time_seconds = (end - start) * 1000
        print(f"Час - {round(time_seconds, 2)} ms")

    # ---------------------------------------------------------
    # РЕЗУЛЬТАТИ + ФІЛЬТРИ + СОРТУВАННЯ
    # ---------------------------------------------------------

    def apply_filters_and_sort(self):
        products = list(self.search_results)

        filtered = []

        for product in products:
            price = product[7]

            try:
                price_value = float(price) if price is not None else 0
            except (ValueError, TypeError):
                price_value = 0

            if self.price_from is not None and price_value < self.price_from:
                continue

            if self.price_to is not None and price_value > self.price_to:
                continue

            filtered.append(product)

        if self.sort_value == "Ціна: від меншої":
            filtered.sort(
                key=lambda p: float(p[7] or 0)
            )
        elif self.sort_value == "Ціна: від більшої":
            filtered.sort(
                key=lambda p: float(p[7] or 0),
                reverse=True
            )
        else:
            # Спочатку товари з більшою кількістю проданих одиниць.
            filtered.sort(
                key=lambda p: self.get_purchased_value(p),
                reverse=True
            )

        self.search_results = filtered

    def get_purchased_value(self, product):
        """
        product має 14 полів.
        purchased_quantity не вибирається в основному SELECT,
        тому для сортування використовуємо 0, якщо цього поля немає.
        """
        return 0

    def apply_results_filters(self):
        try:
            from_text = self.price_from_entry.get().strip().replace(",", ".")
            to_text = self.price_to_entry.get().strip().replace(",", ".")

            self.price_from = float(from_text) if from_text else None
            self.price_to = float(to_text) if to_text else None

            if self.price_from is not None and self.price_from < 0:
                raise ValueError

            if self.price_to is not None and self.price_to < 0:
                raise ValueError

            if (
                self.price_from is not None
                and self.price_to is not None
                and self.price_from > self.price_to
            ):
                raise ValueError

            self.sort_value = self.sort_combo.get()
            self.apply_filters_and_sort()
            self.refresh_results_only()

        except ValueError:
            self.show_message(
                "Невірна ціна",
                "Введіть коректний діапазон цін."
            )

    def on_sort_change(self, value):
        self.sort_value = value
        self.apply_filters_and_sort()
        self.refresh_results_only()

    def refresh_results_only(self):
        # Найпростіший і стабільний спосіб оновити картки.
        self.show_results_page()

    def show_results_page(self):
        self.clear_window()
        page_parent = self.scroll_frame
        self.scroll_to_top()

        top = ctk.CTkFrame(page_parent, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(20, 8))

        top_left = ctk.CTkFrame(top, fg_color="transparent")
        top_left.pack(side="left")

        self.outline_button(
            top_left,
            "← Назад до пошуку",
            command=self.show_search_page,
            height=42
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            top_left,
            text="Аптека",
            font=ctk.CTkFont(size=44, weight="bold"),
            text_color=self.green
        ).pack(side="left")

        self.outline_button(
            top,
            f"Кошик ({len(self.cart)})",
            command=self.show_checkout_page,
            height=42
        ).pack(side="right")

        search_card = self.card(page_parent)
        search_card.pack(fill="x", padx=28, pady=10)

        ctk.CTkLabel(
            search_card,
            text="Ваш пошук",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=22, pady=(18, 8))

        search_text = ""
        if hasattr(page_parent, "medicine_entry"):
            try:
                search_text = self.medicine_entry.get().strip()
            except Exception:
                pass

        if not search_text:
            search_text = "Усі препарати"

        ctk.CTkLabel(
            search_card,
            text=search_text,
            height=45,
            fg_color="#f5f7f6",
            corner_radius=8,
            anchor="w",
            font=ctk.CTkFont(size=16),
            text_color=self.text
        ).pack(fill="x", padx=22, pady=(0, 14))

        if self.selected_symptoms:
            ctk.CTkLabel(
                search_card,
                text="Обрані симптоми: " + ", ".join(self.selected_symptoms),
                font=ctk.CTkFont(size=14),
                text_color=self.green
            ).pack(anchor="w", padx=22, pady=(0, 15))

        filters = self.card(page_parent)
        filters.pack(fill="x", padx=28, pady=8)

        ctk.CTkLabel(
            filters,
            text="Ціна, ₴",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.text
        ).grid(row=0, column=0, padx=20, pady=(18, 8), sticky="w")

        self.price_from_entry = ctk.CTkEntry(
            filters,
            width=130,
            height=40,
            placeholder_text="Від"
        )
        self.price_from_entry.grid(
            row=1, column=0,
            padx=(20, 5), pady=(0, 18)
        )

        self.price_to_entry = ctk.CTkEntry(
            filters,
            width=130,
            height=40,
            placeholder_text="До"
        )
        self.price_to_entry.grid(
            row=1, column=1,
            padx=5, pady=(0, 18)
        )

        if self.price_from is not None:
            self.price_from_entry.insert(0, str(self.price_from))

        if self.price_to is not None:
            self.price_to_entry.insert(0, str(self.price_to))

        ctk.CTkLabel(
            filters,
            text="Сортування",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.text
        ).grid(
            row=0, column=2,
            padx=(70, 15), pady=(18, 8), sticky="w"
        )

        self.sort_combo = ctk.CTkComboBox(
            filters,
            values=[
                "Популярність",
                "Ціна: від меншої",
                "Ціна: від більшої"
            ],
            width=270,
            height=40,
            command=self.on_sort_change
        )
        self.sort_combo.grid(
            row=1, column=2,
            padx=(70, 15), pady=(0, 18), sticky="w"
        )
        self.sort_combo.set(self.sort_value)

        self.green_button(
            filters,
            "Застосувати",
            command=self.apply_results_filters,
            height=40
        ).grid(
            row=1, column=3,
            padx=(10, 20), pady=(0, 18)
        )

        ctk.CTkLabel(
            page_parent,
            text=f"Знайдено препаратів: {len(self.search_results)}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=28, pady=(12, 5))

        if not self.search_results:
            ctk.CTkLabel(
                self,
                text="Препарати не знайдені",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=self.gray
            ).pack(pady=40)
            return

        products_frame = ctk.CTkFrame(page_parent, fg_color="transparent")
        products_frame.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=5
        )

        for index, product in enumerate(self.search_results):
            self.create_product_card(
                products_frame,
                product,
                index // 4,
                index % 4
            )

        for column in range(4):
            products_frame.grid_columnconfigure(column, weight=1)

    # ---------------------------------------------------------
    # ТОВАР
    # ---------------------------------------------------------

    def create_product_card(self, parent, product, row, column):
        name = product[2]
        description = product[4] or product[3] or "Опис відсутній"
        price = product[7]
        stock = product[8]

        card = self.card(parent)
        card.grid(
            row=row,
            column=column,
            padx=6,
            pady=7,
            sticky="nsew"
        )

        image_box = ctk.CTkFrame(
            card,
            height=100,
            fg_color="#f5f7f6",
            corner_radius=8
        )
        image_box.pack(fill="x", padx=12, pady=(12, 8))
        image_box.pack_propagate(False)

        ctk.CTkLabel(
            image_box,
            text="Фото\nпрепарату",
            text_color="#9aa29e",
            font=ctk.CTkFont(size=15)
        ).pack(expand=True)

        ctk.CTkLabel(
            card,
            text=name or "Без назви",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=14, pady=(2, 4))

        ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=self.gray,
            wraplength=240,
            justify="left"
        ).pack(anchor="w", padx=14)

        ctk.CTkLabel(
            card,
            text=f"{float(price):.2f} ₴" if price is not None else "Ціна не вказана",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=14, pady=7)

        ctk.CTkLabel(
            card,
            text=(
                f"В наявності: {stock} шт."
                if stock is not None
                else "Наявність не вказана"
            ),
            font=ctk.CTkFont(size=11),
            text_color=self.gray
        ).pack(anchor="w", padx=14, pady=(0, 7))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 10))

        self.outline_button(
            buttons,
            "Деталі",
            command=lambda p=product: self.show_product_page(p),
            height=35
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 4)
        )

        self.green_button(
            buttons,
            "В кошик",
            command=lambda p=product: self.add_to_cart(p),
            height=35
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(4, 0)
        )

    def add_to_cart(self, product=None):
        if product is None:
            product = self.selected_product

        if product is None:
            return

        stock = product[8]
        count = sum(
            1 for item in self.cart
            if item[1] == product[1]
        )

        if stock is not None and count >= int(stock):
            self.show_message(
                "Немає товару",
                "Цього препарату більше немає в наявності."
            )
            return

        self.cart.append(product)
        self.show_results_page()

    def show_product_page(page_parent, product=None):
        if product is not None:
            self.selected_product = product

        product = self.selected_product

        if product is None:
            self.show_results_page()
            return

        self.clear_window()
        page_parent = self.scroll_frame
        self.scroll_to_top()

        (
            db_id,
            product_id,
            name,
            category,
            description,
            manufacturer,
            manufacturer_country,
            price,
            stock,
            diseases,
            active_ingredients,
            dosage,
            contraindications,
            prescription_required
        ) = product

        navigation = ctk.CTkFrame(page_parent, fg_color="transparent")
        navigation.pack(fill="x", padx=32, pady=(22, 12))

        self.outline_button(
            navigation,
            "← Назад до результатів",
            command=self.show_results_page,
            height=42
        ).pack(side="left")

        self.outline_button(
            navigation,
            f"Кошик ({len(self.cart)})",
            command=self.show_checkout_page,
            height=42
        ).pack(side="right")

        ctk.CTkLabel(
            page_parent,
            text="Аптека",
            font=ctk.CTkFont(size=44, weight="bold"),
            text_color=self.green
        ).pack(pady=(0, 18))

        main = self.card(page_parent)
        main.pack(fill="x", padx=32, pady=8)

        image_box = ctk.CTkFrame(
            main,
            width=450,
            height=320,
            fg_color="#f5f7f6",
            corner_radius=12
        )
        image_box.pack(side="left", padx=24, pady=24)
        image_box.pack_propagate(False)

        ctk.CTkLabel(
            image_box,
            text="Фото препарату",
            text_color="#9aa29e",
            font=ctk.CTkFont(size=22)
        ).pack(expand=True)

        info = ctk.CTkFrame(main, fg_color="transparent")
        info.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(10, 25),
            pady=24
        )

        ctk.CTkLabel(
            info,
            text=name or "Без назви",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", pady=(5, 20))

        self.info_row(
            info,
            "Ціна",
            f"{float(price):.2f} ₴" if price is not None else "—"
        )
        self.info_row(
            info,
            "В наявності",
            f"{stock} шт." if stock is not None else "—"
        )
        self.info_row(info, "Категорія", category or "—")
        self.info_row(info, "Виробник", manufacturer or "—")
        self.info_row(
            info,
            "Країна виробника",
            manufacturer_country or "—"
        )
        self.info_row(
            info,
            "Активна речовина",
            active_ingredients or "—"
        )
        self.info_row(
            info,
            "Рецепт",
            "Так" if prescription_required else "Ні"
        )

        details = self.card(page_parent)
        details.pack(fill="x", padx=32, pady=10)

        self.detail_row(
            details,
            "Показання / симптоми",
            diseases or "—"
        )
        self.detail_row(
            details,
            "Дозування",
            dosage or "—"
        )
        self.detail_row(
            details,
            "Протипоказання",
            contraindications or "—"
        )
        self.detail_row(
            details,
            "Опис",
            description or "—"
        )

        self.green_button(
            page_parent,
            "Додати в кошик",
            command=lambda: self.add_to_cart(product),
            height=55
        ).pack(fill="x", padx=32, pady=(8, 25))

    def info_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            row,
            text=label,
            width=160,
            anchor="w",
            font=ctk.CTkFont(size=14),
            text_color=self.gray
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=value,
            anchor="w",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.text
        ).pack(side="left", fill="x", expand=True)

    def detail_row(self, parent, title, text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            row,
            text=title,
            width=220,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.text
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=text,
            anchor="w",
            justify="left",
            wraplength=850,
            font=ctk.CTkFont(size=14),
            text_color=self.text
        ).pack(side="left", fill="x", expand=True)

    # ---------------------------------------------------------
    # КОШИК / ОПЛАТА
    # ---------------------------------------------------------

    def show_checkout_page(self):
        self.clear_window()
        page_parent = self.scroll_frame
        self.scroll_to_top()

        navigation = ctk.CTkFrame(page_parent, fg_color="transparent")
        navigation.pack(fill="x", padx=25, pady=(20, 0))

        self.outline_button(
            navigation,
            "← Назад до товарів",
            command=self.show_results_page,
            height=42
        ).pack(side="left")

        ctk.CTkLabel(
            page_parent,
            text="Оформлення продажу",
            font=ctk.CTkFont(size=44, weight="bold"),
            text_color=self.green
        ).pack(pady=(15, 15))

        if not self.cart:
            empty = self.card(page_parent)
            empty.pack(fill="x", padx=30, pady=30)

            ctk.CTkLabel(
                empty,
                text="Кошик порожній",
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color=self.text
            ).pack(pady=(35, 10))

            ctk.CTkLabel(
                empty,
                text="Додайте препарат у кошик, щоб оформити продаж.",
                font=ctk.CTkFont(size=16),
                text_color=self.gray
            ).pack(pady=10)

            self.green_button(
                empty,
                "Повернутися до пошуку",
                command=self.show_search_page,
                height=48
            ).pack(pady=(10, 35))

            return

        content = ctk.CTkFrame(page_parent, fg_color="transparent")
        content.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=5
        )

        left = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )
        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        receipt = self.card(left)
        receipt.pack(fill="x", pady=5)

        ctk.CTkLabel(
            receipt,
            text=f"Чек ({len(self.cart)} товарів)",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=18, pady=(18, 12))

        total = 0

        for index, product in enumerate(self.cart, 1):
            price = float(product[7] or 0)
            total += price

            row = ctk.CTkFrame(
                receipt,
                fg_color="transparent"
            )
            row.pack(
                fill="x",
                padx=18,
                pady=7
            )

            for value, width in [
                (str(index), 30),
                (product[2] or "Без назви", 270),
                ("1", 50),
                (f"{price:.2f} ₴", 100)
            ]:
                ctk.CTkLabel(
                    row,
                    text=value,
                    width=width,
                    anchor="w",
                    text_color=self.text
                ).pack(side="left")

            self.outline_button(
                row,
                "🗑",
                command=lambda p=product: self.remove_item(p),
                height=30
            ).pack(side="right")

        ctk.CTkLabel(
            receipt,
            text=f"Разом: {total:.2f} ₴",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.green
        ).pack(anchor="e", padx=20, pady=(12, 20))

        client = self.card(left)
        client.pack(fill="x", pady=5)

        ctk.CTkLabel(
            client,
            text="Клієнт",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=18, pady=(18, 10))

        client_row = ctk.CTkFrame(
            client,
            fg_color="transparent"
        )
        client_row.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.client_phone_entry = ctk.CTkEntry(
            client_row,
            placeholder_text="Введіть номер телефону...",
            height=42
        )
        self.client_phone_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.outline_button(
            client_row,
            "Знайти",
            command=self.find_client,
            height=42
        ).pack(side="left", padx=8)

        self.client_name_entry = ctk.CTkEntry(
            client_row,
            placeholder_text="Клієнт не вибраний",
            height=42
        )
        self.client_name_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

        payment = self.card(left)
        payment.pack(fill="x", pady=5)

        ctk.CTkLabel(
            payment,
            text="Оплата",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.text
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 10)
        )

        methods = ctk.CTkFrame(
            payment,
            fg_color="transparent"
        )
        methods.pack(fill="x", padx=18)

        self.payment_buttons = {}

        for method in ["Готівка", "Картка", "Термінал"]:
            button = self.outline_button(
                methods,
                method,
                command=lambda m=method: self.select_payment(m),
                height=42
            )
            button.pack(
                side="left",
                fill="x",
                expand=True,
                padx=4
            )
            self.payment_buttons[method] = button

        self.update_payment_buttons()

        ctk.CTkLabel(
            payment,
            text="Отримано від клієнта",
            text_color=self.gray
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 5)
        )

        self.received_entry = ctk.CTkEntry(
            payment,
            placeholder_text="0,00 ₴",
            height=42
        )
        self.received_entry.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        self.green_button(
            left,
            "Оформити продаж та створити чек",
            command=self.finish_sale,
            height=55
        ).pack(fill="x", pady=(10, 0))

        right = self.card(content)
        right.pack(
            side="right",
            fill="y",
            padx=(10, 0),
            pady=5
        )

        ctk.CTkLabel(
            right,
            text="Поточна оплата",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.text
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        ctk.CTkLabel(
            right,
            text="Спосіб оплати",
            text_color=self.gray
        ).pack(anchor="w", padx=20, pady=(10, 3))

        ctk.CTkLabel(
            right,
            text=self.payment_method,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.green
        ).pack(anchor="w", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            right,
            text="Товарів у кошику",
            text_color=self.gray
        ).pack(anchor="w", padx=20, pady=(0, 3))

        ctk.CTkLabel(
            right,
            text=str(len(self.cart)),
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color=self.green
        ).pack(padx=20, pady=10)

    def update_payment_buttons(self):
        if not hasattr(self, "payment_buttons"):
            return

        for method, button in self.payment_buttons.items():
            if method == self.payment_method:
                button.configure(
                    fg_color=self.green,
                    text_color="white",
                    hover_color="#116d3a"
                )
            else:
                button.configure(
                    fg_color="white",
                    text_color=self.green,
                    hover_color=self.light_green
                )

    def remove_item(self, product):
        if product in self.cart:
            self.cart.remove(product)

        self.show_checkout_page()

    def find_client(self):
        phone = self.client_phone_entry.get().strip()

        if not phone:
            self.show_message(
                "Клієнт",
                "Введіть номер телефону."
            )
            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT user_name, user_surname, user_phone
                    FROM pharmacy
                    WHERE user_phone = %s
                    ORDER BY sale_date DESC NULLS LAST, id DESC
                    LIMIT 1
                """, (phone,))

                client = cursor.fetchone()

            self.client_name_entry.delete(0, "end")

            if client:
                name = (
                    f"{client[0] or ''} "
                    f"{client[1] or ''}"
                ).strip()

                self.client_name_entry.insert(
                    0,
                    name or client[2]
                )
            else:
                self.client_name_entry.insert(
                    0,
                    "Клієнт не знайдений"
                )

        except Error as e:
            self.show_database_error(e)

    def select_payment(self, method):
        self.payment_method = method
        self.update_payment_buttons()

        # Оновлюємо напис на сторінці.
        self.show_checkout_page()

    # ---------------------------------------------------------
    # ПРОДАЖ + ЧЕК
    # ---------------------------------------------------------

    def generate_receipt_number(self):
        now = datetime.now()
        return now.strftime("R%Y%m%d%H%M%S%f")

    def finish_sale(self):
        if not self.cart:
            self.show_message(
                "Кошик",
                "Кошик порожній."
            )
            return

        total = sum(
            float(product[7] or 0)
            for product in self.cart
        )

        received_text = self.received_entry.get().strip().replace(",", ".")

        if received_text:
            try:
                received = float(received_text)
            except ValueError:
                self.show_message(
                    "Помилка",
                    "У полі «Отримано від клієнта» введіть число."
                )
                return

            if received < total and self.payment_method == "Готівка":
                self.show_message(
                    "Недостатньо коштів",
                    f"Сума покупки: {total:.2f} ₴\n"
                    f"Отримано: {received:.2f} ₴"
                )
                return

        client_phone = self.client_phone_entry.get().strip()
        client_name = self.client_name_entry.get().strip()

        if client_name == "Клієнт не знайдений":
            client_name = ""

        receipt_number = self.generate_receipt_number()

        try:
            with self.connection.cursor() as cursor:
                # 1. Створюємо чек.
                cursor.execute("""
                    INSERT INTO pharmacy_receipts (
                        receipt_number,
                        client_phone,
                        client_name,
                        payment_method,
                        total_amount
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    receipt_number,
                    client_phone or None,
                    client_name or None,
                    self.payment_method,
                    total
                ))

                receipt_id = cursor.fetchone()[0]

                # 2. Додаємо кожен товар до чека.
                for product in self.cart:
                    db_id = product[0]
                    product_id = str(product[1]) if product[1] is not None else None
                    product_name = product[2] or "Без назви"
                    price = float(product[7] or 0)

                    cursor.execute("""
                        INSERT INTO pharmacy_receipt_items (
                            receipt_id,
                            product_id,
                            product_name,
                            quantity,
                            price,
                            total_price
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        receipt_id,
                        product_id,
                        product_name,
                        1,
                        price,
                        price
                    ))

                    # 3. Оновлюємо склад та інформацію про продаж.
                    cursor.execute("""
                        UPDATE pharmacy
                        SET quantity_in_stock =
                                CASE
                                    WHEN quantity_in_stock IS NULL
                                        THEN NULL
                                    ELSE quantity_in_stock - 1
                                END,
                            purchased_quantity =
                                COALESCE(purchased_quantity, 0) + 1,
                            sale_date = CURRENT_TIMESTAMP,
                            total_price = %s,
                            payment_method = %s
                        WHERE id = %s
                          AND (
                              quantity_in_stock IS NULL
                              OR quantity_in_stock > 0
                          )
                    """, (
                        price,
                        self.payment_method,
                        db_id
                    ))

                    if cursor.rowcount == 0:
                        raise Exception(
                            f"Товар «{product_name}» "
                            f"більше не доступний на складі."
                        )

                self.connection.commit()

            # Зберігаємо дані останнього чека перед очищенням кошика.
            self.last_receipt = {
                "number": receipt_number,
                "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "client": client_name or "Не вказано",
                "phone": client_phone or "Не вказано",
                "payment": self.payment_method,
                "items": [
                    {
                        "name": product[2] or "Без назви",
                        "price": float(product[7] or 0)
                    }
                    for product in self.cart
                ],
                "total": total
            }

            self.cart.clear()
            self.show_receipt_page()

        except Exception as e:
            self.connection.rollback()
            self.show_database_error(e)

    def show_receipt_page(self):
        self.clear_window()
        page_parent = self.scroll_frame
        self.scroll_to_top()

        receipt = self.last_receipt

        if not receipt:
            self.show_search_page()
            return

        ctk.CTkLabel(
            page_parent,
            text="Чек створено",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color=self.green
        ).pack(pady=(30, 10))

        card = self.card(page_parent)
        card.pack(
            fill="both",
            expand=True,
            padx=180,
            pady=20
        )

        ctk.CTkLabel(
            card,
            text=f"Чек № {receipt['number']}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.text
        ).pack(anchor="w", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            card,
            text=receipt["date"],
            font=ctk.CTkFont(size=14),
            text_color=self.gray
        ).pack(anchor="w", padx=30, pady=(0, 15))

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(
            info,
            text=f"Клієнт: {receipt['client']}",
            font=ctk.CTkFont(size=15),
            text_color=self.text
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=f"Телефон: {receipt['phone']}",
            font=ctk.CTkFont(size=15),
            text_color=self.text
        ).pack(anchor="w", pady=3)

        ctk.CTkLabel(
            info,
            text=f"Оплата: {receipt['payment']}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.green
        ).pack(anchor="w", pady=(3, 15))

        line = ctk.CTkFrame(
            card,
            height=1,
            fg_color=self.border
        )
        line.pack(fill="x", padx=30, pady=5)

        for index, item in enumerate(receipt["items"], 1):
            row = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )
            row.pack(fill="x", padx=30, pady=7)

            ctk.CTkLabel(
                row,
                text=f"{index}. {item['name']}",
                anchor="w",
                font=ctk.CTkFont(size=15),
                text_color=self.text
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                row,
                text=f"{item['price']:.2f} ₴",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=self.text
            ).pack(side="right")

        ctk.CTkLabel(
            card,
            text=f"РАЗОМ: {receipt['total']:.2f} ₴",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.green
        ).pack(anchor="e", padx=30, pady=(20, 15))

        buttons = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        buttons.pack(fill="x", padx=30, pady=(5, 25))

        self.green_button(
            buttons,
            "Новий пошук",
            command=self.show_search_page,
            height=50
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.outline_button(
            buttons,
            "Перейти до товарів",
            command=self.show_results_page,
            height=50
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))


    def show_database_error(page_parent, error):
        self.clear_window()
        page_parent = self.scroll_frame
        self.scroll_to_top()

        ctk.CTkLabel(
            page_parent,
            text="Помилка бази даних",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.red
        ).pack(pady=(80, 15))

        ctk.CTkLabel(
            page_parent,
            text=str(error),
            wraplength=1000,
            justify="left",
            text_color=self.text
        ).pack(
            padx=40,
            pady=10
        )

        self.outline_button(
            page_parent,
            "Повернутися",
            command=self.show_search_page,
            height=45
        ).pack(pady=20)

    def close_app(self):
        try:
            self.connection.close()
        except Exception:
            pass

        self.destroy()


if __name__ == "__main__":
    app = PharmacyApp()
    app.mainloop()
