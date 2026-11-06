import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

TASKS_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def add_task(title, category, priority, due_date):
    tasks = load_tasks()
    new_task = {
        "id": len(tasks) + 1,
        "title": title,
        "category": category,
        "priority": priority,
        "due_date": due_date,
        "completed": False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return new_task

def analyze_task_with_ai(user_input):
    text = user_input.lower()
    if any(word in text for word in ["دراسة", "اختبار", "رياضيات", "فيزياء", "تحصيلي", "قدرات", "مذاكرة", "بحث"]):
        category = "دراسة 📚"
    elif any(word in text for word in ["برمجة", "كود", "python", "github", "مشروع", "تطوير", "تطبيق"]):
        category = "برمجة 💻"
    else:
        category = "شخصي ⭐"
        
    if any(word in text for word in ["ضروري", "هام", "عاجل", "اليوم", "فوراً", "اختبار"]):
        priority = "عالية 🔥"
    elif any(word in text for word in ["غداً", "قريباً", "الأسبوع القادم"]):
        priority = "متوسطة ⚡"
    else:
        priority = "منخفضة ☕"
        
    return {
        "title": user_input,
        "category": category,
        "priority": priority,
        "due_date": "قريبآ"
    }

class AITaskManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 نظام إدارة المهام الذكي - AI Task Manager")
        self.root.geometry("820x620")
        self.root.configure(bg="#F8FAFC")

        # تخصيص أسلوب الواجهة عبر ttk لتصبح عصرية
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#FFFFFF", 
                        foreground="#1E293B", 
                        rowheight=28, 
                        fieldbackground="#FFFFFF",
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", 
                        background="#0F172A", 
                        foreground="#FFFFFF", 
                        font=("Segoe UI", 10, "bold"))

        # العنوان الرئيسي بتصميم أنيق
        header_frame = tk.Frame(root, bg="#0F172A", height=70)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(
            header_frame, 
            text="✨ نظام إدارة المهام بالذكاء الاصطناعي ✨", 
            font=("Segoe UI", 16, "bold"), 
            bg="#0F172A", 
            fg="#F8FAFC"
        )
        title_label.pack(pady=18)

        # قسم الإدخال بلغة طبيعية
        input_container = tk.LabelFrame(root, text=" إدخال ذكي للمهام ", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#475569", bd=1, relief="solid")
        input_container.pack(fill="x", padx=20, pady=15)

        input_frame = tk.Frame(input_container, bg="#F8FAFC")
        input_frame.pack(fill="x", padx=10, pady=10)

        self.task_entry = tk.Entry(input_frame, font=("Segoe UI", 11), width=45, bd=1, relief="solid")
        self.task_entry.pack(side="left", padx=5, ipady=6)
        self.task_entry.insert(0, "اكتب مهمتك هنا (مثال: اختبار تحصيلي غداً ضروري جداً)...")
        self.task_entry.bind("<FocusIn>", self.clear_placeholder)

        add_btn = tk.Button(
            input_frame, 
            text="➕ تحليل وإضافة", 
            font=("Segoe UI", 10, "bold"), 
            bg="#10B981", 
            fg="white", 
            activebackground="#059669",
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=6,
            command=self.process_task
        )
        add_btn.pack(side="right", padx=5)

        # شريط أزرار الذكاء الاصطناعي التفاعلية
        ai_control_frame = tk.Frame(root, bg="#EEF2FF", bd=1, relief="solid")
        ai_control_frame.pack(fill="x", padx=20, pady=5)

        ai_label = tk.Label(ai_control_frame, text="⚡ المساعد الذكي:", font=("Segoe UI", 10, "bold"), bg="#EEF2FF", fg="#4F46E5")
        ai_label.pack(side="left", padx=12, pady=8)

        auto_sort_btn = tk.Button(
            ai_control_frame, 
            text="📊 ترتيب ذكي للأولويات", 
            font=("Segoe UI", 9, "bold"), 
            bg="#8B5CF6", 
            fg="white", 
            activebackground="#7C3AED",
            relief="flat",
            padx=10,
            pady=5,
            command=self.ai_auto_sort
        )
        auto_sort_btn.pack(side="left", padx=6)

        ai_advice_btn = tk.Button(
            ai_control_frame, 
            text="💡 نصيحة وتوجيه لجدولك", 
            font=("Segoe UI", 9, "bold"), 
            bg="#F59E0B", 
            fg="white", 
            activebackground="#D97706",
            relief="flat",
            padx=10,
            pady=5,
            command=self.ai_give_advice
        )
        ai_advice_btn.pack(side="left", padx=6)

        # جدول عرض المهام
        tree_container = tk.Frame(root, bg="#F8FAFC")
        tree_container.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "العنوان", "التصنيف", "الأولوية", "الحالة")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="#")
        self.tree.heading("العنوان", text="عنوان المهمة")
        self.tree.heading("التصنيف", text="التصنيف")
        self.tree.heading("الأولوية", text="الأولوية")
        self.tree.heading("الحالة", text="الحالة")

        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("العنوان", width=330, anchor="w")
        self.tree.column("التصنيف", width=100, anchor="center")
        self.tree.column("الأولوية", width=100, anchor="center")
        self.tree.column("الحالة", width=110, anchor="center")

        # شريط التمرير للجدول
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # أزرار التحكم السفلية
        btn_frame = tk.Frame(root, bg="#F8FAFC")
        btn_frame.pack(fill="x", padx=20, pady=15)

        complete_btn = tk.Button(
            btn_frame, 
            text="✅ تحديد كمكتملة", 
            font=("Segoe UI", 10, "bold"), 
            bg="#3B82F6", 
            fg="white", 
            activebackground="#2563EB",
            relief="flat",
            padx=12,
            pady=6,
            command=self.mark_completed
        )
        complete_btn.pack(side="left", padx=5)

        delete_btn = tk.Button(
            btn_frame, 
            text="🗑️ حذف المهمة", 
            font=("Segoe UI", 10, "bold"), 
            bg="#EF4444", 
            fg="white", 
            activebackground="#DC2626",
            relief="flat",
            padx=12,
            pady=6,
            command=self.delete_task
        )
        delete_btn.pack(side="left", padx=5)

        refresh_btn = tk.Button(
            btn_frame, 
            text="🔄 تحديث القائمة", 
            font=("Segoe UI", 10, "bold"), 
            bg="#64748B", 
            fg="white", 
            activebackground="#475569",
            relief="flat",
            padx=12,
            pady=6,
            command=self.refresh_list
        )
        refresh_btn.pack(side="right", padx=5)

        self.refresh_list()

    def clear_placeholder(self, event):
        if "اكتب مهمتك هنا" in self.task_entry.get():
            self.task_entry.delete(0, tk.END)

    def process_task(self):
        text = self.task_entry.get().strip()
        if not text or "اكتب مهمتك هنا" in text:
            messagebox.showwarning("تنبيه", "يرجى كتابة نص المهمة أولاً!")
            return

        ai_data = analyze_task_with_ai(text)
        add_task(ai_data['title'], ai_data['category'], ai_data['priority'], ai_data['due_date'])
        self.task_entry.delete(0, tk.END)
        self.refresh_list()
        messagebox.showinfo("🤖 تحليل الذكاء الاصطناعي", f"تم تحليل المهمة وإضافتها بنجاح:\n• التصنيف: {ai_data['category']}\n• الأولوية: {ai_data['priority']}")

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        tasks = load_tasks()
        for t in tasks:
            status = "✅ مكتملة" if t['completed'] else "⏳ قيد الانتظار"
            self.tree.insert("", "end", values=(t['id'], t['title'], t['category'], t['priority'], status))

    def mark_completed(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("تنبيه", "يرجى تحديد مهمة من الجدول أولاً!")
            return
        item_values = self.tree.item(selected_item, "values")
        task_id = int(item_values[0])

        tasks = load_tasks()
        for t in tasks:
            if t['id'] == task_id:
                t['completed'] = True
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
        tasks = [t for t in tasks if t['id'] != task_id]
        save_tasks(tasks)
        self.refresh_list()
        messagebox.showinfo("نجاح", "تم حذف المهمة بنجاح.")

    def ai_auto_sort(self):
        tasks = load_tasks()
        if not tasks:
            messagebox.showinfo("تنبيه", "لا توجد مهام لترتيبها.")
            return
        
        priority_weight = {"عالية 🔥": 1, "متوسطة ⚡": 2, "منخفضة ☕": 3}
        tasks.sort(key=lambda x: (priority_weight.get(x['priority'], 2), x['completed']))
        
        for idx, t in enumerate(tasks, 1):
            t['id'] = idx
            
        save_tasks(tasks)
        self.refresh_list()
        messagebox.showinfo("🤖 الترتيب الذكي", "تم إعادة ترتيب مهامك بناءً على مستوى الأهمية بذكاء!")

    def ai_give_advice(self):
        tasks = load_tasks()
        if not tasks:
            messagebox.showinfo("🤖 توجيه المساعد الذكي", "جدولك خفيف جداً اليوم! أضف بعض المهام لنبدأ التنظيم.")
            return

        pending_tasks = [t for t in tasks if not t['completed']]
        high_priority = [t for t in pending_tasks if "عالية" in t['priority']]

        advice = f"لديك {len(pending_tasks)} مهمة نشطة قيد التنفيذ.\n"
        if high_priority:
            advice += f"🔥 انتبه: لديك {len(high_priority)} مهام ملحة وعالية الأولوية، ابدأ بها أولاً!\n"
        else:
            advice += f"✨ أداء ممتاز، جدولك مستقر ومنظم للغاية اليوم."

        messagebox.showinfo("💡 توجيهات المساعد الذكي", advice)

if __name__ == "__main__":
    root = tk.Tk()
    app = AITaskManagerGUI(root)
    root.mainloop()