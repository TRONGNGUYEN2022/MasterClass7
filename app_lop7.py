import os
import time
import requests
import gdown
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. CẤU HÌNH GIAO DIỆN STREAMLIT
# ----------------------------------------------------
st.set_page_config(
    page_title="Trường Học Số Lớp 7 - AI Virtual Classroom",
    page_icon="🏫",
    layout="wide"
)

# ----------------------------------------------------
# 2. CẤU HÌNH API KEYS & BIẾN MÔI TRƯỜNG
# ----------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
gdrive_folder_id = st.secrets.get("GDRIVE_FOLDER_ID", os.getenv("GDRIVE_FOLDER_ID", "1SFtX3w6EgF6MzwrRrhG9WgYy056ikJ_X"))
did_api_key = st.secrets.get("DID_API_KEY", os.getenv("DID_API_KEY"))

if not api_key:
    api_key = st.sidebar.text_input("🔑 Nhập Gemini API Key:", type="password")
    if not api_key:
        st.warning("⚠️ Vui lòng cấu hình GEMINI_API_KEY để bắt đầu!")
        st.stop()

if not gdrive_folder_id:
    gdrive_folder_id = st.sidebar.text_input("📁 Nhập Google Drive Folder ID:", value="1SFtX3w6EgF6MzwrRrhG9WgYy056ikJ_X")

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 3. ĐỒNG BỘ TÀI LIỆU SGK & PPCT TỪ GOOGLE DRIVE
# ----------------------------------------------------
DATA_DIR = "./data_gdrive"

@st.cache_resource(show_spinner="⏳ Đang đồng bộ SGK & Phân phối chương trình từ Google Drive...")
def sync_sgk_from_drive(folder_id):
    if not folder_id:
        return ""
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Kiểm tra xem trong thư mục đã có file PDF chưa
    existing_pdfs = []
    for root, _, files in os.walk(DATA_DIR):
        for f in files:
            if f.lower().endswith(".pdf"):
                existing_pdfs.append(os.path.join(root, f))
                
    # Nếu chưa có file nào thì tiến hành tải từ Google Drive
    if not existing_pdfs:
        try:
            # Tải thư mục Google Drive theo folder_id
            gdown.download_folder(
                id=folder_id,
                output=DATA_DIR,
                quiet=True,
                use_cookies=False,
            )
        except Exception as e:
            st.sidebar.error(f"Lỗi khi tải từ Google Drive: {e}")

    # Quét đọc toàn bộ file PDF (bao gồm cả các thư mục con nếu có)
    extracted_text = ""
    file_count = 0
    for root, _, files in os.walk(DATA_DIR):
        for file_name in files:
            if file_name.lower().endswith(".pdf"):
                file_count += 1
                pdf_path = os.path.join(root, file_name)
                try:
                    reader = PdfReader(pdf_path)
                    extracted_text += f"\n--- TÀI LIỆU: {file_name} ---\n"
                    # Đọc 25 trang đầu của mỗi tài liệu để lấy mục lục, PPCT và kiến thức trọng tâm
                    max_pages = min(25, len(reader.pages))
                    for page_idx in range(max_pages):
                        page_text = reader.pages[page_idx].extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
                except Exception:
                    continue

    return extracted_text

sgk_text = sync_sgk_from_drive(gdrive_folder_id) if gdrive_folder_id else ""

