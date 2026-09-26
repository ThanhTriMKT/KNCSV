import { ButtonLink } from "@/components/motion/button";

export function Hero() {
  return (
    <section className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-24 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
        Kết nối với Cựu sinh viên
        <br />
        <span className="text-accent">chỉ trong một câu hỏi.</span>
      </h1>
      <p className="max-w-xl text-muted-foreground">
        Hỏi AI về môn học, thực tập, hay một công ty cụ thể — AI sẽ tìm đúng cựu
        sinh viên phù hợp và giúp bạn kết nối an toàn, ẩn danh, không lộ thông
        tin liên hệ thật của cả hai bên.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <ButtonLink href="/app" variant="primary" size="lg">
          Trò chuyện ngay
        </ButtonLink>
        <ButtonLink href="/alumni" variant="outline" size="lg">
          Duyệt danh sách Cựu sinh viên
        </ButtonLink>
      </div>
    </section>
  );
}
