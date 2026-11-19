import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.error
import urllib.request
import webbrowser

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

APP_VERSION = "2.1.0"
TASKS_FILE = "tasks.json"
UPDATE_CONFIG_FILE = "update_config.json"

VALID_CATEGORIES = {"دراسة 📚", "برمجة 💻", "شخصي ⭐"}
VALID_PRIORITIES = {"عالية 🔥", "متوسطة ⚡", "منخفضة ☕"}


def load_update_config():
    default_config = {
        "current_version": APP_VERSION,
        "update_manifest_url": ""
    }
    if not os.path.exists(UPDATE_CONFIG_FILE):
        with open(UPDATE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        return default_config

    with open(UPDATE_CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                return default_config
            return {
                "current_version": str(data.get("current_version") or APP_VERSION),
                "update_manifest_url": str(data.get("update_manifest_url") or "").strip()
            }
        except json.JSONDecodeError:
            return default_config


def _parse_version_tuple(version_str):
    parts = re.findall(r"\d+", str(version_str))
    return tuple(int(p) for p in parts) if parts else (0,)


def _compare_versions(current_ver, latest_ver):
    cur_t = _parse_version_tuple(current_ver)
    lat_t = _parse_version_tuple(latest_ver)
    max_len = max(len(cur_t), len(lat_t))
    cur_t += (0,) * (max_len - len(cur_t))
    lat_t += (0,) * (max_len - len(lat_t))
    if lat_t > cur_t:
        return 1
    if lat_t < cur_t:
        return -1
    return 0


def check_for_updates_manually():
    config = load_update_config()
    current_ver = config["current_version"]
    manifest_url = config["update_manifest_url"]

    if not manifest_url:
        return {
            "status": "unconfigured",
            "current_version": current_ver,
            "message": (
                f"النسخة الحالية: v{current_ver}\n\n"
                f"لم يتم تحديد رابط التحديث بعد في ملف ({UPDATE_CONFIG_FILE}).\n"
                "أضف رابط ملف JSON للتحديث داخل الحقل update_manifest_url ثم أعد المحاولة."
            )
        }

    try:
        req = urllib.request.Request(
            manifest_url,
            headers={"User-Agent": f"AITaskManager/{current_ver}"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw_data = resp.read().decode("utf-8")
            payload = json.loads(raw_data)

        if not isinstance(payload, dict) or not payload.get("latest_version"):
            return {
                "status": "error",
                "current_version": current_ver,
                "message": "ملف التحديث لا يحتوي على حقل latest_version بشكل صحيح."
            }

        latest_ver = str(payload["latest_version"]).strip()
        download_url = str(payload.get("download_url") or "").strip()
        notes = str(payload.get("release_notes") or "تحسينات وإصلاحات عامة.").strip()

        cmp_result = _compare_versions(current_ver, latest_ver)
        if cmp_result > 0:
            return {
                "status": "update_available",
                "current_version": current_ver,
                "latest_version": latest_ver,
                "download_url": download_url,
                "release_notes": notes
            }

        return {
            "status": "up_to_date",
            "current_version": current_ver,
            "latest_version": latest_ver,
            "message": f"أنت تستخدم أحدث إصدار بالفعل (v{current_ver})."
        }

    except urllib.error.URLError:
        return {
            "status": "error",
            "current_version": current_ver,
            "message": "تعذر الاتصال بخادم التحديث. تحقق من اتصالك بالإنترنت أو من صحة الرابط."
        }
    except Exception as e:
        return {
            "status": "error",
            "current_version": current_ver,
            "message": f"حدث خطأ أثناء التحقق من التحديثات:\n{e}"
        }


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)


def add_task(title, category, priority, due_date):
    tasks = load_tasks()
    new_id = max([t.get("id", 0) for t in tasks], default=0) + 1
    new_task = {
        "id": new_id,
        "title": title,
        "category": category,
        "priority": priority,
        "due_date": due_date,
        "completed": False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return new_task


def add_tasks_bulk(task_items):
    tasks = load_tasks()
    current_max_id = max([t.get("id", 0) for t in tasks], default=0)
    added = []
    for item in task_items:
        current_max_id += 1
        new_task = {
            "id": current_max_id,
            "title": item["title"],
            "category": item["category"],
            "priority": item["priority"],
            "due_date": item["due_date"],
            "completed": False
        }
        tasks.append(new_task)
        added.append(new_task)
    save_tasks(tasks)
    return added


def _rule_based_single_task(part_text, full_text):
    clean_part = part_text.strip(" -،.؛")
    if not clean_part:
        clean_part = full_text.strip()

    combined = f"{clean_part} {full_text}".lower()

    if any(word in combined for word in ["دراسة", "اختبار", "رياضيات", "فيزياء", "كيمياء", "تحصيلي", "قدرات", "مذاكرة", "بحث", "واجب", "تجميعات"]):
        category = "دراسة 📚"
    elif any(word in combined for word in ["برمجة", "كود", "python", "github", "مشروع", "تطوير", "تطبيق", "واجهة"]):
        category = "برمجة 💻"
    else:
        category = "شخصي ⭐"

    if any(word in combined for word in ["ضروري", "هام", "عاجل", "اليوم", "فوراً", "اختبار", "مهم"]):
        priority = "عالية 🔥"
    elif any(word in combined for word in ["غداً", "غدا", "قريباً", "قريبا", "الأسبوع القادم", "ساعتين", "مذاكرة"]):
        priority = "متوسطة ⚡"
    else:
        priority = "منخفضة ☕"

    if "اليوم" in combined:
        due_date = "اليوم"
    elif "غداً" in combined or "غدا" in combined:
        due_date = "غداً"
    else:
        due_date = "قريباً"

    return {
        "title": clean_part,
        "category": category,
        "priority": priority,
        "due_date": due_date,
        "mode": "محلي (احتياطي)"
    }


def _rule_based_split_tasks(user_input):
    raw_parts = re.split(r"\s+(?:و|ثم)\s+|[،,؛]+", user_input.strip())
    meaningful_parts = [p.strip() for p in raw_parts if len(p.strip()) >= 3]

    if len(meaningful_parts) <= 1:
        return [_rule_based_single_task(user_input, user_input)]

    return [_rule_based_single_task(part, user_input) for part in meaningful_parts]


def analyze_tasks_with_ai(user_input):
    fallback_items = _rule_based_split_tasks(user_input)
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not GENAI_AVAILABLE or not api_key:
        return fallback_items

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
أنت مساعد ذكي لإدارة المهام. حلل النص التالي وقسّمه إلى قائمة مهام فرعية واضحة وقابلة للتنفيذ إذا كان يحتوي على أكثر من خطوة أو مهمة، أو أعد مهمة واحدة إذا كان مهمة بسيطة.
أعد كائن JSON يحتوي على مفتاح "tasks" وهو مصفوفة، وكل عنصر فيها يحتوي على الحقول التالية:
- "title": عنوان مختصر وواضح للمهمة الفرعية
- "category": اختر واحدة فقط من: "دراسة 📚"، "برمجة 💻"، "شخصي ⭐"
- "priority": اختر واحدة فقط من: "عالية 🔥"، "متوسطة ⚡"، "منخفضة ☕"
- "due_date": موعد مختصر مثل "اليوم"، "غداً"، أو "قريباً"

النص: "{user_input}"
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        parsed = json.loads(response.text)
        raw_tasks = parsed.get("tasks") if isinstance(parsed, dict) else None
        if not isinstance(raw_tasks, list) or not raw_tasks:
            return fallback_items

        default_item = fallback_items[0]
        cleaned_items = []
        for idx, item in enumerate(raw_tasks):
            if not isinstance(item, dict):
                continue
            fb = fallback_items[idx] if idx < len(fallback_items) else default_item
            title = str(item.get("title") or fb["title"]).strip()
            category = item.get("category") if item.get("category") in VALID_CATEGORIES else fb["category"]
            priority = item.get("priority") if item.get("priority") in VALID_PRIORITIES else fb["priority"]
            due_date = str(item.get("due_date") or fb["due_date"]).strip()
            if title:
                cleaned_items.append({
                    "title": title,
                    "category": category,
                    "priority": priority,
                    "due_date": due_date,
                    "mode": "Gemini AI"
                })

        return cleaned_items if cleaned_items else fallback_items
    except Exception:
        return fallback_items


def generate_ai_advice(tasks):
    pending = [t for t in tasks if not t.get("completed")]
    if not pending:
        return "جدولك خفيف جداً اليوم! أضف مهمة جديدة لنبدأ تنظيم وقتك بذكاء."

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if GENAI_AVAILABLE and api_key:
        try:
            client = genai.Client(api_key=api_key)
            summary = json.dumps(pending, ensure_ascii=False)
            prompt = f"""
أنت مساعد إنتاجية ذكي. بناءً على قائمة المهام النشطة التالية، قدم نصيحة عملية مختصرة (من 3 إلى 4 أسطر باللغة العربية) توضح بماذا يبدأ المستخدم ولماذا:
{summary}
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4),
            )
            if response.text and response.text.strip():
                return response.text.strip()
        except Exception:
            pass

    high_priority = [t for t in pending if "عالية" in t.get("priority", "")]
    advice = f"لديك {len(pending)} مهام نشطة قيد التنفيذ.\n"
    if high_priority:
        advice += f"🔥 ابدأ بـ ({high_priority[0]['title']}) لأنها ذات أولوية عالية."
    else:
        advice += "✨ جدولك متوازن؛ ابدأ بأقصر مهمة لإنجاز سريع ثم انتقل للأطول."
    return advice


class AITaskManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"🤖 نظام إدارة المهام الذكي - v{APP_VERSION}")
        self.root.geometry("880x650")
        self.dark_mode = True

        self.palettes = {
            "dark": {
                "bg": "#0F172A",
                "panel": "#1E293B",
                "header_bg": "#020617",
                "fg": "#F8FAFC",
                "muted": "#94A3B8",
                "entry_bg": "#0F172A",
                "entry_fg": "#F8FAFC",
                "ai_bar": "#1E1B4B",
                "ai_fg": "#A5B4FC",
                "tree_bg": "#1E293B",
                "tree_fg": "#F8FAFC",
                "tree_head_bg": "#334155",
            },
            "light": {
                "bg": "#F8FAFC",
                "panel": "#F8FAFC",
                "header_bg": "#0F172A",
                "fg": "#0F172A",
                "muted": "#475569",
                "entry_bg": "#FFFFFF",
                "entry_fg": "#0F172A",
                "ai_bar": "#EEF2FF",
                "ai_fg": "#4F46E5",
                "tree_bg": "#FFFFFF",
                "tree_fg": "#1E293B",
                "tree_head_bg": "#0F172A",
            },
        }

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.header_frame = tk.Frame(root, height=70)
        self.header_frame.pack(fill="x")

        self.title_label = tk.Label(
            self.header_frame,
            text=f"✨ نظام إدارة المهام بالذكاء الاصطناعي (v{APP_VERSION}) ✨",
            font=("Segoe UI", 15, "bold"),
        )
        self.title_label.pack(side="left", padx=20, pady=18)

        self.theme_btn = tk.Button(
            self.header_frame,
            text="☀️ وضع نهاري",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="white",
            relief="flat",
            padx=10,
            pady=5,
            command=self.toggle_theme,
        )
        self.theme_btn.pack(side="right", padx=(6, 20), pady=18)

        self.update_btn = tk.Button(
            self.header_frame,
            text="🔎 التحقق من التحديثات",
            font=("Segoe UI", 9, "bold"),
            bg="#0EA5E9",
            fg="white",
            activebackground="#0284C7",
            relief="flat",
            padx=10,
            pady=5,
            command=self.manual_update_check,
        )
        self.update_btn.pack(side="right", padx=6, pady=18)

        self.input_container = tk.LabelFrame(
            root,
            text=" إدخال ذكي وتقسيم تلقائي للمهام ",
            font=("Segoe UI", 10, "bold"),
            bd=1,
            relief="solid",
        )
        self.input_container.pack(fill="x", padx=20, pady=12)

        self.input_frame = tk.Frame(self.input_container)
        self.input_frame.pack(fill="x", padx=10, pady=10)

        self.placeholder_text = "اكتب مهمة أو خطة (مثال: مذاكرة تحصيلي رياضيات وحل تجميعات غداً)..."
        self.task_entry = tk.Entry(self.input_frame, font=("Segoe UI", 11), width=48, bd=1, relief="solid")
        self.task_entry.pack(side="left", padx=5, ipady=6, fill="x", expand=True)
        self.task_entry.insert(0, self.placeholder_text)
        self.task_entry.bind("<FocusIn>", self.clear_placeholder)
        self.task_entry.bind("<FocusOut>", self.restore_placeholder)
        self.task_entry.bind("<Return>", lambda event: self.process_task())

        add_btn = tk.Button(
            self.input_frame,
            text="➕ تحليل وتقسيم",
            font=("Segoe UI", 10, "bold"),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=6,
            command=self.process_task,
        )
        add_btn.pack(side="right", padx=5)

        self.ai_control_frame = tk.Frame(root, bd=1, relief="solid")
        self.ai_control_frame.pack(fill="x", padx=20, pady=4)

        self.ai_label = tk.Label(
            self.ai_control_frame,
            text="⚡ المساعد الذكي:",
            font=("Segoe UI", 10, "bold"),
        )
        self.ai_label.pack(side="left", padx=12, pady=8)

        auto_sort_btn = tk.Button(
            self.ai_control_frame,
            text="📊 ترتيب ذكي للأولويات",
            font=("Segoe UI", 9, "bold"),
            bg="#8B5CF6",
            fg="white",
            activebackground="#7C3AED",
            relief="flat",
            padx=10,
            pady=5,
            command=self.ai_auto_sort,
        )
        auto_sort_btn.pack(side="left", padx=6)

        ai_advice_btn = tk.Button(
            self.ai_control_frame,
            text="💡 نصيحة وتوجيه لجدولك",
            font=("Segoe UI", 9, "bold"),
            bg="#F59E0B",
            fg="white",
            activebackground="#D97706",
            relief="flat",
            padx=10,
            pady=5,
            command=self.ai_give_advice,
        )
        ai_advice_btn.pack(side="left", padx=6)

        self.tree_container = tk.Frame(root)
        self.tree_container.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "العنوان", "التصنيف", "الأولوية", "الموعد", "الحالة")
        self.tree = ttk.Treeview(self.tree_container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("ID", text="#")
        self.tree.heading("العنوان", text="عنوان المهمة")
        self.tree.heading("التصنيف", text="التصنيف")
        self.tree.heading("الأولوية", text="الأولوية")
        self.tree.heading("الموعد", text="الموعد")
        self.tree.heading("الحالة", text="الحالة")

        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("العنوان", width=290, anchor="w")
        self.tree.column("التصنيف", width=105, anchor="center")
        self.tree.column("الأولوية", width=105, anchor="center")
        self.tree.column("الموعد", width=90, anchor="center")
        self.tree.column("الحالة", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(fill="x", padx=20, pady=12)

        complete_btn = tk.Button(
            self.btn_frame,
            text="✅ تحديد كمكتملة",
            font=("Segoe UI", 10, "bold"),
            bg="#3B82F6",
            fg="white",
            activebackground="#2563EB",
            relief="flat",
            padx=12,
            pady=6,
            command=self.mark_completed,
        )
        complete_btn.pack(side="left", padx=5)

        delete_btn = tk.Button(
            self.btn_frame,
            text="🗑️ حذف المهمة",
            font=("Segoe UI", 10, "bold"),
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            relief="flat",
            padx=12,
            pady=6,
            command=self.delete_task,
        )
        delete_btn.pack(side="left", padx=5)

        refresh_btn = tk.Button(
            self.btn_frame,
            text="🔄 تحديث القائمة",
            font=("Segoe UI", 10, "bold"),
            bg="#64748B",
            fg="white",
            activebackground="#475569",
            relief="flat",
            padx=12,
            pady=6,
            command=self.refresh_list,
        )
        refresh_btn.pack(side="right", padx=5)

        self.apply_theme()
        self.refresh_list()

    def manual_update_check(self):
        result = check_for_updates_manually()
        status = result.get("status")

        if status == "update_available":
            msg = (
                f"يتوفر إصدار جديد: v{result['latest_version']}\n"
                f"النسخة الحالية: v{result['current_version']}\n\n"
                f"ملاحظات الإصدار:\n{result['release_notes']}\n\n"
                "هل ترغب في فتح رابط التحميل الآن؟"
            )
            if messagebox.askyesno("🔄 تحديث متوفر", msg):
                if result.get("download_url"):
                    webbrowser.open(result["download_url"])
                else:
                    messagebox.showinfo("تنبيه", "لم يتم تحديد رابط تحميل (download_url) في ملف التحديث.")
        elif status == "up_to_date":
            messagebox.showinfo("✅ لا توجد تحديثات", result["message"])
        elif status == "unconfigured":
            messagebox.showinfo("⚙️ إعداد التحديث اليدوي", result["message"])
        else:
            messagebox.showwarning("⚠️ تعذر التحقق من التحديث", result["message"])

    def apply_theme(self):
        p = self.palettes["dark" if self.dark_mode else "light"]
        self.root.configure(bg=p["bg"])
        self.header_frame.configure(bg=p["header_bg"])
        self.title_label.configure(bg=p["header_bg"], fg="#F8FAFC")
        self.theme_btn.configure(text="☀️ وضع نهاري" if self.dark_mode else "🌙 وضع ليلي")

        self.input_container.configure(bg=p["panel"], fg=p["muted"])
        self.input_frame.configure(bg=p["panel"])
        self.task_entry.configure(
            bg=p["entry_bg"],
            fg=p["entry_fg"],
            insertbackground=p["entry_fg"],
        )

        self.ai_control_frame.configure(bg=p["ai_bar"])
        self.ai_label.configure(bg=p["ai_bar"], fg=p["ai_fg"])

        self.tree_container.configure(bg=p["bg"])
        self.btn_frame.configure(bg=p["bg"])

        self.style.configure(
            "Treeview",
            background=p["tree_bg"],
            foreground=p["tree_fg"],
            rowheight=28,
            fieldbackground=p["tree_bg"],
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Treeview.Heading",
            background=p["tree_head_bg"],
            foreground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
        )

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def clear_placeholder(self, event):
        if self.task_entry.get() == self.placeholder_text:
            self.task_entry.delete(0, tk.END)

    def restore_placeholder(self, event):
        if not self.task_entry.get().strip():
            self.task_entry.insert(0, self.placeholder_text)

    def process_task(self):
        text = self.task_entry.get().strip()
        if not text or text == self.placeholder_text:
            messagebox.showwarning("تنبيه", "يرجى كتابة نص المهمة أولاً!")
            return

        ai_items = analyze_tasks_with_ai(text)
        added_tasks = add_tasks_bulk(ai_items)
        self.task_entry.delete(0, tk.END)
        self.restore_placeholder(None)
        self.refresh_list()

        mode = ai_items[0]["mode"] if ai_items else "محلي (احتياطي)"
        preview = "\n".join(
            f"• {t['title']} ({t['category']} | {t['priority']} | {t['due_date']})"
            for t in added_tasks
        )
        messagebox.showinfo(
            "🤖 تحليل وتقسيم الذكاء الاصطناعي",
            f"تمت إضافة {len(added_tasks)} مهمة ({mode}):\n{preview}",
        )

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        tasks = load_tasks()
        for t in tasks:
            status = "✅ مكتملة" if t.get("completed") else "⏳ قيد الانتظار"
            due = t.get("due_date") or "قريباً"
            self.tree.insert(
                "",
                "end",
                values=(t.get("id"), t.get("title"), t.get("category"), t.get("priority"), due, status),
            )

    def mark_completed(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("تنبيه", "يرجى تحديد مهمة من الجدول أولاً!")
            return
        item_values = self.tree.item(selected_item, "values")
        task_id = int(item_values[0])

        tasks = load_tasks()
        for t in tasks:
            if t.get("id") == task_id:
                t["completed"] = True
                break
        save_tasks(tasks)
        self.refresh_list()

    def delete_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("تنبيه", "يرجى تحديد مهمة للحذف!")
            return
        item_values = self.tree.item(selected_item, "values")
        task_id = int(item_values[0])

        tasks = load_tasks()
        tasks = [t for t in tasks if t.get("id") != task_id]
        save_tasks(tasks)
        self.refresh_list()
        messagebox.showinfo("نجاح", "تم حذف المهمة بنجاح.")

    def ai_auto_sort(self):
        tasks = load_tasks()
        if not tasks:
            messagebox.showinfo("تنبيه", "لا توجد مهام لترتيبها.")
            return

        priority_weight = {"عالية 🔥": 1, "متوسطة ⚡": 2, "منخفضة ☕": 3}
        tasks.sort(key=lambda x: (priority_weight.get(x.get("priority"), 2), bool(x.get("completed"))))

        for idx, t in enumerate(tasks, 1):
            t["id"] = idx

        save_tasks(tasks)
        self.refresh_list()
        messagebox.showinfo("🤖 الترتيب الذكي", "تم إعادة ترتيب مهامك بناءً على مستوى الأهمية وحالة الإنجاز!")

    def ai_give_advice(self):
        tasks = load_tasks()
        advice = generate_ai_advice(tasks)
        messagebox.showinfo("💡 توجيهات المساعد الذكي", advice)


if __name__ == "__main__":
    root = tk.Tk()
    app = AITaskManagerGUI(root)
    root.mainloop()