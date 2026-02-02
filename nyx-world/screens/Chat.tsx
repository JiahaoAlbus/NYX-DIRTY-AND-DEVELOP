import React, { useEffect, useState, useRef } from 'react';
import {
  createChatRoom,
  listChatMessages,
  listChatRooms,
  PortalSession,
  sendChatMessage,
  encryptMessage,
  decryptMessage
} from '../api';
import { Search, Send, MoreHorizontal, Camera, Heart, MessageCircle } from 'lucide-react';

interface ChatProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
}

export const Chat: React.FC<ChatProps> = ({ backendOnline, session }) => {
  const [rooms, setRooms] = useState<any[]>([]);
  const [activeRoomId, setRoomId] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [status, setStatus] = useState('');
  const [showEmoji, setShowEmoji] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const loadRooms = async () => {
    if (!backendOnline || !session) return;
    try {
      const payload = await listChatRooms(session.access_token);
      const roomList = (payload.rooms || []) as any[];
      setRooms(roomList);
      if (roomList.length > 0 && !activeRoomId) {
        setRoomId(roomList[0].room_id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadMessages = async () => {
    if (!backendOnline || !session || !activeRoomId) return;
    try {
      const payload = await listChatMessages(session.access_token, activeRoomId);
      setMessages(payload.messages || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadRooms();
  }, [backendOnline, session]);

  useEffect(() => {
    loadMessages();
    const timer = setInterval(loadMessages, 3000);
    return () => clearInterval(timer);
  }, [activeRoomId]);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const handleSendMessage = async () => {
    if (!message.trim() || !session || !activeRoomId) return;
    try {
      const encryptedBody = await encryptMessage(activeRoomId, message);
      await sendChatMessage(session.access_token, activeRoomId, encryptedBody);
      setMessage('');
      loadMessages();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const decrypt = async (body: string, roomId: string) => {
    return await decryptMessage(roomId, body);
  };

  // We need to handle async decryption in the render or via state
  const [decryptedMessages, setDecryptedMessages] = useState<Record<string, string>>({});

  useEffect(() => {
    const run = async () => {
      const newDecrypted: Record<string, string> = { ...decryptedMessages };
      let changed = false;
      for (const msg of messages) {
        if (!newDecrypted[msg.message_id]) {
          newDecrypted[msg.message_id] = await decryptMessage(activeRoomId, msg.body);
          changed = true;
        }
      }
      if (changed) setDecryptedMessages(newDecrypted);
    };
    run();
  }, [messages, activeRoomId]);

  return (
    <div className="flex h-[calc(100vh-180px)] bg-white dark:bg-background-dark rounded-3xl overflow-hidden glass shadow-2xl border border-primary/10">
      {/* Sidebar: IG Style */}
      <div className="w-1/3 border-r border-primary/5 flex flex-col bg-surface-light/30 dark:bg-surface-dark/30">
        <div className="p-6 pb-2">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-black tracking-tight">Direct</h2>
            <button className="p-2 hover:bg-primary/10 rounded-full transition-all">
              <MoreHorizontal size={20} />
            </button>
          </div>
          
          {/* IG Stories in Sidebar */}
          <div className="flex gap-4 overflow-x-auto no-scrollbar pb-4 mb-2">
            <div className="flex-shrink-0 flex flex-col items-center gap-1">
              <div className="size-14 rounded-full p-0.5 border-2 border-dashed border-primary/50 flex items-center justify-center">
                <div className="size-full rounded-full bg-surface-light dark:bg-surface-dark flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary">add</span>
                </div>
              </div>
              <span className="text-[10px] text-text-subtle">Your Story</span>
            </div>
            {[1,2,3].map(i => (
              <div key={i} className="flex-shrink-0 flex flex-col items-center gap-1">
                <div className="size-14 rounded-full p-0.5 bg-gradient-to-tr from-[#f9ce34] via-[#ee2a7b] to-[#6228d7]">
                  <div className="size-full rounded-full border-2 border-white dark:border-background-dark overflow-hidden">
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=ig-${i}`} alt="avatar" />
                  </div>
                </div>
                <span className="text-[10px] text-text-subtle">user_{i}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto no-scrollbar">
          {rooms.map(room => (
            <button 
              key={room.room_id}
              onClick={() => setRoomId(room.room_id)}
              className={`w-full p-4 flex items-center gap-3 transition-all ${activeRoomId === room.room_id ? 'bg-primary/10 border-r-2 border-primary' : 'hover:bg-primary/5'}`}
            >
              <div className="relative">
                <div className="size-12 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold overflow-hidden">
                  <img src={`https://api.dicebear.com/7.x/initials/svg?seed=${room.name}`} alt={room.name} />
                </div>
                <div className="absolute bottom-0 right-0 size-3 bg-binance-green rounded-full border-2 border-white dark:border-background-dark" />
              </div>
              <div className="flex-1 text-left min-w-0">
                <div className="font-bold text-sm truncate">{room.name}</div>
                <div className="text-[11px] text-text-subtle truncate flex items-center gap-1">
                  <span className="font-medium text-text-main dark:text-white">Active</span>
                  <span>• 2h ago</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white dark:bg-background-dark/20">
        {/* Header */}
        <div className="px-6 py-4 border-b border-primary/5 flex items-center justify-between bg-white/50 dark:bg-background-dark/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold overflow-hidden">
              <img src={`https://api.dicebear.com/7.x/initials/svg?seed=${rooms.find(r => r.room_id === activeRoomId)?.name ?? '?'}`} alt="avatar" />
            </div>
            <div>
              <div className="font-bold text-sm leading-none mb-1">
                {rooms.find(r => r.room_id === activeRoomId)?.name ?? 'Select a room'}
              </div>
              <div className="text-[10px] text-text-subtle flex items-center gap-1">
                <div className="size-1.5 bg-binance-green rounded-full" />
                Active now
              </div>
            </div>
          </div>
          <div className="flex gap-5 text-text-main dark:text-white">
            <button className="hover:text-primary transition-colors"><Camera size={22} /></button>
            <button className="hover:text-primary transition-colors"><Search size={22} /></button>
            <button className="hover:text-primary transition-colors"><MoreHorizontal size={22} /></button>
          </div>
        </div>

        {/* Message Feed */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 flex flex-col gap-4 no-scrollbar bg-gradient-to-b from-transparent to-primary/5">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center opacity-40">
              <div className="size-24 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <MessageCircle size={48} className="text-primary" />
              </div>
              <h3 className="font-bold">No messages yet</h3>
              <p className="text-xs">Send a message to start the conversation</p>
            </div>
          ) : (
            messages.map((msg, i) => {
              const isMe = msg.sender_account_id === session?.account_id;
              return (
                <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'} items-end gap-2 group`}>
                  {!isMe && (
                    <div className="size-7 rounded-full bg-surface-light dark:bg-surface-dark overflow-hidden mb-1 shadow-sm">
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${msg.sender_account_id}`} alt="avatar" />
                    </div>
                  )}
                  <div className="flex flex-col gap-1 max-w-[75%]">
                    <div className={`p-3 rounded-2xl text-sm transition-all hover:scale-[1.02] ${
                      isMe 
                        ? 'bg-primary text-black rounded-br-none shadow-md' 
                        : 'bg-surface-light dark:bg-surface-dark text-text-main dark:text-white rounded-bl-none border border-primary/5'
                    }`}>
                      {decryptedMessages[msg.message_id] || 'Decrypting...'}
                    </div>
                    <div className={`text-[8px] opacity-0 group-hover:opacity-100 transition-opacity ${isMe ? 'text-right' : 'text-left'} text-text-subtle px-1`}>
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Input Area: IG Style */}
        <div className="p-4">
          <div className="bg-surface-light dark:bg-surface-dark/60 rounded-full border border-primary/10 px-4 py-2 flex items-center gap-3 shadow-lg focus-within:border-primary/30 transition-all">
            <button className="size-8 rounded-full bg-primary flex items-center justify-center text-black shrink-0 hover:scale-110 transition-transform">
              <Camera size={18} />
            </button>
            <input 
              className="flex-1 bg-transparent outline-none text-sm py-2"
              placeholder="Message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            {message.trim() ? (
              <button 
                onClick={handleSendMessage} 
                className="text-primary font-bold text-sm px-2 hover:scale-105 transition-all"
              >
                Send
              </button>
            ) : (
              <div className="flex gap-4 text-text-subtle pr-2">
                <button className="hover:text-primary transition-colors"><Heart size={20} /></button>
                <button className="hover:text-primary transition-colors"><Send size={20} /></button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
