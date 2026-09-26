# Alumni — Thiết kế giao diện Chat AI

> Spec này hướng dẫn build UI cho luồng **AI Broker** (SPEC §2) bằng cách
> tái dùng bộ component `beUI` đã có trong `src/components/agents/`.
> Không viết lại component có sẵn.

---

## 1. Màn hình duy nhất: Chat Page

File cần tạo: `src/app/page.tsx` → render `<AlumniChat />`  
File component: `src/components/alumni-chat.tsx`

Layout:

```
┌─────────────────────────────────────────────┐
│  Header (tĩnh)                              │
├─────────────────────────────────────────────┤
│                                             │
│  MessageScroller  (flex-1, auto-scroll)     │
│  ├─ [tin nhắn cũ]                          │
│  ├─ Message (user bubble)                   │
│  ├─ Message (assistant)                     │
│  │   ├─ AgentActivity  ← đang tìm CSV      │
│  │   └─ StreamingResponse ← câu trả lời    │
│  └─ ThinkingShimmer  ← khi đang chờ        │
│                                             │
├─────────────────────────────────────────────┤
│  PromptInput  (sticky bottom)               │
└─────────────────────────────────────────────┘
```

---

## 2. State & kiểu dữ liệu

```ts
// src/components/alumni-chat.tsx

type MessageFrom = "user" | "assistant";

interface ChatMessage {
  id: string;
  from: MessageFrom;
  content: string;
  streaming?: boolean;
  // chỉ có ở assistant message khi AI đang tìm CSV
  activity?: AgentActivityItem[];
  activityStatus?: AgentActivityStatus;
}

// State tối thiểu
const [messages, setMessages]       = useState<ChatMessage[]>([]);
const [input, setInput]             = useState("");
const [pending, setPending]         = useState(false);      // đang gửi HTTP
const [activeReply, setActiveReply] = useState<string | null>(null); // id đang stream
const abortRef = useRef<AbortController | null>(null);
```

---

## 3. Component mapping

### 3.1 `PromptInput`

```tsx
import { PromptInput } from "@/components/agents/prompt-input";

<PromptInput
  value={input}
  onValueChange={setInput}
  loading={busy}          // busy = pending || activeReply !== null
  onStop={stop}
  onSubmit={submit}
  minRows={1}
  maxRows={5}
  placeholder="Hỏi về môn học, thực tập, định hướng nghề nghiệp…"
/>
```

**Props cần thiết:**

| Prop | Giá trị | Ghi chú |
|------|---------|---------|
| `loading` | `busy` | Tự đổi icon → ■ Stop |
| `onStop` | `() => abortRef.current?.abort()` | Huỷ stream SSE |
| `onSubmit` | `(text) => submit(text)` | Gọi `/chat` |
| `minRows` / `maxRows` | 1 / 5 | Textarea tự resize |

---

### 3.2 `MessageScroller`

```tsx
import { MessageScroller } from "@/components/agents/message-scroller";

<MessageScroller
  busy={busy}
  navigation="rail"
  className="flex-1 min-h-0"
  viewportClassName="px-4 py-6"
  contentClassName="mx-auto w-full max-w-2xl"
>
  {/* nội dung §4 */}
</MessageScroller>
```

**Props quan trọng:**

| Prop | Mặc định | Tác dụng |
|------|----------|---------|
| `busy` | `false` | `aria-busy` khi đang stream |
| `navigation="rail"` | — | Thanh preview click-to-scroll |
| `followOutput` | `true` | Auto-scroll khi content mới đến |

---

### 3.3 `AgentActivity`

Hiển thị trong **assistant message** trong khi AI đang xử lý
(RAG search → tìm CSV → soạn brief).

```tsx
import { AgentActivity } from "@/components/agents/agent-activity";
import type {
  AgentActivityItem,
  AgentActivityStatus,
} from "@/components/agents/agent-activity";

<AgentActivity
  status={msg.activityStatus}   // "working" | "complete"
  items={msg.activity ?? []}
  collapseOnComplete             // tự thu lại khi xong
/>
```

**Các `AgentActivityItem` dùng cho Alumni:**

```ts
// AI đang search hồ sơ CSV (RAG)
{ id: "search", type: "search",
  query: "internship data engineer K18",
  results: [{ id: "r1", title: "Anh N.V.A — Senior DA", domain: "alumni" }] }

// AI soạn brief
{ id: "draft", type: "tool", action: "run", target: "Soạn brief tư vấn" }

// AI gọi MCP tool gửi Zalo
{ id: "zalo", type: "tool", action: "run", target: "Gửi lời mời qua Zalo OA" }

// Reasoning text
{ id: "reason", type: "text",
  content: "Đang phân tích câu hỏi và tìm CSV phù hợp…" }
```