# ----------------------------------------------------
# 4. HÀM TẠO VIDEO GIÁO VIÊN ẢO (D-ID API)
# ----------------------------------------------------
def generate_teacher_video(script_text):
    """Gửi kịch bản bài giảng sang D-ID để tạo video cô giáo giảng bài"""
    if not did_api_key:
        st.info("💡 Chưa cấu hình DID_API_KEY trong Secrets/Sidebar nên tính năng video chưa bật.")
        return None

    # Rút gọn kịch bản dưới 260 ký tự để render nhanh và mượt mà
    clean_script = script_text.replace("*", "").replace("#", "").replace("-", " ")[:260]

    url = "https://api.d-id.com/talks"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {did_api_key}"
    }

    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "vi-VN-HoaiMyNeural"  # Giọng tiếng Việt chuẩn truyền cảm
            },
            "input": clean_script
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0"
        },
        "source_url": "https://img.freepik.com/free-photo/portrait-young-asian-teacher-classroom_23-2148780280.jpg"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        talk_id = res_data.get("id")

        if not talk_id:
            return None

        # Chờ render video
        status_url = f"https://api.d-id.com/talks/{talk_id}"
        for _ in range(25):
            time.sleep(2)
            check_res = requests.get(status_url, headers=headers).json()
            if check_res.get("status") == "done":
                return check_res.get("result_url")
            elif check_res.get("status") == "error":
                return None
    except Exception as e:
        st.error(f"Lỗi kết nối tạo video: {e}")
        return None

# ----------------------------------------------------
# 5. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ----------------------------------------------------
st.sidebar.title("🏫 Trường Học Số Lớp 7")

subject = st.sidebar.selectbox(
    "📚 Chọn Môn học:",
    ["Toán học", "Khoa học tự nhiên", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lí", "Tin học", "GDCD"]
)

room_mode = st.sidebar.radio(
    "🚪 Chọn Phòng chức năng:",
    ["👩‍🏫 Phòng Giảng Bài (Video & Tiết dạy)", "💬 Phòng Gia Sư (Hỏi & Giải bài)", "📝 Phòng Kiểm Tra (Đề & Ma trận)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Kế hoạch bài dạy (PPCT)")
week = st.sidebar.slider("Chọn Tuần học:", min_value=1, max_value=35, value=1)
lesson_name = st.sidebar.text_input("Tên bài học / Tiết dạy:", placeholder="Ví dụ: Tiết 5 - Số vô tỉ, Căn bậc hai số học")

if sgk_text:
    st.sidebar.success("✅ Đã kết nối SGK & PPCT từ Drive")
else:
    st.sidebar.info("ℹ️ Đang dùng AI gốc (Chưa nạp tài liệu Drive)")

if st.sidebar.button("🗑️ Làm mới / Đổi bài học"):
    st.session_state.messages = []
    if "last_lesson_content" in st.session_state:
        del st.session_state.last_lesson_content
    st.rerun()

# ----------------------------------------------------
# PHÒNG 1: PHÒNG GIẢNG BÀI (VIRTUAL CLASSROOM & VIDEO)
# ----------------------------------------------------
if room_mode == "👩‍🏫 Phòng Giảng Bài (Video & Tiết dạy)":
    st.title(f"👩‍🏫 Lớp Học Trực Tuyến - Môn {subject}")
    st.caption(f"🗓️ **Tuần {week}** | 📖 Bài học: **{lesson_name if lesson_name else 'Chưa chọn bài'}**")

    if not lesson_name:
        st.info("👈 Con hãy nhập **Tên bài học hoặc Tiết dạy** ở thanh bên trái để bắt đầu tiết học nhé!")
    else:
        st.markdown(f"### 🎯 Tiến trình tiết học: {lesson_name}")
        step = st.radio(
            "Giai đoạn bài học:",
            ["1. 🚀 Khởi động & Dẫn nhập", "2. 📖 Giảng kiến thức trọng tâm", "3. ✏️ Luyện tập tại lớp", "4. 🌟 Vận dụng & Dặn dò"],
            horizontal=True
        )

        TEACHER_PROMPT = f"""Bạn là Thầy/Cô giáo bộ môn {subject} Lớp 7 theo chương trình GDPT 2018 của Việt Nam.
Bạn đang dạy:
- Tuần: {week}
- Bài học/Tiết dạy: {lesson_name}
- Giai đoạn: {step}

YÊU CẦU SƯ PHẠM:
- Xưng hô: Thầy/Cô và con/em.
- Giọng điệu ấm áp, khích lệ, sinh động, dễ tiếp thu cho lứa tuổi 12-13 tuổi.
- Đưa ví dụ so sánh đời sống thực tế, giải thích bản chất kiến thức.
- Bám sát nội dung SGK và chuẩn kiến thức kỹ năng GDPT 2018.
"""
        if st.button("🔔 Bắt đầu giảng phần này", type="primary"):
            with st.spinner("Thầy/Cô đang lên bảng bài giảng..."):
                contents_input = [f"Hãy tiến hành giảng dạy nội dung: {step} của bài {lesson_name}."]
                if sgk_text:
                    contents_input.insert(0, f"[TÀI LIỆU SGK THAM KHẢO]:\n{sgk_text[:10000]}")

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents_input,
                    config=types.GenerateContentConfig(
                        system_instruction=TEACHER_PROMPT,
                        temperature=0.3
                    )
                )
                st.session_state.last_lesson_content = response.text

        if "last_lesson_content" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state.last_lesson_content)

            st.markdown("---")
            col_vid, _ = st.columns([1, 1])
            with col_vid:
                if st.button("🎬 Bật Video Cô Giáo Ảo Giảng Bài"):
                    with st.spinner("👩‍🏫 Cô giáo đang chuẩn bị video bài giảng... (khoảng 15-20 giây)"):
                        video_url = generate_teacher_video(st.session_state.last_lesson_content)
                        if video_url:
                            st.video(video_url)
                            st.success("🎉 Video đã sẵn sàng, mời con theo dõi bài giảng!")
                        else:
                            st.warning("Chưa thể phát video lúc này. Con có thể đọc nội dung bài giảng chi tiết ở trên nhé!")

