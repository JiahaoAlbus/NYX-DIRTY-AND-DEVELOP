export function encodeUtf8(value: string): Uint8Array {
  return new TextEncoder().encode(value);
}

export function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((b) => {
    binary += String.fromCharCode(b);
  });
  return btoa(binary);
}

export function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
