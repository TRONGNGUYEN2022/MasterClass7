import os
import gdown
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Lớp Học Số Lớp 7 - Trường Học AI",
    page_icon="🏫",
    layout="wide"
)

# ----------------------------------------------------
# 1. CẤU HÌNH API & GOOGLE DRIVE
# ----------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
gdrive_folder_id = st.secrets.get("GDRIVE_FOLDER_ID", os.getenv("GDRIVE_FOLDER_ID"))

if not api_key:
    api_key = st.sidebar.text_input("🔑 Nhập Gemini API Key:", type="password")
    if not api_key:
        st.warning("Vui lòng cấu hình GEMINI_API_KEY!")
        st.stop()

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 2. ĐỒNG BỘ TÀI LIỆU SGK & PPCT TỪ GOOGLE DRIVE
# ----------------------------------------------------
DATA_DIR = "./data_gdrive"

@st.cache_resource(show_spinner="⏳ Đang mở kho sách & Phân phối chương trình...")
def sync_sgk_from_drive(folder_id):
    if not folder_id:
        return ""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        try:
            gdown.download_folder(url, output=DATA_DIR, quiet=True, use_cookies=False)
        except Exception:
            return ""
    
    extracted_text = ""
    for file_name in os.listdir(DATA_DIR):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(DATA_DIR, file_name)
            try:
                reader = PdfReader(pdf_path)
                extracted_text += f"\n--- TÀI LIỆU: {file_name} ---\n"
                for page in reader.pages[:20]:  # Đọc trích dẫn
                    t = page.extract_text()
                    if t: extracted_text += t + "\n"
            except Exception:
                continue
    return extracted_text

sgk_text = sync_sgk_from_drive(gdrive_folder_id) if gdrive_folder_id else ""

# ----------------------------------------------------
# 3. THỜI KHÓA BIỂU & PHÂN PHỐI CHƯƠNG TRÌNH (PPCT)
# ----------------------------------------------------
st.sidebar.title("🏫 Trường Học Số Lớp 7")

subject = st.sidebar.selectbox(
    "📚 Chọn Môn học:",
    ["Toán học", "Khoa học tự nhiên", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lí", "Tin học", "GDCD"]
)

room_mode = st.sidebar.radio(
    "🚪 Chọn Phòng chức năng:",
    ["👩‍🏫 Phòng Giảng Bài (Theo Tiết)", "💬 Phòng Gia Sư (Hỏi & Giải bài)", "📝 Phòng Kiểm Tra (Đề & Ma trận)"]
)

# Sidebar chọn tuần và bài học
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Kế hoạch bài dạy (PPCT)")
week = st.sidebar.slider("Chọn Tuần học:", min_value=1, max_value=35, value=1)
lesson_name = st.sidebar.text_input("Tên bài học / Tiết dạy:", placeholder="Ví dụ: Tiết 5 - Số vô tỉ, Căn bậc hai")

if st.sidebar.button("🗑️ Đổi tiết học mới"):
    st.session_state.messages = []
    st.session_state.classroom_state = None
    st.rerun()

# ----------------------------------------------------
# PHÒNG 1: PHÒNG GIẢNG BÀI (VIRTUAL CLASSROOM)
# ----------------------------------------------------
if room_mode == "👩‍🏫 Phòng Giảng Bài (Theo Tiết)":
    st.title(f"👩‍🏫 Lớp Học Trực Tuyến - Môn {subject}")
    st.caption(f"🗓️ **Tuần {week}** | 📖 Bài học: **{lesson_name if lesson_name else 'Chưa chọn bài cụ thể'}**")

    if not lesson_name:
        st.info("👈 Con hãy nhập **Tên bài học hoặc Tiết dạy** ở thanh bên trái để Thầy/Cô bắt đầu tiết học nhé!")
    else:
        st.markdown(f"### 🎯 Tiến trình tiết học: {lesson_name}")
        step = st.radio(
            "Giai đoạn bài học:",
            ["1. 🚀 Khởi động & Giới thiệu", "2. 📖 Giảng kiến thức trọng tâm", "3. ✏️ Luyện tập tại lớp", "4. 🌟 Vận dụng & Dặn dò"],
            horizontal=True
        )

        TEACHER_PROMPT = f"""Bạn là Thầy/Cô giáo chuyên môn môn {subject} Lớp 7 theo chương trình GDPT 2018.
Hôm nay bạn đang dạy:
- Tuần: {week}
- Tên bài/Tiết học: {lesson_name}
- Giai đoạn đang dạy: {step}

YÊU CẦU DẠY HỌC:
- Xưng hô: Thầy/Cô và con/em.
- Giọng điệu: Truyền cảm, ân cần, khích lệ, chuẩn tác phong sư phạm.
- Nếu ở mục 1 (Khởi động): Đưa câu chuyện thực tế hoặc câu đố dẫn nhập thú vị.
- Nếu ở mục 2 (Giảng bài): Giảng giải ngắn gọn, mạch lạc, dùng ví dụ so sánh đời sống, công thức đóng khung rõ ràng.
- Nếu ở mục 3 (Luyện tập): Đưa ra 2 bài tập nhỏ và khuyến khích con thử làm.
- Nếu ở mục 4 (Vận dụng): Tóm tắt 3 điều cốt lõi cần nhớ và dặn dò bài tập về nhà.
"""
        if st.button("🔔 Bắt đầu phần này"):
            with st.spinner("Thầy/Cô đang chuẩn bị giáo án lên bảng..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[f"Hãy tiến hành giảng dạy phần: {step} của bài {lesson_name}."],
                    config=types.GenerateContentConfig(
                        system_instruction=TEACHER_PROMPT,
                        temperature=0.3
                    )
                )
                st.markdown(response.text)

# ----------------------------------------------------
# PHÒNG 2: PHÒNG GIA SƯ (HỎI ĐÁP & CHỮA BÀI)
# ----------------------------------------------------
elif room_mode == "💬 Phòng Gia Sư (Hỏi & Giải bài)":
    st.title("💬 Bàn Hỏi Bài & Giải Đáp")
    st.caption(f"Đồng hành cùng con môn **{subject}**")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "image" in msg and msg["image"]:
                st.image(msg["image"])
            st.write(msg["text"])

    uploaded_file = st.file_uploader("📸 Tải ảnh bài tập (iPad):", type=["png", "jpg", "jpeg"])
    user_input = st.chat_input("Hỏi thầy/cô bất cứ điều gì con chưa hiểu...")

    if user_input or uploaded_file:
        image_obj = None
        if uploaded_file:
            image_obj = Image.open(uploaded_file)

        with st.chat_message("user"):
            if image_obj: st.image(image_obj)
            if user_input: st.write(user_input)

        st.session_state.messages.append({
            "role": "user",
            "text": user_input if user_input else "[Ảnh bài tập]",
            "image": image_obj
        })

        TUTOR_PROMPT = f"""Bạn là Thầy/Cô gia sư môn {subject} Lớp 7.
- Nếu học sinh hỏi đáp án hoặc nhờ giải chi tiết: Lập tức trình bày lời giải mẫu tường tận từng bước, dễ hiểu.
- Nếu học sinh hỏi bài bình thường: Gợi ý từng bước (Socratic) để con tự tư duy.
- Luôn thân thiện, động viên con."""

        contents = []
        if sgk_text: contents.append(sgk_text[:10000])
        if image_obj: contents.append(image_obj)
        contents.append(user_input if user_input else "Hướng dẫn bài này giúp con với ạ.")

        with st.chat_message("assistant"):
            with st.spinner("Thầy/Cô đang hướng dẫn..."):
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(system_instruction=TUTOR_PROMPT, temperature=0.3)
                )
                st.write(resp.text)

        st.session_state.messages.append({"role": "assistant", "text": resp.text})