**Mapping SSE event → activity:**  
Backend stream theo thứ tự:

```
event: activity
data: {"type":"search","query":"..."}

event: activity
data: {"type":"tool","action":"run","target":"..."}

event: chunk
data: Câu trả lời tổng hợp...

event: done
data:
```

---

### 3.4 `StreamingResponse`

Hiển thị câu trả lời text từ AI, có nút copy, feedback, sources.

```tsx
import { StreamingResponse } from "@/components/agents/streaming-response";

<StreamingResponse
  status={msg.streaming ? "streaming" : "complete"}
  copyText={msg.content}
  showActions={!msg.streaming}
>
  {msg.content}
</StreamingResponse>
```

**Props hay dùng:**

| Prop | Tác dụng |
|------|---------|
| `status` | `"streaming"` ẩn actions; `"complete"` hiện copy/feedback |
| `copyText` | Plain text cho nút copy |
| `sources` | `CitationItem[]` — gắn CSV gợi ý vào đây |
| `onRetry` | Gọi lại `/chat` với cùng câu hỏi |

---

## 4. Cấu trúc JSX bên trong `MessageScroller`

```tsx
<MessageGroup spacing="default">
  {messages.map((msg) => (
    <Message key={msg.id} from={msg.from} animateIn>
      <MessageAvatar>
        {msg.from === "user" ? <User /> : <Bot />}
      </MessageAvatar>

      <MessageContent className="gap-3">
        {msg.from === "assistant" && (
          <MessageHeader>
            <span>AI Alumni</span>
          </MessageHeader>
        )}

        {/* Activity: chỉ hiện khi assistant đang xử lý */}
        {msg.activity && (
          <AgentActivity
            status={msg.activityStatus}
            items={msg.activity}
            collapseOnComplete
          />
        )}

        {/* Nội dung text */}
        {msg.content && (
          <MessageBubble variant={msg.from === "user" ? "solid" : "ghost"}>
            <MessageBubbleContent>
              {msg.from === "assistant" ? (
                <StreamingResponse
                  status={msg.streaming ? "streaming" : "complete"}
                  copyText={msg.content}
                  showActions={!msg.streaming}
                >
                  {msg.content}
                </StreamingResponse>
              ) : (
                msg.content
              )}
            </MessageBubbleContent>
          </MessageBubble>
        )}
      </MessageContent>
    </Message>
  ))}

  {/* Skeleton khi chờ response */}
  {pending && (
    <Message from="assistant" animateIn>
      <MessageAvatar><Bot /></MessageAvatar>
      <MessageContent>
        <ThinkingShimmer>Đang tìm kiếm cựu sinh viên phù hợp</ThinkingShimmer>
      </MessageContent>
    </Message>
  )}
</MessageGroup>
```

---

## 5. Luồng submit → stream

```
submit(text)
  ├─ setMessages([...prev, { from:"user", content: text }])
  ├─ setPending(true)
  ├─ setMessages([...prev, { id: aId, from:"assistant",
  │                          content:"", streaming:true,
  │                          activity:[], activityStatus:"working" }])
  ├─ setPending(false)
  └─ sendChatMessage(text, {
       onActivityItem: (item) =>
         setMessages(cur => cur.map(m =>
           m.id === aId
             ? { ...m, activity: [...(m.activity ?? []), item] }
             : m
         )),
       onChunk: (text) =>
         setMessages(cur => cur.map(m =>
           m.id === aId
             ? { ...m, content: m.content + text, activityStatus:"complete" }
             : m
         )),
     })
     .finally(() => {
       setMessages(cur => cur.map(m =>
         m.id === aId ? { ...m, streaming: false } : m
       ));
       setActiveReply(null);
     });
```

---

## 6. Mở rộng `lib/api.ts`

Thêm `onActivityItem` vào `SendChatMessageOptions`:

```ts
interface SendChatMessageOptions {
  onChunk: (text: string) => void;
  onActivityItem?: (item: AgentActivityItem) => void;  // thêm
  signal?: AbortSignal;
}
```

Parse thêm `event: activity` trong `parseSseStream`:

```ts
if (event === "activity" && data) {
  try { onActivityItem?.(JSON.parse(data)); } catch { /* skip */ }
}
if (event === "chunk" && data) onChunk(data);
if (event === "done") return;
```

---

## 7. Checklist file cần làm

| File | Việc |
|------|------|
| `src/components/alumni-chat.tsx` | **[MỚI]** Component chính |
| `src/app/page.tsx` | Sửa: import `AlumniChat` |
| `src/lib/api.ts` | Thêm `onActivityItem` + parse `event: activity` |

> `alumni-app.tsx` đã xoá.
