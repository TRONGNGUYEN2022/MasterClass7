import os
import gdown
import streamlit as st
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types

# Cấu hình giao diện Streamlit tối ưu cho iPad
st.set_page_config(
    page_title="Gia Sư & Luyện Đề Lớp 7",
    page_icon="🎒",
    layout="centered"
)

# ----------------------------------------------------
# 1. CẤU HÌNH API KEY & GOOGLE DRIVE
# ----------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
gdrive_folder_id = st.secrets.get("GDRIVE_FOLDER_ID", os.getenv("GDRIVE_FOLDER_ID"))

if not api_key:
    api_key = st.sidebar.text_input("🔑 Nhập Gemini API Key:", type="password")
    if not api_key:
        st.warning("Vui lòng cấu hình GEMINI_API_KEY để bắt đầu!")
        st.stop()

if not gdrive_folder_id:
    gdrive_folder_id = st.sidebar.text_input("📁 Nhập Google Drive Folder ID:")

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 2. TỰ ĐỘNG ĐỒNG BỘ SGK TỪ GOOGLE DRIVE
# ----------------------------------------------------
DATA_DIR = "./data_gdrive"

@st.cache_resource(show_spinner="⏳ Đang đồng bộ SGK từ Google Drive (chỉ tải 1 lần)...")
def sync_sgk_from_drive(folder_id):
    if not folder_id:
        return ""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        try:
            gdown.download_folder(url, output=DATA_DIR, quiet=True, use_cookies=False)
        except Exception as e:
            st.sidebar.error(f"Lỗi tải từ Google Drive: {e}")
            return ""
    
    extracted_text = ""
    for file_name in os.listdir(DATA_DIR):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(DATA_DIR, file_name)
            try:
                reader = PdfReader(pdf_path)
                extracted_text += f"\n--- TÀI LIỆU: {file_name} ---\n"
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            except Exception:
                continue
    return extracted_text

sgk_text = sync_sgk_from_drive(gdrive_folder_id) if gdrive_folder_id else ""

# ----------------------------------------------------
# 3. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ----------------------------------------------------
st.sidebar.title("🎒 Góc Học Tập Lớp 7")

app_mode = st.sidebar.radio(
    "Chọn chế độ:",
    ["💬 Phòng Gia Sư AI (Hỏi bài)", "📝 Phòng Tạo Đề Kiểm Tra"]
)

subject = st.sidebar.selectbox(
    "Môn học lớp 7:",
    ["Toán học", "Khoa học tự nhiên", "Ngữ văn", "Tiếng Anh", "Lịch sử & Địa lí", "Tin học", "GDCD"]
)

if sgk_text:
    st.sidebar.success("✅ Đã kết nối SGK từ Google Drive")
else:
    st.sidebar.info("ℹ️ Chưa liên kết SGK Drive (Dùng AI gốc)")

if st.sidebar.button("🗑️ Làm mới đoạn chat"):
    st.session_state.messages = []
    st.rerun()

# ----------------------------------------------------
# 4. PROMPT HỆ THỐNG GIA SƯ SƯ PHẠM LỚP 7
# ----------------------------------------------------
SYSTEM_PROMPT = f"""Bạn là "Gia sư Trí Tuệ", một gia sư kiên nhẫn, thân thiện và thấu hiểu tâm lý cho học sinh lớp 7 (12-13 tuổi) theo chương trình GDPT 2018 của Việt Nam.

QUY TẮC XỬ LÝ THEO YÊU CẦU CỦA NGƯỜI HỌC:
1. TRƯỜNG HỢP CẦN ĐÁP ÁN NGAY (Khi người học yêu cầu: "cho xin đáp án", "giải nhanh", "giải chi tiết", "làm mẫu", hoặc cần kiểm tra kết quả gấp):
   - Cung cấp NGAY kết quả/lời giải hoàn chỉnh và chính xác.
   - Giải thích tường tận, mạch lạc theo từng bước (Bước 1, Bước 2...).
   - Trình bày trực quan, sinh động (dùng bảng biểu, công thức rõ ràng, ví dụ so sánh đời sống thực tế gần gũi).
2. TRƯỜNG HỢP HỌC TẬP TỰ NHIÊN / HỎI BÀI THÔNG THƯỜNG:
   - Áp dụng phương pháp Gợi mở (Socratic): Không đưa ngay đáp án cuối cùng hoặc bài văn mẫu.
   - Chia nhỏ bài toán/câu hỏi thành từng bước gợi ý để học sinh tự suy nghĩ và giải quyết.
   - Kiểm tra hiểu bài: Sau mỗi bước gợi ý, đặt một câu hỏi nhỏ để xác nhận học sinh đã hiểu trước khi tiếp tục.
3. NGUYÊN TẮC THEO MÔN (Lớp 7):
   - Toán/KHTN: Bám sát công thức, định nghĩa, liên hệ thực tế.
   - Ngữ văn: Hướng dẫn dàn ý, biện pháp nghệ thuật, cảm xúc, không chép văn mẫu.
   - Tiếng Anh: Giải thích ngữ pháp ngắn gọn, kèm ví dụ thực tế.
4. Giọng điệu: Tích cực, khích lệ, khen ngợi sự nỗ lực của con.
[Môn học hiện tại: {subject} - Lớp 7]
"""

