import os
import gdown
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN STREAMLIT CHUẨN IPAD / WEB
# ----------------------------------------------------
st.set_page_config(
    page_title="Lớp Học Số Toán 7 - Kết Nối Tri Thức",
    page_icon="🏫",
    layout="wide"
)

# ----------------------------------------------------
# 2. CẤU HÌNH API KEYS & BIẾN MÔI TRƯỜNG
# ----------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
gdrive_folder_id = st.secrets.get("GDRIVE_FOLDER_ID", os.getenv("GDRIVE_FOLDER_ID", "1SFtX3w6EgF6MzwrRrhG9WgYy056ikJ_X"))

if not api_key:
    api_key = st.sidebar.text_input("🔑 Nhập Gemini API Key:", type="password")
    if not api_key:
        st.warning("⚠️ Vui lòng cấu hình GEMINI_API_KEY để bắt đầu!")
        st.stop()

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 3. ĐỒNG BỘ SGK & MEDIA TỪ GOOGLE DRIVE
# ----------------------------------------------------
DATA_DIR = "./data_gdrive"

@st.cache_resource(show_spinner="⏳ Đang mở kho sách & tài liệu từ Google Drive...")
def sync_sgk_from_drive(folder_id):
    if not folder_id:
        return "", {}
    
    os.makedirs(DATA_DIR, exist_ok=True)
    existing_files = [os.path.join(root, f) for root, _, files in os.walk(DATA_DIR) for f in files]
    
    if not existing_files:
        try:
            url = f"https://drive.google.com/drive/folders/{folder_id}"
            gdown.download_folder(url=url, output=DATA_DIR, quiet=True, use_cookies=False)
        except Exception as e:
            st.sidebar.error(f"Lỗi tải từ Google Drive: {e}")

    extracted_text = ""
    media_files = {}
    for root, _, files in os.walk(DATA_DIR):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.lower().endswith(".pdf"):
                try:
                    reader = PdfReader(file_path)
                    extracted_text += f"\n--- TÀI LIỆU: {file_name} ---\n"
                    max_pages = min(25, len(reader.pages))
                    for page_idx in range(max_pages):
                        page_text = reader.pages[page_idx].extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
                except Exception:
                    continue
            elif file_name.lower().endswith((".mp3", ".m4a", ".wav", ".mp4")):
                media_files[file_name] = file_path

    return extracted_text, media_files

sgk_text, media_dict = sync_sgk_from_drive(gdrive_folder_id) if gdrive_folder_id else ("", {})

