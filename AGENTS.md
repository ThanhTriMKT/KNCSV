## Cấu trúc dự án

```text
alumni/
├── backend/          # FastAPI backend
    ├── /app
        ├── /database
        ├── /routers
        └── /mcp
        └── /services
        └── main.py
├── frontend/         # Next.js frontend
├── package.json      # Script chạy toàn dự án
└── .gitignore
```

## Nguyên tắc

- Tìm kiếm có thư viện hỗ trợ trước khi viết.
- Tuân thủ quy tắc: (Đặc biệt quan trọng)
  - 1. Does this need to exist? → no: skip it (YAGNI)
  - 2. Already in this codebase? → reuse it, don't rewrite
  - 3. Stdlib does it? → use it
  - 4. Native platform feature? → use it
  - 5. Installed dependency? → use it
  - 6. One line? → one line

## Ý tưởng dự án:

@docs/SPEC.md