# ----------------------------------------------------
# PHÒNG 2: PHÒNG GIA SƯ (HỎI ĐÁP & CHỮA BÀI TẬP)
# ----------------------------------------------------
elif room_mode == "💬 Phòng Gia Sư (Hỏi & Giải bài)":
    st.title("💬 Bàn Hỏi Bài & Giải Đáp")
    st.caption(f"Đồng hành cùng con môn **{subject} - Lớp 7**")

    SYSTEM_PROMPT = f"""Bạn là "Gia sư Trí Tuệ", một gia sư kiên nhẫn, thân thiện và thấu hiểu tâm lý cho học sinh lớp 7 (12-13 tuổi) theo chương trình GDPT 2018 của Việt Nam.

QUY TẮC XỬ LÝ THEO YÊU CẦU:
1. TRƯỜNG HỢP CẦN ĐÁP ÁN NGAY (Khi người học yêu cầu: "đáp án", "giải nhanh", "giải chi tiết", "làm mẫu", hoặc kiểm tra kết quả gấp):
   - Lập tức cung cấp ĐÁP ÁN HOÀN CHỈNH, CHÍNH XÁC.
   - Giải thích tường tận từng bước, kèm ví dụ thực tế minh họa sinh động.
2. TRƯỜNG HỢP HỎI BÀI THÔNG THƯỜNG:
   - Áp dụng phương pháp Gợi mở (Socratic), không đưa ngay kết quả cuối cùng.
   - Chia nhỏ bài toán, gợi ý từng bước và đặt câu hỏi nhỏ để con tự suy nghĩ.
3. Luôn giữ giọng điệu tích cực, khen ngợi sự nỗ lực của con.
[Môn học hiện tại: {subject} - Lớp 7]
"""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "image" in msg and msg["image"]:
                st.image(msg["image"])
            st.write(msg["text"])

    uploaded_file = st.file_uploader("📸 Chụp hoặc tải ảnh bài tập (iPad):", type=["png", "jpg", "jpeg"])
    user_input = st.chat_input("Hỏi thầy/cô bất cứ điều gì con chưa hiểu...")

    if user_input or uploaded_file:
        image_obj = None
        if uploaded_file:
            image_obj = Image.open(uploaded_file)

        with st.chat_message("user"):
            if image_obj:
                st.image(image_obj, caption="Ảnh bài tập con gửi")
            if user_input:
                st.write(user_input)

        st.session_state.messages.append({
            "role": "user",
            "text": user_input if user_input else "[Đã gửi ảnh bài tập]",
            "image": image_obj
        })

        contents_payload = []
        if sgk_text:
            contents_payload.append(f"[DỮ LIỆU SGK THAM KHẢO]:\n{sgk_text[:10000]}")
        if image_obj:
            contents_payload.append(image_obj)
        prompt_text = user_input if user_input else "Hãy hướng dẫn em làm bài tập trong ảnh này."
        contents_payload.append(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("Thầy/Cô đang hướng dẫn cho con..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3
                    )
                )
                st.write(response.text)

        st.session_state.messages.append({"role": "assistant", "text": response.text})

