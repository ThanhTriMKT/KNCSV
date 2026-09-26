"""
PDF Parser & AI Extraction service for school documents (Admin upload flow).
"""

import io
from typing import Any, Literal

import pandas as pd
import pymupdf  # PyMuPDF
from loguru import logger
from pydantic import BaseModel, Field

from app.config import settings

DocumentType = Literal["grade_sheet", "internship_list", "course_enrollment", "general"]


def extract_text_from_file(file_bytes: bytes, filename: str = "document.pdf") -> str:
    """Extract raw text from PDF, CSV, or Excel binary."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext == "pdf":
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    elif ext in ("xlsx", "xls"):
        try:
            df_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
            texts = []
            for sheet_name, df in df_dict.items():
                texts.append(f"--- Sheet: {sheet_name} ---")
                texts.append(df.to_string(index=False))
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"Error parsing Excel file '{filename}': {e}")
            return ""
    elif ext == "csv":
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore")
    else:
        # Fallback to PyMuPDF
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Alias for backwards compatibility."""
    return extract_text_from_file(pdf_bytes, "document.pdf")


# ---------------------------------------------------------------------------
# Pydantic schema cho LangChain structured output
# ---------------------------------------------------------------------------


class StudentExtra(BaseModel):
    gpa: str | None = Field(None, description="Điểm trung bình (nếu bảng điểm)")
    company: str | None = Field(None, description="Công ty thực tập (nếu ds thực tập)")
    internship_role: str | None = Field(None, description="Vị trí thực tập (nếu có)")
    courses: list[str] = Field(default_factory=list, description="Danh sách môn học")


class StudentRecord(BaseModel):
    student_id: str | None = Field(None, description="Mã số sinh viên")
    full_name: str = Field(description="Họ và tên đầy đủ")
    email: str | None = Field(None, description="Email trường (nếu có)")
    phone: str | None = Field(None, description="Số điện thoại (nếu có)")
    extra: StudentExtra = Field(default_factory=StudentExtra)


class StudentList(BaseModel):
    students: list[StudentRecord] = Field(default_factory=list)


async def parse_student_document(
    raw_text: str,
    doc_type: DocumentType = "general",
) -> list[dict[str, Any]]:
    """
    Parse tài liệu trường (bảng điểm, ds thực tập, ds đăng ký môn) bằng LangChain
    structured output → trả về list dict chuẩn hoá.

    Trả về [] nếu không cấu hình API key hoặc extraction thất bại.
    """
    if not raw_text.strip():
        return []

    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY chưa cấu hình — trả về danh sách rỗng")
        return []

    doc_type_hint = {
        "grade_sheet": "bảng điểm (GPA, môn học, điểm số)",
        "internship_list": "danh sách thực tập (tên công ty, vị trí, thời gian)",
        "course_enrollment": "danh sách đăng ký môn học (tên môn, mã môn, số tín chỉ)",
        "general": "tài liệu sinh viên (bất kỳ thông tin nào có thể trích xuất)",
    }[doc_type]

    prompt = (
        f"Bạn là AI Parser trích xuất thông tin từ tài liệu trường đại học.\n"
        f"Đây là tài liệu loại: {doc_type_hint}.\n\n"
        f"Hãy trích xuất danh sách sinh viên/cựu sinh viên từ văn bản dưới đây.\n"
        f"Bỏ qua các dòng header/footer không phải thông tin sinh viên.\n"
        f"Nếu không tìm thấy danh sách sinh viên rõ ràng, trả về danh sách rỗng.\n\n"
        f"Văn bản tài liệu:\n{raw_text[:4000]}"
    )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )
        structured_llm = llm.with_structured_output(StudentList)
        result: StudentList = await structured_llm.ainvoke(prompt)
        return [r.model_dump() for r in result.students]
    except Exception as e:
        logger.error(f"parse_student_document thất bại: {e}")
        return []
