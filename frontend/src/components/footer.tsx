import { GraduationCap, Heart, Mail, MapPin, Phone } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="w-full border-t border-border bg-card/50 text-foreground transition-colors mt-auto">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Col 1 */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-xs">
                <GraduationCap className="size-5" />
              </div>
              <span className="font-bold text-base tracking-tight">ALUMNI PORTAL</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Cổng thông tin kết nối Cựu sinh viên, Doanh nghiệp và Sinh viên Khoa Công nghệ Thông tin. Đồng hành cùng sự phát triển của các thế hệ sinh viên.
            </p>
          </div>

          {/* Col 2 */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Phân hệ Chức năng
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/alumni" className="text-muted-foreground hover:text-primary transition-colors">
                  Cơ sở dữ liệu Cựu sinh viên
                </Link>
              </li>
              <li>
                <Link href="/jobs" className="text-muted-foreground hover:text-primary transition-colors">
                  Tuyển dụng & Việc làm
                </Link>
              </li>
              <li>
                <Link href="/events" className="text-muted-foreground hover:text-primary transition-colors">
                  Sự kiện & Hội thảo
                </Link>
              </li>
              <li>
                <Link href="/surveys" className="text-muted-foreground hover:text-primary transition-colors">
                  Khảo sát việc làm
                </Link>
              </li>
              <li>
                <Link href="/financial-aid" className="text-muted-foreground hover:text-primary transition-colors">
                  Quỹ học bổng cựu sinh viên
                </Link>
              </li>
              <li>
                <Link href="/career-advisor" className="text-muted-foreground hover:text-primary transition-colors">
                  Trợ lý Hướng nghiệp DLU
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3 */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Thông tin Liên hệ
            </h4>
            <ul className="space-y-2.5 text-xs text-muted-foreground">
              <li className="flex items-start gap-2">
                <MapPin className="size-4 shrink-0 text-primary mt-0.5" />
                <span>Khoa CNTT — Trường Đại học Đà Lạt, 01 Phù Đổng Thiên Vương, TP. Đà Lạt</span>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="size-4 shrink-0 text-primary" />
                <span>khoacntt@dlu.edu.vn</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="size-4 shrink-0 text-primary" />
                <span>(0263) 3822 246</span>
              </li>
            </ul>
          </div>

          {/* Col 4 */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Đồng hành
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Mỗi sự đóng góp, tham gia sự kiện và tin tuyển dụng từ Quý Cựu sinh viên là nguồn động lực to lớn cho sinh viên vững bước tương lai.
            </p>
            <div className="pt-2">
              <Link
                href="/financial-aid"
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600/10 border border-emerald-600/20 px-3 py-1.5 text-xs font-semibold text-emerald-600 hover:bg-emerald-600 hover:text-white transition-all"
              >
                <Heart className="size-3.5 fill-current" />
                Đóng góp Quỹ học bổng
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-8 border-t border-border/60 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-muted-foreground">
          <p>© {new Date().getFullYear()} Alumni Portal — Khoa Công nghệ Thông tin. All rights reserved.</p>
          <p className="mt-2 sm:mt-0 flex items-center gap-1">
            Thiết kế & phát triển cho cộng đồng Cựu sinh viên & Sinh viên
          </p>
        </div>
      </div>
    </footer>
  );
}
