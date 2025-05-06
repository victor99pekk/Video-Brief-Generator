import { useState, useRef, useEffect } from "react";
import axios from "axios";

const API = import.meta.env.VITE_BRIEF_API || "http://localhost:8001";

export default function BriefChat() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! Drop me a song title + artist 🚀" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const [song, ...artistArr] = userMsg.text.split(" by ");
      const artist = artistArr.join(" by ");        // allow “Paint It Black by Rolling Stones”

      const { data } = await axios.post(`${API}/generate`, {
        song: song.trim(),
        artist: artist.trim(),
      });

      const brief = data.brief || JSON.stringify(data, null, 2);
      setMessages((m) => [...m, { role: "assistant", text: brief }]);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        "Unknown error, check backend log.";
      setMessages((m) => [...m, { role: "assistant", text: `❌ ${detail}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Chat window */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <ChatBubble key={idx} msg={msg} />
        ))}
        <div ref={endRef} />
      </div>

      {/* Input bar */}
      <form
        onSubmit={handleSubmit}
        className="bg-white p-4 flex gap-2 shadow-inner"
      >
        <input
          className="flex-1 border rounded px-3 py-2"
          placeholder='e.g. "Paint It Black by Rolling Stones"'
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white rounded px-4"
        >
          {loading ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}

function ChatBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} animate__animated animate__fadeInUp`}
    >
      <div
        className={`max-w-xl p-3 rounded-lg shadow ${
          isUser
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-gray-200 text-gray-900 rounded-bl-none"
        }`}
      >
        {msg.text}
      </div>
    </div>
  );
}
