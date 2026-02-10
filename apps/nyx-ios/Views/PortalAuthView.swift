import SwiftUI

struct PortalAuthView: View {
    @ObservedObject var settings: BackendSettings
    @State private var handle: String = ""
    @State private var existingAccountId: String = ""
    @State private var status: String = ""
    @State private var busy: Bool = false

    private let client = GatewayClient()

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("NYX Testnet Sign In")
                        .font(.largeTitle)
                        .fontWeight(.black)
                    Text("No Web2 tasks. No fake buttons. Every mutation produces receipts.")
                        .font(.footnote)
                        .foregroundColor(.secondary)
                }

                Group {
                    Text("Backend URL")
                        .font(.headline)
                    TextField("http://127.0.0.1:8091", text: $settings.baseURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled(true)
                        .padding(10)
                        .background(RoundedRectangle(cornerRadius: 12).stroke(.secondary))
                }

                Divider()

                Group {
                    Text("Create Account")
                        .font(.headline)
                    TextField("handle (lowercase)", text: $handle)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled(true)
                        .padding(10)
                        .background(RoundedRectangle(cornerRadius: 12).stroke(.secondary))
                    Button {
                        Task { await createAndSignIn() }
                    } label: {
                        Text(busy ? "Working…" : "Create + Sign In")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(busy || handle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }

                Group {
                    Text("Restore (Optional)")
                        .font(.headline)
                    TextField("account_id", text: $existingAccountId)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled(true)
                        .padding(10)
                        .background(RoundedRectangle(cornerRadius: 12).stroke(.secondary))
                    Button {
                        Task { await signInExisting() }
                    } label: {
                        Text(busy ? "Working…" : "Sign In Existing")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .disabled(busy || existingAccountId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }

                if !status.isEmpty {
                    Text(status)
                        .font(.footnote)
                        .foregroundColor(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }

                Spacer()
            }
            .padding()
            .navigationTitle("Sign In")
        }
    }

    @MainActor
    private func createAndSignIn() async {
        guard let baseURL = settings.resolvedURL() else {
            status = "Invalid backend URL"
            return
        }
        let handleTrimmed = handle.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !handleTrimmed.isEmpty else {
            status = "Handle required"
            return
        }
        busy = true
        status = "Creating account…"
        client.setBaseURL(baseURL)
        do {
            let pubkey = PortalKeyStore.shared.publicKeyBase64()
            let account = try await client.createPortalAccount(handle: handleTrimmed, pubkey: pubkey)
            status = "Issuing challenge…"
            let challenge = try await client.requestPortalChallenge(accountId: account.accountId)
            let signature = PortalKeyStore.shared.sign(nonce: challenge.nonce)
            status = "Verifying…"
            let token = try await client.verifyPortalChallenge(accountId: account.accountId, nonce: challenge.nonce, signature: signature)
            status = "Fetching profile…"
            let me = try await client.fetchPortalMe(token: token.accessToken)
            settings.save()
            settings.saveSession(
                PortalSession(
                    account_id: me.accountId,
                    handle: me.handle,
                    pubkey: me.pubkey,
                    access_token: token.accessToken,
                    wallet_address: me.walletAddress
                )
            )
        } catch {
            status = "Sign in failed: \(String(describing: error))"
        }
        busy = false
    }

    @MainActor
    private func signInExisting() async {
        guard let baseURL = settings.resolvedURL() else {
            status = "Invalid backend URL"
            return
        }
        let accountId = existingAccountId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !accountId.isEmpty else {
            status = "account_id required"
            return
        }
        busy = true
        status = "Issuing challenge…"
        client.setBaseURL(baseURL)
        do {
            let challenge = try await client.requestPortalChallenge(accountId: accountId)
            let signature = PortalKeyStore.shared.sign(nonce: challenge.nonce)
            status = "Verifying…"
            let token = try await client.verifyPortalChallenge(accountId: accountId, nonce: challenge.nonce, signature: signature)
            status = "Fetching profile…"
            let me = try await client.fetchPortalMe(token: token.accessToken)
            settings.save()
            settings.saveSession(
                PortalSession(
                    account_id: me.accountId,
                    handle: me.handle,
                    pubkey: me.pubkey,
                    access_token: token.accessToken,
                    wallet_address: me.walletAddress
                )
            )
        } catch {
            status = "Sign in failed: \(String(describing: error))"
        }
        busy = false
    }
}
