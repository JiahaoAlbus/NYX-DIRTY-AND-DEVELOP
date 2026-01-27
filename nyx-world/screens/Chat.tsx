import React, { useEffect, useState } from 'react';
import { createChatRoom, listChatMessages, listChatRooms, PortalSession, sendChatMessage } from '../api';

interface ChatProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
}

export const Chat: React.FC<ChatProps> = ({ backendOnline, session }) => {
  const [rooms, setRooms] = useState<Record<string, unknown>[]>([]);
  const [roomId, setRoomId] = useState('');
  const [roomName, setRoomName] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Record<string, unknown>[]>([]);
  const [receipt, setReceipt] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState('');

  const loadRooms = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!session) {
      setStatus('Portal sign-in required');
      return;
    }
    try {
      const payload = await listChatRooms(session.access_token);
      setRooms(payload.rooms || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const loadMessages = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!session) {
      setStatus('Portal sign-in required');
      return;
    }
    if (!roomId.trim()) {
      setStatus('Room ID required');
      return;
    }
    try {
      const payload = await listChatMessages(session.access_token, roomId.trim());
      setMessages(payload.messages || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const createRoom = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!session) {
      setStatus('Portal sign-in required');
      return;
    }
    if (!roomName.trim()) {
      setStatus('Room name required');
      return;
    }
    try {
      await createChatRoom(session.access_token, roomName.trim(), true);
      setStatus('Room created');
      setRoomName('');
      await loadRooms();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const sendMessage = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!session) {
      setStatus('Portal sign-in required');
      return;
    }
    if (!roomId.trim()) {
      setStatus('Room ID required');
      return;
    }
    if (!message.trim()) {
      setStatus('Message required');
      return;
    }
    try {
      const payload = await sendChatMessage(session.access_token, roomId.trim(), message.trim());
      setReceipt(payload);
      setMessage('');
      setStatus('Message sent');
      await loadMessages();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  useEffect(() => {
    if (backendOnline && session) {
      loadRooms();
    }
  }, [backendOnline, session]);

  const actionsDisabled = !backendOnline || !session;

  return (
    <div className="flex flex-col gap-6 pb-24">
      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Rooms</div>
        <div className="mt-2 flex gap-2">
          <label className="text-xs text-text-subtle">Room name</label>
          <input className="h-9 flex-1 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Room name" value={roomName} onChange={(e) => setRoomName(e.target.value)} />
          <button onClick={createRoom} className="h-9 px-4 rounded-lg bg-primary text-background-dark text-sm font-semibold" disabled={actionsDisabled}>Create</button>
        </div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(rooms, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Messages</div>
        <label className="mt-2 text-xs text-text-subtle">Room ID</label>
        <input className="mt-2 h-9 w-full rounded-lg border border-primary/20 px-3 text-sm" aria-label="Room ID" value={roomId} onChange={(e) => setRoomId(e.target.value)} />
        <button onClick={loadMessages} className="mt-2 h-9 w-full rounded-lg border border-primary/20 text-sm" disabled={actionsDisabled}>Refresh</button>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(messages, null, 2)}</pre>
        <div className="mt-3 flex gap-2">
          <label className="text-xs text-text-subtle">Message</label>
          <input className="h-9 flex-1 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Message" value={message} onChange={(e) => setMessage(e.target.value)} />
          <button onClick={sendMessage} className="h-9 px-4 rounded-lg bg-primary text-background-dark text-sm font-semibold" disabled={actionsDisabled}>Send</button>
        </div>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Latest Receipt</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(receipt ?? {}, null, 2)}</pre>
      </section>

      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
