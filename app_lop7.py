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
    page_title="Lớp Học Số Lớp 7 - AI Virtual Classroom",
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

if not gdrive_folder_id:
    gdrive_folder_id = st.sidebar.text_input("📁 Nhập Google Drive Folder ID:", value="1SFtX3w6EgF6MzwrRrhG9WgYy056ikJ_X")

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 3. ĐỒNG BỘ SGK & MEDIA TỪ GOOGLE DRIVE
# ----------------------------------------------------
DATA_DIR = "./data_gdrive"

@st.cache_resource(show_spinner="⏳ Đang mở kho sách & Phân phối chương trình từ Google Drive...")
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
# 4. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ----------------------------------------------------
st.sidebar.title("🏫 Trường Học Số Lớp 7")

subject = st.sidebar.selectbox(
    "📚 Chọn Môn học:",
    ["Toán học", "Khoa học tự nhiên", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lí", "Tin học", "GDCD"]
)

room_mode = st.sidebar.radio(
    "🚪 Chọn Phòng chức năng:",
    ["👩‍🏫 Phòng Học Trực Tuyến (Chuẩn 4 bước)", "💬 Phòng Gia Sư (Hỏi & Giải bài)", "📝 Phòng Tạo Đề (Chuẩn Ma trận)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Kế hoạch bài dạy (PPCT)")
week = st.sidebar.slider("Chọn Tuần học:", min_value=1, max_value=35, value=1)
lesson_name = st.sidebar.text_input("Tên bài học / Tiết dạy:", value="Tập hợp các số hữu tỉ")

media_url_input = st.sidebar.text_input("🔗 Link Audio/Video NotebookLM (nếu có):", placeholder="Dán link Drive/Youtube tại đây")

if sgk_text:
    st.sidebar.success("✅ Đã kết nối SGK & Tài liệu từ Drive")
else:
    st.sidebar.info("ℹ️ Đang dùng AI gốc (Chưa nạp tài liệu Drive)")

if st.sidebar.button("🗑️ Làm mới / Đổi bài học"):
    st.session_state.clear()
    st.rerun()

# ----------------------------------------------------
# PHÒNG 1: TIẾT HỌC TRỰC TUYẾN CHUẨN 4 BƯỚC SƯ PHẠM
# ----------------------------------------------------
if room_mode == "👩‍🏫 Phòng Học Trực Tuyến (Chuẩn 4 bước)":
    st.title(f"👩‍🏫 Tiết Học Trực Tuyến: {lesson_name}")
    st.caption(f"📚 Môn: **{subject}** | 🗓️ **Tuần {week}**")

    # BƯỚC 1: XEM/NGHE BÀI GIẢNG TỪ NOTEBOOKLM
    with st.expander("🎬 BƯỚC 1: XEM / NGHE BÀI GIẢNG SINH ĐỘNG (NotebookLM Overview)", expanded=True):
        st.write("Lắng nghe bài tóm tắt thảo luận sinh động về chủ đề bài học:")
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
            st.info("💡 Bạn có thể dán link Audio/Video bài giảng từ NotebookLM vào thanh bên trái hoặc đặt file mp3/mp4 vào thư mục Google Drive.")

    # BƯỚC 2: THẺ GHI NHỚ CỐT LÕI (FLASHCARD MÀU SẮC TRỰC QUAN)
    with st.expander("📌 BƯỚC 2: THẺ GHI NHỚ CỐT LÕI (1 PHÚT NẮM BẢN CHẤT)", expanded=True):
        if st.button("✨ Mở Thẻ Ghi Nhớ Trọng Tâm", type="primary"):
            with st.spinner("Đang cô đọng kiến thức thành các thẻ ghi nhớ màu sắc..."):
                prompt = f"""
                Bạn là chuyên gia sư phạm hàng đầu môn {subject} Lớp 7 chương trình GDPT 2018.
                Hãy tóm tắt bài học "{lesson_name}" (Tuần {week}) THẬT CÔ ĐỌNG, DỄ HIỂU VÀ TRỰC QUAN.
                
                QUY TẮC BẮT BUỘC:
                - TUYỆT ĐỐI KHÔNG dùng bất kỳ thẻ HTML nào (như <div>, <span>, <table>, <p>).
                - Sử dụng ký hiệu LaTeX ($...$) cho công thức hoặc ký hiệu toán học.
                - Định dạng chính xác theo 3 thẻ sau:
                  [KHAI_NIEM]: Tối đa 2-3 gạch đầu dòng giải thích bản chất khái niệm ngắn gọn kèm ví dụ thực tế.
                  [CONG_THUC]: Các công thức, định nghĩa hoặc ký hiệu cốt lõi nhất cần nhớ.
                  [ME_O_NHO]: 1 câu mẹo ghi nhớ ngắn gọn hoặc lưu ý tránh bẫy sai lầm hay gặp.
                """
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, f"[DỮ LIỆU SGK]:\n{sgk_text[:6000]}"],
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                st.session_state.card_content = resp.text

        if "card_content" in st.session_state:
            raw = st.session_state.card_content
            
            # Tách nội dung theo từng thẻ màu sắc
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
                Hãy đưa ra đúng 2 bài tập áp dụng mức độ Nhận biết và Thông hiểu cho bài: {lesson_name} môn {subject} Lớp 7.
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

    # BƯỚC 4: CỦNG CỐ & DẶN DÒ BÀI TẬP VỀ NHÀ
    with st.expander("🎯 BƯỚC 4: CỦNG CỐ & DẶN DÒ BÀI TẬP VỀ NHÀ", expanded=False):
        if st.button("📋 Tổng Kết Tiết Học & Nhận Bài Về Nhà"):
            with st.spinner("Thầy/Cô đang tổng kết..."):
                prompt = f"""
                Hãy đóng vai giáo viên môn {subject} lớp 7 tổng kết bài {lesson_name}.
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
    st.caption(f"Đồng hành cùng con môn **{subject} - Lớp 7**")

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

        SYSTEM_PROMPT = f"""Bạn là Gia sư Trí Tuệ môn {subject} Lớp 7 theo chương trình GDPT 2018.
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
            with st.spinner("Thầy/Cô đang chuẩn bị câu trả lời..."):
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

    exam_topic = st.text_input("Chủ đề kiểm tra:", value=f"Tuần {week}: {lesson_name}")

    if st.button("📋 Biên Soạn Đề & Ma Trận Ngay", type="primary"):
        with st.spinner("Đang lập bảng ma trận đặc tả, soạn câu hỏi và thang điểm chi tiết..."):
            prompt = f"""
            Bạn là tổ trưởng chuyên môn biên soạn đề thi môn {subject} Lớp 7 theo chương trình GDPT 2018.
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
            file_name=f"De_Kiem_Tra_{subject}_Lop7.md",
            mime="text/markdown"
        )