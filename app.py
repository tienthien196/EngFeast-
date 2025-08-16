# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import csv
import os
import requests
import random
import hashlib
from datetime import datetime

# config
UNSPLASH_ACCESS_KEY = "_bu-idIBdSauNOT-jkeM13quMLjfKvja4EMg1xi1Zk4"
PATH_ACCOUNTS = r"./data/account.csv"
PATH_QUESTION_DB = r"./data/vocabulary_database_600_unique.csv"

class EnglishLearning:
    def __init__(self, csv_file=PATH_QUESTION_DB, account_file=PATH_ACCOUNTS):
        self.app = Flask(__name__, template_folder="templates")
        self.app.secret_key = "engfeast_bnbnbnbnbnbnbnnbnbnbnbnbnbnbnbnbnbnbnbnbnbnbnbnbbbbnbnb"  # Nên đổi bằng os.urandom(24)
        self.csv_file = csv_file
        self.account_file = account_file
        self.questions = []
        self.accounts = []

        self.load_questions()
        self.load_accounts()
        self.setup_routes()

    def load_questions(self):
        self.questions = []
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"{self.csv_file} không tồn tại!")
        with open(self.csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # print(row)
                self.questions.append({
                    "id": int(row["\ufeffid"]),
                    "question_en": row["question_en"],
                    "answer_vi": row["answer_vi"],
                    "answer_en": row["answer_en"],
                    "category": row["category"],
                    "search_keyword": row["search_keyword"].strip(),
                    "detail_meaning": row["detail_meaning"],
                })

    def load_accounts(self):
        self.accounts = []
        if not os.path.exists(self.account_file):
            self.create_default_accounts()
        with open(self.account_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.accounts.append({
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "password_hash": row["password_hash"],
                    "current_question_id": int(row["current_question_id"]),
                    "questions_learned": row["questions_learned"].split(",") if row["questions_learned"] else [],
                    "active": row["active"] == "1"
                })

    def create_default_accounts(self):
        with open(self.account_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username", "full_name", "password_hash", "current_question_id", "questions_learned", "active"])
            writer.writeheader()
            writer.writerow({
                "username": "user1",
                "full_name": "Người Dùng 1",
                "password_hash": hashlib.md5("123456".encode()).hexdigest(),
                "current_question_id": 1,
                "questions_learned": "1,2,3",
                "active": 1
            })
            writer.writerow({
                "username": "user2",
                "full_name": "Trần Thị B",
                "password_hash": hashlib.md5("123".encode()).hexdigest(),
                "current_question_id": 1,
                "questions_learned": "",
                "active": 1
            })
            writer.writerow({
                "username": "guest",
                "full_name": "Guest User",
                "password_hash": "",
                "current_question_id": 1,
                "questions_learned": "",
                "active": 1
            })

    def save_accounts(self):
        with open(self.account_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username", "full_name", "password_hash", "current_question_id", "questions_learned", "active"])
            writer.writeheader()
            for acc in self.accounts:
                writer.writerow({
                    "username": acc["username"],
                    "full_name": acc["full_name"],
                    "password_hash": acc["password_hash"],
                    "current_question_id": acc["current_question_id"],
                    "questions_learned": ",".join(acc["questions_learned"]),
                    "active": 1 if acc["active"] else 0
                })

    def get_account(self, username):
        for acc in self.accounts:
            if acc["username"] == username:
                return acc
        return None

    def get_image_url(self, keyword):
        print("get key wowrd: ", keyword)
        try:
            # ✅ Sửa lỗi: Xóa khoảng trắng thừa trong URL
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            params = {
                "query": keyword,
                "per_page": 1,
                "orientation": "landscape",
                "page": random.randint(1, 3)
            }
            response = requests.get(url, headers=headers, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    return data["results"][0]["urls"]["regular"]
            return None
        except Exception as e:
            print(f"[Unsplash] Lỗi: {e}")
            return None

    def get_user_stats(self, username):
        user = self.get_account(username)
        if not user:
            return None

        total_questions = len(self.questions)
        learned_count = len(user["questions_learned"])
        progress_percent = (learned_count / total_questions * 100) if total_questions > 0 else 0

        last_learned_id = user["questions_learned"][-1] if user["questions_learned"] else None
        last_learned_question = None
        if last_learned_id:
            q = next((q for q in self.questions if str(q["id"]) == last_learned_id), None)
            if q:
                last_learned_question = q["question_en"]

        # Tạo dữ liệu giả cho streak (sau này có thể dùng log)
        streak = random.randint(1, 30)

        return {
            "username": user["username"],
            "full_name": user["full_name"],
            "created_at": "2024-01-01T00:00:00Z",  # Có thể mở rộng
            "total_questions": total_questions,
            "learned_count": learned_count,
            "today_count": random.randint(5, 15),
            "progress_percent": round(progress_percent, 1),
            "last_learned_question": last_learned_question,
            "last_learned_time": datetime.now().strftime("%H:%M:%S"),
            "streak": streak
        }

    def setup_routes(self):
        # ————— ROUTES —————
        @self.app.route("/")
        def home():
            if 'username' not in session:
                return redirect(url_for('login'))
            user = self.get_account(session['username'])
            if user:
                return render_template("index.html")
            session.clear()
            return redirect(url_for('login'))

        @self.app.route("/login")
        def login():
            return render_template("login.html")
        
        @self.app.route("/listening")
        def listening():
            return render_template("listening.html")
        
        @self.app.route("/visual-vocab")
        def visual_vocab():
            return render_template("visual-vocab.html")
        
        @self.app.route("/guest")
        def guest_login():
            session['username'] = 'guest'
            return redirect(url_for('home'))

        # ————— API ĐĂNG NHẬP / ĐĂNG KÝ —————
        @self.app.route("/api/login", methods=["POST"])
        def api_login():
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")
            acc = self.get_account(username)
            password_hash = hashlib.md5(password.encode()).hexdigest() if password else ""

            if acc and acc["password_hash"] == password_hash:
                session['username'] = acc["username"]
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Sai thông tin đăng nhập"}), 401

        @self.app.route("/api/register", methods=["POST"])
        def api_register():
            data = request.get_json()
            full_name = data.get("full_name", "").strip()
            username = data.get("username", "").strip()
            email = data.get("email", "").strip()
            password = data.get("password", "")

            if not full_name or not username or not email or not password:
                return jsonify({"status": "error", "message": "Vui lòng điền đầy đủ thông tin"}), 400
            if len(password) < 6:
                return jsonify({"status": "error", "message": "Mật khẩu phải có ít nhất 6 ký tự"}), 400
            if "@" not in email:
                return jsonify({"status": "error", "message": "Email không hợp lệ"}), 400
            if self.get_account(username):
                return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại"}), 400

            new_user = {
                "username": username,
                "full_name": full_name,
                "password_hash": hashlib.md5(password.encode()).hexdigest(),
                "current_question_id": 1,
                "questions_learned": [],
                "active": True
            }
            self.accounts.append(new_user)
            self.save_accounts()
            return jsonify({"status": "success", "message": "Đăng ký thành công!"})

        # ————— API CÂU HỎI —————
        @self.app.route("/api/questions")
        def api_questions():
            if 'username' not in session:
                return jsonify([]), 401
            user = self.get_account(session['username'])
            if not user:
                return jsonify([]), 401

            questions_with_status = []
            for q in self.questions:
                is_learned = str(q["id"]) in user["questions_learned"]
                image_url = self.get_image_url(q["search_keyword"])
                questions_with_status.append({
                    "id": q["id"],
                    "question_en": q["question_en"],
                    "answer_vi": q["answer_vi"],
                    "answer_en": q["answer_en"],
                    "category": q["category"],
                    "image": image_url or "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&h=500&fit=crop",
                    "learned": is_learned,
                    "detail_meaning": q["detail_meaning"],
                })
            questions_with_status.sort(key=lambda x: (x["id"] < user["current_question_id"], x["id"]))
            return jsonify(questions_with_status)

        @self.app.route("/api/mark-learned", methods=["POST"])
        def mark_learned():
            if 'username' not in session:
                return jsonify({"status": "error"}), 401
            user = self.get_account(session['username'])
            if not user:
                return jsonify({"status": "error"}), 401

            data = request.get_json()
            q_id = str(data.get("id"))
            if q_id and q_id not in user["questions_learned"]:
                user["questions_learned"].append(q_id)
                user["current_question_id"] = int(q_id) + 1
                for acc in self.accounts:
                    if acc["username"] == user["username"]:
                        acc.update(user)
                self.save_accounts()
            return jsonify({"status": "ok"})

        # ————— API PROFILE —————
        @self.app.route("/profile")
        def profile():
            if 'username' not in session:
                return redirect(url_for('login'))
            user = self.get_account(session['username'])
            if not user:
                return redirect(url_for('login'))
            return render_template("profile.html")

        @self.app.route("/api/profile")
        def api_profile():
            if 'username' not in session:
                return jsonify({"error": "Unauthorized"}), 401
            stats = self.get_user_stats(session['username'])
            if not stats:
                return jsonify({"error": "User not found"}), 404
            return jsonify(stats)

        # ————— API TÀI KHOẢN —————
        @self.app.route("/api/change-password", methods=["POST"])
        def api_change_password():
            if 'username' not in session:
                return jsonify({"status": "error", "message": "Chưa đăng nhập"}), 401

            data = request.get_json()
            current_password = data.get("current_password")
            new_password = data.get("new_password")
            confirm_password = data.get("confirm_password")

            username = session['username']
            user = self.get_account(username)
            if not user:
                return jsonify({"status": "error", "message": "Tài khoản không tồn tại"}), 404

            current_hash = hashlib.md5(current_password.encode()).hexdigest()
            if user["password_hash"] != current_hash:
                return jsonify({"status": "error", "message": "Mật khẩu hiện tại sai"}), 400

            if len(new_password) < 6:
                return jsonify({"status": "error", "message": "Mật khẩu mới phải có ít nhất 6 ký tự"}), 400
            if new_password != confirm_password:
                return jsonify({"status": "error", "message": "Xác nhận mật khẩu không khớp"}), 400

            user["password_hash"] = hashlib.md5(new_password.encode()).hexdigest()
            for acc in self.accounts:
                if acc["username"] == username:
                    acc["password_hash"] = user["password_hash"]
            self.save_accounts()

            return jsonify({"status": "success", "message": "Đổi mật khẩu thành công!"})

        @self.app.route("/api/reset-progress", methods=["POST"])
        def api_reset_progress():
            if 'username' not in session:
                return jsonify({"status": "error"}), 401
            user = self.get_account(session['username'])
            if not user:
                return jsonify({"status": "error"}), 404

            user["questions_learned"] = []
            user["current_question_id"] = 1
            for acc in self.accounts:
                if acc["username"] == user["username"]:
                    acc.update(user)
            self.save_accounts()

            return jsonify({"status": "success", "message": "Đã đặt lại tiến độ học!"})

        @self.app.route("/api/logout")
        def api_logout():
            # session.pop('username', None)
            return render_template("login.html")
            # return jsonify({"status": "success"})

    def run(self, host="127.0.0.1", port=5000, debug=True):
        print(f"🌍 Server đang chạy tại http://{host}:{port}")
        print(f"📚 Câu hỏi: {self.csv_file}")
        print(f"👥 Tài khoản: {self.account_file}")
        print(f"🔐 Đăng nhập: có mật khẩu, dùng session")
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    backend = EnglishLearning(csv_file=PATH_QUESTION_DB, account_file=PATH_ACCOUNTS)
    backend.run()