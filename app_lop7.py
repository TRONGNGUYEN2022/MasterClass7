import os
import gdown
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Lớp Học Số Lớp 7 - Chuẩn NotebookLM",
    page_icon="🏫",
    layout="wide"
)

# ----------------------------------------------------
# 1. CẤU HÌNH API & GOOGLE DRIVE
# ----------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
gdrive_folder_id = st.secrets.get("GDRIVE_FOLDER_ID", os.getenv("GDRIVE_FOLDER_ID", "1SFtX3w6EgF6MzwrRrhG9WgYy056ikJ_X"))

if not api_key:
    api_key = st.sidebar.text_input("🔑 Nhập Gemini API Key:", type="password")
    if not api_key:
        st.warning("⚠️ Vui lòng cấu hình GEMINI_API_KEY!")
        st.stop()

if not gdrive_folder_id:
    gdrive_folder_id = st.sidebar.text_input("📁 Nhập Google Drive Folder ID:", value="1SFtX3w6EgF6MzwrRrhG9WgYy056ikJ_X")

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 2. ĐỒNG BỘ SGK TỪ GOOGLE DRIVE
# ----------------------------------------------------
DATA_DIR = "./data_gdrive"

@st.cache_resource(show_spinner="⏳ Đang kết nối kho dữ liệu Google Drive...")
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
    media_files = {} # Lưu file audio/video bài giảng NotebookLM
    for root, _, files in os.walk(DATA_DIR):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.lower().endswith(".pdf"):
                try:
                    reader = PdfReader(pdf_path)
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
# 3. SIDEBAR ĐIỀU HƯỚNG
# ----------------------------------------------------
st.sidebar.title("🏫 Trường Học Số Lớp 7")

