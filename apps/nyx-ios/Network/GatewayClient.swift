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

    init(baseURL: URL = URL(string: "http://localhost:8090")!) {
        self.baseURL = baseURL
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

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw GatewayError(message: "invalid response")
        }
        if httpResponse.statusCode >= 400 {
            let errorText = String(data: data, encoding: .utf8) ?? "run failed"
            throw GatewayError(message: errorText)
        }
        return try JSONDecoder().decode(RunResponse.self, from: data)
    }

    func fetchEvidence(runId: String) async throws -> EvidenceBundle {
        var components = URLComponents(url: baseURL.appendingPathComponent("evidence"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "run_id", value: runId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw GatewayError(message: "invalid response")
        }
        if httpResponse.statusCode >= 400 {
            let errorText = String(data: data, encoding: .utf8) ?? "evidence failed"
            throw GatewayError(message: errorText)
        }
        return try JSONDecoder().decode(EvidenceBundle.self, from: data)
    }

    func fetchExportZip(runId: String) async throws -> Data {
        var components = URLComponents(url: baseURL.appendingPathComponent("export.zip"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "run_id", value: runId)]
        guard let url = components?.url else {
            throw GatewayError(message: "invalid url")
        }
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw GatewayError(message: "invalid response")
        }
        if httpResponse.statusCode >= 400 {
            let errorText = String(data: data, encoding: .utf8) ?? "export failed"
            throw GatewayError(message: errorText)
        }
        return data
    }
}
