import Foundation

struct RunResponse: Codable {
    let runId: String
    let status: String
    let replayOk: Bool?

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status
        case replayOk = "replay_ok"
    }
}

struct GatewayError: Error {
    let message: String
}

final class GatewayClient {
    private let baseURL: URL
    private let maxRetries = 1
    private var evidenceCache: [String: EvidenceBundle] = [:]

    init(baseURL: URL = URL(string: "http://localhost:8091")!) {
        self.baseURL = baseURL
    }

    private func requestData(_ request: URLRequest) async throws -> Data {
        var attempts = 0
        var lastError: Error?
        while attempts <= maxRetries {
            do {
                let (data, response) = try await URLSession.shared.data(for: request)
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw GatewayError(message: "invalid response")
                }
                if httpResponse.statusCode >= 400 {
                    let errorText = String(data: data, encoding: .utf8) ?? "request failed"
                    throw GatewayError(message: errorText)
                }
                return data
            } catch {
                lastError = error
                attempts += 1
            }
        }
        throw lastError ?? GatewayError(message: "request failed")
    }

    func run(seed: Int, runId: String, module: String, action: String, payload: [String: Any]) async throws -> RunResponse {
        let url = baseURL.appendingPathComponent("run")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "seed": seed,
            "run_id": runId,
            "module": module,
            "action": action,
            "payload": payload,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])

        let data = try await requestData(request)
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func fetchEvidence(runId: String) async throws -> EvidenceBundle {
        if let cached = evidenceCache[runId] {
            return cached
        }
        var components = URLComponents(url: baseURL.appendingPathComponent("evidence"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "run_id", value: runId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        let data = try await requestData(request)
        let bundle = try JSONDecoder().decode(EvidenceBundle.self, from: data)
        evidenceCache[runId] = bundle
        return bundle
    }

    func fetchExportZip(runId: String) async throws -> Data {
        var components = URLComponents(url: baseURL.appendingPathComponent("export.zip"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "run_id", value: runId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let request = URLRequest(url: url)
        return try await requestData(request)
    }
}