# ----------------------------------------------------
# PHÒNG 3: PHÒNG KIỂM TRA (TẠO ĐỀ CHUẨN MA TRẬN)
# ----------------------------------------------------
elif room_mode == "📝 Phòng Kiểm Tra (Đề & Ma trận)":
    st.title("📝 Khảo Sát & Kiểm Tra Chuẩn Ma Trận")
    col1, col2 = st.columns(2)
    with col1:
        exam_type = st.selectbox("Hình thức kiểm tra:", ["Kiểm tra 15 phút", "Kiểm tra 1 tiết (45 phút)", "Giữa học kỳ", "Cuối học kỳ"])
    with col2:
        diff = st.selectbox("Mức độ đề:", ["Chuẩn ma trận GDPT 2018 (4 mức độ)", "Cơ bản ôn tập", "Nâng cao bồi dưỡng"])

    exam_topic = st.text_input("Nội dung / Tuần kiểm tra:", value=f"Tuần {week}: {lesson_name}" if lesson_name else "")

    if st.button("📋 Biên soạn đề kiểm tra & Ma trận", type="primary"):
        with st.spinner("Đang xây dựng ma trận đề, bản đặc tả và đề bài chuẩn..."):
            prompt = f"""
            Bạn là tổ trưởng chuyên môn trường THCS môn {subject} lớp 7.
            Hãy soạn đề kiểm tra {exam_type}, mức độ: {diff} cho nội dung: {exam_topic}.
            
            CẤU TRÚC GỒM 3 PHẦN:
            1. BẢNG MA TRẬN & BẢN ĐẶC TẢ ĐỀ (Nhận biết - Thông hiểu - Vận dụng - Vận dụng cao).
            2. ĐỀ BÀI KIỂM TRA (Trắc nghiệm + Tự luận).
            3. HƯỚNG DẪN CHẤM, ĐÁP ÁN & BIỂU ĐIỂM (Chi tiết từng 0.25đ).
            """
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(temperature=0.3)
            )
            st.markdown(resp.text)
            st.session_state.exam_content = resp.text

    if "exam_content" in st.session_state:
        st.download_button(
            label="📥 Tải đề kiểm tra (.md / Word)",
            data=st.session_state.exam_content,
            file_name=f"De_Kiem_Tra_{subject}_Lop7.md"
        )