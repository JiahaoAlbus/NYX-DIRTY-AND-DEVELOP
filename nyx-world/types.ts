export enum Screen {
  ONBOARDING = 'ONBOARDING',
  HOME = 'HOME',
  WALLET = 'WALLET',
  SWAP = 'SWAP',
  CHAT = 'CHAT',
  MARKET = 'MARKET',
  ACTIVITY = 'ACTIVITY'
}

export interface EvidenceRun {
  run_id: string;
  status: string;
}

export interface ChatRoomV1 {
  room_id: string;
  name: string;
  created_at: number;
  is_public: boolean;
}

export interface ChatMessageV1 {
  message_id: string;
  room_id: string;
  sender_account_id: string;
  body: string;
  created_at: number;
}

export interface MarketplaceListing {
  listing_id: string;
  sku: string;
  title: string;
  unit_value: number;
  created_at: number;
}

export interface MarketplacePurchase {
  purchase_id: string;
  listing_id: string;
  qty: number;
  created_at: number;
}

export interface EntertainmentItem {
  item_id: string;
  title: string;
  created_at: number;
}

export interface EntertainmentEvent {
  event_id: string;
  item_id: string;
  mode: string;
  step: number;
  created_at: number;
}