# ----------------------------------------------------
# 5. TÍNH NĂNG 1: PHÒNG GIA SƯ AI
# ----------------------------------------------------
if app_mode == "💬 Phòng Gia Sư AI (Hỏi bài)":
    st.title("🎓 Gia Sư AI - Dành Riêng Cho Lớp 7")
    st.caption(f"Đang đồng hành môn: **{subject}**")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Hiển thị lịch sử chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "image" in msg and msg["image"]:
                st.image(msg["image"])
            st.write(msg["text"])

    uploaded_file = st.file_uploader("📸 Chụp hoặc tải ảnh bài tập (iPad):", type=["png", "jpg", "jpeg"])
    user_input = st.chat_input("Nhập câu hỏi bài tập cần thầy hướng dẫn...")

    if user_input or uploaded_file:
        image_obj = None
        if uploaded_file:
            image_obj = Image.open(uploaded_file)

        with st.chat_message("user"):
            if image_obj:
                st.image(image_obj, caption="Ảnh bài tập bạn gửi")
            if user_input:
                st.write(user_input)

        st.session_state.messages.append({
            "role": "user",
            "text": user_input if user_input else "[Đã gửi ảnh bài tập]",
            "image": image_obj
        })

        # Chuẩn bị payload gửi Gemini
        contents_payload = []
        if sgk_text:
            # Trích xuất đoạn SGK liên quan (rút gọn theo ngữ cảnh)
            contents_payload.append(f"[THÔNG TIN THAM KHẢO SGK LỚP 7 MÔN {subject}]:\n" + sgk_text[:12000])
        
        if image_obj:
            contents_payload.append(image_obj)
            
        prompt_text = user_input if user_input else "Hãy hướng dẫn em làm bài tập trong ảnh này."
        contents_payload.append(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("Thầy đang phân tích và chuẩn bị hướng dẫn cho con..."):
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
# 6. TÍNH NĂNG 2: PHÒNG TẠO ĐỀ KIỂM TRA LỚP 7
# ----------------------------------------------------
elif app_mode == "📝 Phòng Tạo Đề Kiểm Tra":
    st.title("📝 Trình Tạo Đề Kiểm Tra Lớp 7")
    st.write(f"Biên soạn đề kiểm tra môn **{subject} - Lớp 7** theo chuẩn ma trận đề GDPT 2018.")

    col1, col2 = st.columns(2)
    with col1:
        exam_type = st.selectbox("Loại đề:", ["15 phút", "45 phút (1 tiết)", "Giữa học kỳ", "Cuối học kỳ"])
    with col2:
        difficulty = st.selectbox("Mức độ:", ["Cơ bản (Nhận biết - Thông hiểu)", "Chuẩn (Đủ 4 mức độ)", "Nâng cao (Học sinh giỏi)"])

    topic_focus = st.text_input("Nhập chủ đề/bài học cụ thể (Ví dụ: Số hữu tỉ, Tam giác bằng nhau, Quang hợp, Tốc độ chuyển động...):")

    if st.button("🚀 Bắt đầu tạo đề", type="primary"):
        if not topic_focus:
            st.warning("Vui lòng nhập chủ đề để AI biên soạn chính xác nhất!")
        else:
            with st.spinner(f"Đang soạn đề kiểm tra môn {subject} lớp 7..."):
                prompt = f"""
                Bạn là giáo viên biên soạn đề thi THCS chương trình GDPT 2018 của Việt Nam.
                Hãy soạn một đề kiểm tra môn {subject} - Lớp 7, loại đề: {exam_type}, mức độ: {difficulty}.
                Chủ đề trọng tâm: {topic_focus}.
                
                YÊU CẦU:
                1. Phần I: Trắc nghiệm khách quan (4 lựa chọn A, B, C, D) hoặc Tự luận ngắn.
                2. Phần II: Tự luận (chia câu, các ý a, b, c rõ ràng).
                3. Hướng dẫn giải chi tiết và Thang điểm cụ thể cho từng câu.
                Trình bày đẹp mắt bằng Markdown.
                """
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt],
                    config=types.GenerateContentConfig(temperature=0.4)
                )
                st.success("🎉 Đã tạo đề kiểm tra thành công!")
                st.markdown("---")
                st.markdown(response.text)
                st.session_state.last_exam = response.text

    if "last_exam" in st.session_state:
        st.download_button(
            label="📥 Tải xuống đề thi (.md / .txt)",
            data=st.session_state.last_exam,
            file_name=f"De_Kiem_Tra_Lop7_{subject}.md",
            mime="text/markdown"
        )