# ----------------------------------------------------
# 4. DANH MỤC TOÀN BỘ CHƯƠNG & BÀI HỌC SGK TOÁN 7 (KẾT NỐI TRI THỨC)
# ----------------------------------------------------
TOAN_7_KNTT = {
    "Chương I. Số hữu tỉ (Tập 1)": [
        "Bài 1: Tập hợp các số hữu tỉ",
        "Bài 2: Cộng, trừ, nhân, chia số hữu tỉ",
        "Luyện tập chung (trang 14 - 15)",
        "Bài 3: Lũy thừa với số mũ tự nhiên của một số hữu tỉ",
        "Bài 4: Thứ tự thực hiện các phép tính. Quy tắc chuyển vế",
        "Luyện tập chung (trang 23 - 24)",
        "Bài tập cuối chương I"
    ],
    "Chương II. Số thực (Tập 1)": [
        "Bài 5: Làm quen với số thập phân vô hạn tuần hoàn",
        "Bài 6: Số vô tỉ. Căn bậc hai số học",
        "Bài 7: Tập hợp các số thực",
        "Luyện tập chung (trang 37 - 38)",
        "Bài tập cuối chương II"
    ],
    "Chương III. Góc và đường thẳng song song (Tập 1)": [
        "Bài 8: Góc ở vị trí đặc biệt. Tia phân giác của một góc",
        "Bài 9: Hai đường thẳng song song và dấu hiệu nhận biết",
        "Luyện tập chung (trang 50)",
        "Bài 10: Tiên đề Euclid. Tính chất của hai đường thẳng song song",
        "Bài 11: Định lí và chứng minh định lí",
        "Luyện tập chung (trang 58)",
        "Bài tập cuối chương III"
    ],
    "Chương IV. Tam giác bằng nhau (Tập 1)": [
        "Bài 12: Tổng các góc trong một tam giác",
        "Bài 13: Hai tam giác bằng nhau. Trường hợp bằng nhau thứ nhất của tam giác (c.c.c)",
        "Luyện tập chung (trang 68)",
        "Bài 14: Trường hợp bằng nhau thứ hai và thứ ba của tam giác (c.g.c, g.c.g)",
        "Luyện tập chung (trang 74 - 75)",
        "Bài 15: Các trường hợp bằng nhau của tam giác vuông",
        "Bài 16: Tam giác cân. Đường trung trực của đoạn thẳng",
        "Luyện tập chung (trang 85 - 86)",
        "Bài tập cuối chương IV"
    ],
    "Chương V. Thu thập và biểu diễn dữ liệu (Tập 1)": [
        "Bài 17: Thu thập và phân loại dữ liệu",
        "Bài 18: Biểu đồ hình quạt tròn",
        "Bài 19: Biểu đồ đoạn thẳng",
        "Luyện tập chung (trang 106 - 107)",
        "Bài tập cuối chương V"
    ],
    "Chương VI. Tỉ lệ thức và đại lượng tỉ lệ (Tập 2)": [
        "Bài 20: Tỉ lệ thức",
        "Bài 21: Tính chất của dãy tỉ số bằng nhau",
        "Luyện tập chung (trang 10 - 11)",
        "Bài 22: Đại lượng tỉ lệ thuận",
        "Bài 23: Đại lượng tỉ lệ nghịch",
        "Luyện tập chung (trang 19 - 20)",
        "Bài tập cuối chương VI"
    ],
    "Chương VII. Biểu thức đại số và đa thức một biến (Tập 2)": [
        "Bài 24: Biểu thức đại số",
        "Bài 25: Đa thức một biến",
        "Bài 26: Phép cộng và phép trừ đa thức một biến",
        "Luyện tập chung (trang 37 - 38)",
        "Bài 27: Phép nhân đa thức một biến",
        "Bài 28: Phép chia đa thức một biến",
        "Luyện tập chung (trang 45)",
        "Bài tập cuối chương VII"
    ],
    "Chương VIII. Làm quen với biến cố và xác suất của biến cố (Tập 2)": [
        "Bài 29: Làm quen với biến cố",
        "Bài 30: Làm quen với xác suất của biến cố",
        "Luyện tập chung (trang 57)",
        "Bài tập cuối chương VIII"
    ],
    "Chương IX. Quan hệ giữa các yếu tố trong một tam giác (Tập 2)": [
        "Bài 31: Quan hệ giữa góc và cạnh đối diện trong một tam giác",
        "Bài 32: Quan hệ giữa đường vuông góc và đường xiên",
        "Bài 33: Quan hệ giữa ba cạnh của một tam giác",
        "Luyện tập chung (trang 71)",
        "Bài 34: Sự đồng quy của ba đường trung tuyến, ba đường phân giác trong một tam giác",
        "Bài 35: Sự đồng quy của ba đường trung trực, ba đường cao trong một tam giác",
        "Luyện tập chung (trang 84 - 85)",
        "Bài tập cuối chương IX"
    ],
    "Chương X. Một số hình khối trong thực tiễn (Tập 2)": [
        "Bài 36: Hình hộp chữ nhật và hình lập phương",
        "Bài 37: Hình lăng trụ đứng tam giác và hình lăng trụ đứng tứ giác",
        "Luyện tập chung (trang 100 - 101)",
        "Bài tập cuối chương X",
        "Ôn tập cuối năm"
    ]
}

# ----------------------------------------------------
# 5. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ----------------------------------------------------
st.sidebar.title("🏫 Trường Học Số Toán 7")
st.sidebar.caption("Bộ sách: **Kết nối tri thức với cuộc sống**")

