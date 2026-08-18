"""موتور پرسش از دادهٔ ریپوی مصحف محشی.

سؤال‌ها را ذخیره نمی‌کند. فقط از data/ و docs/ و یادداشت‌های موجود می‌خواند.
"""

from .ask import ask, format_pack
from .models import ContextPack

__all__ = ["ask", "format_pack", "ContextPack"]
