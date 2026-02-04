export enum Screen {
  ONBOARDING = 'ONBOARDING',
  HOME = 'HOME',
  WALLET = 'WALLET',
  EXCHANGE = 'EXCHANGE',
  CHAT = 'CHAT',
  STORE = 'STORE',
  ACTIVITY = 'ACTIVITY',
  EVIDENCE = 'EVIDENCE',
  SETTINGS = 'SETTINGS',
  DAPP_BROWSER = 'DAPP_BROWSER',
  AIRDROP = 'AIRDROP',
  FAUCET = 'FAUCET',
  FIAT = 'FIAT',
  WEB2_ACCESS = 'WEB2_ACCESS'
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

export interface Web2AllowlistEntry {
  id: string;
  label: string;
  base_url: string;
  path_prefix: string;
  methods: string[];
}

export interface Web2GuardRequestRow {
  request_id: string;
  account_id: string;
  run_id: string;
  url: string;
  method: string;
  request_hash: string;
  response_hash: string;
  response_status: number;
  response_size: number;
  response_truncated: boolean;
  body_size: number;
  header_names: string[];
  sealed_request_present?: boolean;
  created_at: number;
}

export interface Web2GuardResponse {
  run_id: string;
  state_hash: string;
  receipt_hashes: string[];
  replay_ok: boolean;
  request_id: string;
  request_hash: string;
  response_hash: string;
  response_status: number;
  response_size: number;
  response_truncated: boolean;
  body_size: number;
  upstream_ok: boolean;
  upstream_error?: string | null;
  response_preview?: string;
  fee_total: number;
  fee_breakdown?: {
    protocol_fee_total: number;
    platform_fee_amount: number;
  };
  treasury_address?: string;
  from_balance?: number;
  treasury_balance?: number;
}