# ----------------------------------------------------
# PHÒNG 3: PHÒNG KIỂM TRA (TẠO ĐỀ CHUẨN MA TRẬN)
# ----------------------------------------------------
elif room_mode == "📝 Phòng Kiểm Tra (Đề & Ma trận)":
    st.title("📝 Khảo Sát & Biên Soạn Đề Kiểm Tra")
    st.write(f"Tạo đề kiểm tra môn **{subject} - Lớp 7** chuẩn Ma trận & Bản đặc tả GDPT 2018.")

    col1, col2 = st.columns(2)
    with col1:
        exam_type = st.selectbox("Hình thức kiểm tra:", ["Kiểm tra 15 phút", "Kiểm tra 45 phút (1 tiết)", "Kiểm tra Giữa kỳ", "Kiểm tra Cuối kỳ"])
    with col2:
        diff = st.selectbox("Mức độ phân hóa:", ["Chuẩn ma trận GDPT 2018 (Đủ 4 mức độ)", "Cơ bản ôn tập", "Nâng cao bồi dưỡng học sinh giỏi"])

    exam_topic = st.text_input("Chủ đề / Bài học kiểm tra:", value=f"Tuần {week}: {lesson_name}" if lesson_name else "")

    if st.button("📋 Biên soạn Đề & Ma trận chi tiết", type="primary"):
        if not exam_topic:
            st.warning("Vui lòng nhập chủ đề kiểm tra!")
        else:
            with st.spinner("Đang xây dựng ma trận đề, bản đặc tả và thang điểm chi tiết..."):
                prompt = f"""
                Bạn là tổ trưởng chuyên môn trường THCS môn {subject} Lớp 7 chương trình GDPT 2018.
                Hãy biên soạn đề kiểm tra:
                - Môn: {subject} - Lớp 7
                - Loại đề: {exam_type}
                - Mức độ: {diff}
                - Chủ đề/Tiết kiểm tra: {exam_topic}

                YÊU CẦU BẮT BUỘC THEO CẤU TRÚC:
                1. PHẦN I: KHUNG MA TRẬN VÀ BẢN ĐẶC TẢ ĐỀ THI
                   (Bảng phân phối tỉ lệ %: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao).
                2. PHẦN II: ĐỀ BÀI KIỂM TRA
                   (Trắc nghiệm khách quan + Tự luận rõ ràng từng câu, từng ý a, b, c).
                3. PHẦN III: HƯỚNG DẪN CHẤM, ĐÁP ÁN & THANG ĐIỂM
                   (Thang điểm chi tiết đến từng 0.25đ cho mỗi bước giải).
                """
                contents_exam = [prompt]
                if sgk_text:
                    contents_exam.insert(0, f"[DỮ LIỆU PPCT & SGK]:\n{sgk_text[:12000]}")

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents_exam,
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                st.markdown(response.text)
                st.session_state.exam_content = response.text

    if "exam_content" in st.session_state:
        st.download_button(
            label="📥 Tải xuống bộ đề thi (.md / Word)",
            data=st.session_state.exam_content,
            file_name=f"De_Kiem_Tra_{subject}_Lop7.md",
            mime="text/markdown"
        )
