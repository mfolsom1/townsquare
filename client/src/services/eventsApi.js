// Frontend-only data layer for now. Swap to real API later.
const KEY = "tsq_events";
const bus = new EventTarget();

function read() {
  return JSON.parse(localStorage.getItem(KEY) || "[]");
}
function write(events) {
  localStorage.setItem(KEY, JSON.stringify(events));
  bus.dispatchEvent(new Event("changed"));     // notify this tab
}
export async function listEvents() {
  return read().sort((a,b) => new Date(a.startAt) - new Date(b.startAt));
}
export function subscribeToEvents(callback) {
  callback(read());                            // initial snapshot
  const onChanged = () => callback(read());
  bus.addEventListener("changed", onChanged);
  const onStorage = (e) => { if (e.key === KEY) callback(read()); };
  window.addEventListener("storage", onStorage);
  return () => {
    bus.removeEventListener("changed", onChanged);
    window.removeEventListener("storage", onStorage);
  };
}
export async function createEvent(data) {
  const events = read();
  const ev = {
    id: crypto.randomUUID(),
    title: data.title?.trim() || "Untitled Event",
    desc: data.desc?.trim() || "",
    category: data.category || "",
    startAt: data.startAt || null,             // ISO string "YYYY-MM-DDTHH:mm"
    location: data.location || "",
    coverUrl: data.coverUrl || null,
    createdAt: new Date().toISOString(),
  };
  events.push(ev);
  write(events);
  return ev;
}