subject = st.sidebar.selectbox(
    "📚 Môn học:",
    ["Toán học", "Khoa học tự nhiên", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lí", "Tin học", "GDCD"]
)

room_mode = st.sidebar.radio(
    "🚪 Chọn Phòng:",
    ["👩‍🏫 Phòng Học Trực Tuyến (Chuẩn 4 bước)", "💬 Phòng Gia Sư (Hỏi & Giải bài)", "📝 Phòng Tạo Đề (Chuẩn Ma trận)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Kế hoạch bài dạy (PPCT)")
week = st.sidebar.slider("Chọn Tuần học:", min_value=1, max_value=35, value=1)
lesson_name = st.sidebar.text_input("Tên bài học / Tiết dạy:", value="Tập hợp các số hữu tỉ")

# Link hoặc file Audio/Video từ NotebookLM
media_url_input = st.sidebar.text_input("🔗 Link Audio/Video NotebookLM (nếu có):", placeholder="Dán link Drive/Youtube tại đây")

if sgk_text:
    st.sidebar.success("✅ Đã nạp SGK & Media từ Drive")
else:
    st.sidebar.info("ℹ️ Đang dùng AI gốc")

if st.sidebar.button("🗑️ Làm mới bài học"):
    st.session_state.clear()
    st.rerun()

# ----------------------------------------------------
# PHÒNG 1: TIẾT HỌC CHUẨN 4 BƯỚC
# ----------------------------------------------------
if room_mode == "👩‍🏫 Phòng Học Trực Tuyến (Chuẩn 4 bước)":
    st.title(f"👩‍🏫 Tiết Học Trực Tuyến: {lesson_name}")
    st.caption(f"📚 Môn: **{subject}** | 🗓️ **Tuần {week}**")

    # BƯỚC 1: XEM/NGHE BÀI GIẢNG NOTEBOOKLM
    with st.expander("🎬 BƯỚC 1: XEM / NGHE BÀI GIẢNG (NotebookLM Overview)", expanded=True):
        st.write("Cùng lắng nghe bài tóm tắt thảo luận sinh động về chủ đề bài học hôm nay nhé:")
        # Kiểm tra xem có file audio trong folder hoặc link ngoài không
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
            st.info("💡 Bạn có thể dán link Audio Overview từ NotebookLM vào thanh bên trái hoặc ném file mp3 vào Google Drive nhé.")

    # BƯỚC 2: TÓM TẮT TRỌNG TÂM
    with st.expander("📌 BƯỚC 2: TÓM TẮT KIẾN THỨC CỐT LÕI & CÔNG THỨC", expanded=True):
        if st.button("📖 Xem Bảng Tóm Tắt Trọng Tâm", type="primary"):
            with st.spinner("Thầy/Cô đang tổng hợp bảng ghi nhớ..."):
                prompt = f"""
                Bạn là giáo viên giỏi môn {subject} Lớp 7 theo GDPT 2018.
                Hãy tóm tắt KIẾN THỨC CỐT LÕI của bài: {lesson_name} (Tuần {week}).
                YÊU CẦU:
                - Ngắn gọn, súc tích, trực quan (dùng bảng biểu, đóng khung công thức).
                - Nêu rõ: Định nghĩa/Khái niệm, Công thức cần nhớ, và 1 ví dụ minh họa thực tế dễ hiểu nhất.
                """
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, f"[DỮ LIỆU SGK]:\n{sgk_text[:8000]}"],
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                st.session_state.summary_text = resp.text

        if "summary_text" in st.session_state:
            st.markdown(st.session_state.summary_text)

    # BƯỚC 3: BÀI TẬP ÁP DỤNG TẠI LỚP (TƯƠNG TÁC)
    with st.expander("✏️ BƯỚC 3: BÀI TẬP ÁP DỤNG TẠI LỚP", expanded=True):
        st.write("Thực hành ngay 2 bài tập nhỏ để khắc sâu kiến thức:")
        if st.button("🎯 Nhận Bài Tập Áp Dụng"):
            with st.spinner("Thầy/Cô đang chọn bài tập tiêu biểu..."):
                prompt = f"""
                Hãy đưa ra 2 bài tập áp dụng mức độ Nhận biết và Thông hiểu cho bài: {lesson_name} môn {subject} Lớp 7.
                Chỉ đưa đề bài, KHÔNG đưa kèm lời giải để học sinh tự làm.
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
                            "Hãy nhận xét xem học sinh làm đúng hay sai ở từng bước, khen ngợi điểm tốt và chỉ ra chỗ cần sửa (nếu có)."
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
                Hãy đóng vai giáo viên môn {subject} lớp 7 tổng kết bài {lesson_name}.
                1. 3 điều cốt lõi con cần nhớ hôm nay.
                2. Giao 2 bài tập về nhà mức độ Vận dụng (kèm gợi ý nhỏ).
                3. Lời chúc và động viên khích lệ tinh thần học tập.
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
    st.caption(f"Môn **{subject} - Lớp 7**")

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
            if img_obj: st.image(img_obj)
            if user_input: st.write(user_input)

        st.session_state.chat_history.append({"role": "user", "text": user_input or "[Ảnh bài tập]", "image": img_obj})

        SYSTEM_PROMPT = f"""Bạn là Gia sư Trí Tuệ lớp 7 môn {subject}.
- Nếu học sinh xin đáp án / giải nhanh: Đưa ngay kết quả chuẩn xác và giải thích tường tận từng bước.
- Nếu học sinh hỏi bài bình thường: Gợi mở từng bước (Socratic).
- Giọng điệu thân thiện, khích lệ."""

        contents = [SYSTEM_PROMPT]
        if sgk_text: contents.append(f"[SGK]:\n{sgk_text[:8000]}")
        if img_obj: contents.append(img_obj)
        contents.append(user_input or "Hướng dẫn con bài này ạ.")

        with st.chat_message("assistant"):
            with st.spinner("Thầy đang chuẩn bị câu trả lời..."):
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
        exam_type = st.selectbox("Loại đề:", ["15 phút", "45 phút (1 tiết)", "Giữa học kỳ", "Cuối học kỳ"])
    with col2:
        diff = st.selectbox("Mức độ:", ["Chuẩn ma trận GDPT 2018", "Cơ bản ôn tập", "Nâng cao học sinh giỏi"])

    exam_topic = st.text_input("Chủ đề kiểm tra:", value=f"Tuần {week}: {lesson_name}")

    if st.button("📋 Tạo Đề & Ma Trận Ngay", type="primary"):
        with st.spinner("Đang lập bảng ma trận, soạn câu hỏi và thang điểm..."):
            prompt = f"""
            Biên soạn đề kiểm tra môn {subject} Lớp 7 theo GDPT 2018.
            - Loại: {exam_type} | Mức độ: {diff} | Nội dung: {exam_topic}
            YÊU CẦU CẤU TRÚC 3 PHẦN:
            1. BẢNG MA TRẬN & ĐẶC TẢ ĐỀ (Phân bổ tỉ lệ % 4 mức độ).
            2. ĐỀ BÀI (Trắc nghiệm + Tự luận rõ ràng).
            3. HƯỚNG DẪN CHẤM & BIỂU ĐIỂM (Chi tiết đến 0.25 điểm).
            """
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, f"[DỮ LIỆU]:\n{sgk_text[:10000]}"],
                config=types.GenerateContentConfig(temperature=0.3)
            )
            st.markdown(resp.text)
            st.session_state.last_exam = resp.text

    if "last_exam" in st.session_state:
        st.download_button("📥 Tải Đề Kiểm Tra (.md / Word)", data=st.session_state.last_exam, file_name=f"De_Kiem_Tra_{subject}_Lop7.md")