room_mode = st.sidebar.radio(
    "🚪 Chọn Phòng chức năng:",
    ["👩‍🏫 Phòng Học Trực Tuyến (Chuẩn 4 bước)", "💬 Phòng Gia Sư (Hỏi & Giải bài)", "📝 Phòng Tạo Đề (Chuẩn Ma trận)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Kế hoạch bài dạy (SGK)")

selected_chapter = st.sidebar.selectbox("📖 Chọn Chương:", list(TOAN_7_KNTT.keys()))
lesson_name = st.sidebar.selectbox("📝 Chọn Bài học:", TOAN_7_KNTT[selected_chapter])
week = st.sidebar.slider("Tuần học (ước tính):", min_value=1, max_value=35, value=1)

media_url_input = st.sidebar.text_input("🔗 Link Audio/Video NotebookLM (nếu có):", placeholder="Dán link Drive/Youtube tại đây")

if sgk_text:
    st.sidebar.success("✅ Đã kết nối SGK từ Drive")
else:
    st.sidebar.info("ℹ️ Đang dùng AI gốc")

if st.sidebar.button("🗑️ Làm mới / Xóa phiên"):
    st.session_state.clear()
    st.rerun()

# ----------------------------------------------------
# PHÒNG 1: TIẾT HỌC TRỰC TUYẾN CHUẨN 4 BƯỚC
# ----------------------------------------------------
if room_mode == "👩‍🏫 Phòng Học Trực Tuyến (Chuẩn 4 bước)":
    st.title(f"👩‍🏫 {lesson_name}")
    st.caption(f"📚 **{selected_chapter}** | 🗓️ **Tuần {week}**")

    # BƯỚC 1: XEM/NGHE BÀI GIẢNG NOTEBOOKLM
    with st.expander("🎬 BƯỚC 1: XEM / NGHE BÀI GIẢNG SINH ĐỘNG (NotebookLM Overview)", expanded=True):
        st.write("Cùng lắng nghe bài giảng tóm tắt sinh động về nội dung bài học:")
        matched_media = [p for name, p in media_dict.items() if lesson_name.lower() in name.lower() or f"tuan{week}" in name.lower()]
        
        if matched_media:
            file_path = matched_media[0]
            if file_path.endswith((".mp3", ".m4a", ".wav")):
                st.audio(file_path)
            else:
                st.video(file_path)
            st.success(f"🎵 Đang phát bài giảng: {os.path.basename(file_path)}")
        elif media_url_input:
            if "youtube.com" in media_url_input or "youtu.be" in media_url_input:
                st.video(media_url_input)
            else:
                st.markdown(f"👉 [**Bấm vào đây để mở Audio/Video bài giảng trên Drive**]({media_url_input})")
        else:
            st.info("💡 Con có thể dán link Audio Overview từ NotebookLM vào thanh bên trái hoặc đặt file mp3/mp4 vào thư mục Google Drive.")

    # BƯỚC 2: THẺ GHI NHỚ CỐT LÕI (FLASHCARD MÀU SẮC TRỰC QUAN)
    with st.expander("📌 BƯỚC 2: THẺ GHI NHỚ CỐT LÕI (1 PHÚT NẮM BẢN CHẤT)", expanded=True):
        if st.button("✨ Mở Thẻ Ghi Nhớ Trọng Tâm", type="primary"):
            with st.spinner("Đang cô đọng kiến thức thành các thẻ ghi nhớ màu sắc..."):
                prompt = f"""
                Bạn là giáo viên dạy Toán 7 xuất sắc bộ sách Kết nối tri thức với cuộc sống.
                Hãy tóm tắt bài học: "{lesson_name}" thuộc "{selected_chapter}".
                
                QUY TẮC BẮT BUỘC:
                - TUYỆT ĐỐI KHÔNG dùng bất kỳ thẻ HTML nào (<div>, <span>, <table>...).
                - Dùng ký hiệu LaTeX ($...$) cho công thức hoặc ký hiệu toán học.
                - Phân tách đúng 3 phần bằng cú pháp:
                  [KHAI_NIEM]: Tối đa 2-3 câu ngắn nêu bản chất khái niệm và 1 ví dụ thực tế gần gũi.
                  [CONG_THUC]: Các công thức, tính chất hoặc quy tắc cốt lõi nhất.
                  [ME_O_NHO]: 1 câu mẹo ghi nhớ ngắn gọn hoặc lưu ý tránh sai lầm hay gặp trong bài thi.
                """
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, f"[DỮ LIỆU SGK]:\n{sgk_text[:6000]}"],
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                st.session_state.card_content = resp.text

        if "card_content" in st.session_state:
            raw = st.session_state.card_content
            kn = raw.split("[CONG_THUC]")[0].replace("[KHAI_NIEM]:", "").strip() if "[KHAI_NIEM]:" in raw else raw
            ct = raw.split("[CONG_THUC]")[1].split("[ME_O_NHO]")[0].strip() if "[CONG_THUC]" in raw else ""
            meo = raw.split("[ME_O_NHO]")[1].strip() if "[ME_O_NHO]" in raw else ""

            col_left, col_right = st.columns([1.1, 1])
            with col_left:
                st.markdown("#### 💡 1. Bản Chất Khái Niệm")
                st.info(kn if kn else "Khái niệm trọng tâm của bài học.")

            with col_right:
                st.markdown("#### 📐 2. Công Thức Cốt Lõi")
                st.success(ct if ct else "Các công thức cần ghi nhớ.")

            if meo:
                st.markdown("#### ⚡ 3. Mẹo Nhớ Nhanh & Tránh Bẫy")
                st.warning(meo)

    # BƯỚC 3: BÀI TẬP ÁP DỤNG TẠI LỚP (TƯƠNG TÁC CHẤM CHỮA)
    with st.expander("✏️ BƯỚC 3: BÀI TẬP ÁP DỤNG TẠI LỚP", expanded=True):
        st.write("Thực hành ngay 2 bài tập nhỏ để củng cố kiến thức vừa học:")
        if st.button("🎯 Nhận Bài Tập Áp Dụng"):
            with st.spinner("Thầy/Cô đang chuẩn bị bài tập..."):
                prompt = f"""
                Hãy đưa ra đúng 2 bài tập áp dụng mức độ Nhận biết và Thông hiểu cho bài: {lesson_name} thuộc {selected_chapter} môn Toán 7 (Kết nối tri thức).
                Chỉ đưa đề bài rõ ràng, KHÔNG đưa kèm lời giải để học sinh tự làm.
                """
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt],
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                st.session_state.practice_questions = resp.text

        if "practice_questions" in st.session_state:
            st.markdown(st.session_state.practice_questions)
            user_answer = st.text_area("✍️ Con hãy nhập câu trả lời / cách làm của mình vào đây:")
            uploaded_ans_img = st.file_uploader("📸 Hoặc chụp ảnh bài làm trên vở:", type=["png", "jpg", "jpeg"], key="ans_img")

            if st.button("📤 Gửi Thầy/Cô Chấm Bài"):
                if not user_answer and not uploaded_ans_img:
                    st.warning("Con hãy nhập câu trả lời hoặc gửi ảnh bài làm nhé!")
                else:
                    with st.spinner("Thầy/Cô đang chấm và nhận xét bài cho con..."):
                        ans_payload = [
                            f"Đề bài:\n{st.session_state.practice_questions}\n\nBài làm của học sinh:\n{user_answer}",
                            "Hãy nhận xét từng bước xem học sinh làm đúng hay sai, khen ngợi điểm tốt và giải thích tỉ mỉ chỗ cần khắc phục nếu có."
                        ]
                        if uploaded_ans_img:
                            ans_payload.append(Image.open(uploaded_ans_img))

                        resp_grade = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=ans_payload,
                            config=types.GenerateContentConfig(temperature=0.2)
                        )
                        st.success("🎉 Kết quả nhận xét bài làm:")
                        st.markdown(resp_grade.text)

    # BƯỚC 4: CỦNG CỐ & GIAO BÀI TẬP VỀ NHÀ
    with st.expander("🎯 BƯỚC 4: CỦNG CỐ & DẶN DÒ BÀI TẬP VỀ NHÀ", expanded=False):
        if st.button("📋 Tổng Kết Tiết Học & Nhận Bài Về Nhà"):
            with st.spinner("Thầy/Cô đang tổng kết..."):
                prompt = f"""
                Hãy đóng vai giáo viên Toán 7 tổng kết bài {lesson_name} ({selected_chapter}).
                1. 3 điều cốt lõi con cần nhớ hôm nay.
                2. Giao 2 bài tập về nhà mức độ Vận dụng (kèm gợi ý nhỏ).
                3. Lời chúc và động viên khích lệ tinh thần học tập của con.
                """
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt],
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                st.markdown(resp.text)

# ----------------------------------------------------
# PHÒNG 2: PHÒNG GIA SƯ (HỎI ĐÁP & CHỮA BÀI TẬP)
# ----------------------------------------------------
elif room_mode == "💬 Phòng Gia Sư (Hỏi & Giải bài)":
    st.title("💬 Bàn Gia Sư Hỏi Đáp")
    st.caption(f"Đang học: **{lesson_name}** ({selected_chapter})")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if msg.get("image"):
                st.image(msg["image"])
            st.write(msg["text"])

    uploaded_file = st.file_uploader("📸 Tải ảnh bài tập (iPad):", type=["png", "jpg", "jpeg"], key="tutor_img")
    user_input = st.chat_input("Hỏi thầy/cô bài tập con chưa hiểu...")

    if user_input or uploaded_file:
        img_obj = Image.open(uploaded_file) if uploaded_file else None
        with st.chat_message("user"):
            if img_obj: 
                st.image(img_obj)
            if user_input: 
                st.write(user_input)

        st.session_state.chat_history.append({"role": "user", "text": user_input or "[Ảnh bài tập]", "image": img_obj})

        SYSTEM_PROMPT = f"""Bạn là Gia sư Trí Tuệ môn Toán 7 theo bộ sách Kết nối tri thức.
- Nếu học sinh xin đáp án / nhờ giải nhanh / giải chi tiết: Lập tức đưa lời giải hoàn chỉnh, chính xác và giải thích tường tận từng bước.
- Nếu học sinh hỏi bài bình thường: Áp dụng phương pháp Gợi mở (Socratic) để con tự tư duy.
- Luôn giữ giọng điệu thân thiện, ấm áp và khích lệ."""

        contents = [SYSTEM_PROMPT]
        if sgk_text: 
            contents.append(f"[DỮ LIỆU SGK]:\n{sgk_text[:8000]}")
        if img_obj: 
            contents.append(img_obj)
        contents.append(user_input or "Hướng dẫn con làm bài tập này với ạ.")

        with st.chat_message("assistant"):
            with st.spinner("Thầy/Cô đang hướng dẫn..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                st.write(response.text)

        st.session_state.chat_history.append({"role": "assistant", "text": response.text})

# ----------------------------------------------------
# PHÒNG 3: PHÒNG TẠO ĐỀ KIỂM TRA CHUẨN MA TRẬN
# ----------------------------------------------------
elif room_mode == "📝 Phòng Tạo Đề (Chuẩn Ma trận)":
    st.title("📝 Biên Soạn Đề Kiểm Tra Chuẩn Ma Trận")
    col1, col2 = st.columns(2)
    with col1:
        exam_type = st.selectbox("Hình thức kiểm tra:", ["Kiểm tra 15 phút", "Kiểm tra 45 phút (1 tiết)", "Kiểm tra Giữa kỳ", "Kiểm tra Cuối kỳ"])
    with col2:
        diff = st.selectbox("Mức độ đề:", ["Chuẩn ma trận GDPT 2018 (Đủ 4 mức độ)", "Cơ bản ôn tập", "Nâng cao bồi dưỡng học sinh giỏi"])

    exam_topic = st.text_input("Chủ đề kiểm tra:", value=f"{selected_chapter} - {lesson_name}")

    if st.button("📋 Biên Soạn Đề & Ma Trận Ngay", type="primary"):
        with st.spinner("Đang lập bảng ma trận đặc tả, soạn câu hỏi và thang điểm chi tiết..."):
            prompt = f"""
            Bạn là tổ trưởng chuyên môn biên soạn đề thi môn Toán 7 (Bộ Kết nối tri thức).
            - Loại đề: {exam_type}
            - Mức độ: {diff}
            - Nội dung trọng tâm: {exam_topic}

            YÊU CẦU CẤU TRÚC 3 PHẦN CHUẨN MỰC:
            1. BẢNG MA TRẬN & BẢN ĐẶC TẢ ĐỀ (Phân bổ %: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao).
            2. ĐỀ BÀI KIỂM TRA (Trắc nghiệm khách quan + Tự luận rõ ràng từng câu, từng ý).
            3. HƯỚNG DẪN CHẤM & THANG ĐIỂM (Chi tiết đến từng 0.25 điểm cho mỗi bước).
            """
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, f"[DỮ LIỆU SGK & PPCT]:\n{sgk_text[:10000]}"],
                config=types.GenerateContentConfig(temperature=0.3)
            )
            st.markdown(resp.text)
            st.session_state.last_exam = resp.text

    if "last_exam" in st.session_state:
        st.download_button(
            label="📥 Tải Đề Kiểm Tra (.md / Word)",
            data=st.session_state.last_exam,
            file_name=f"De_Kiem_Tra_Toan7_{lesson_name}.md",
            mime="text/markdown"
        )