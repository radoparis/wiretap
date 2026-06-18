import Foundation

/// An audio input device, mirroring the worker's `devices` JSON output.
struct Device: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let inputChannels: Int

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case inputChannels = "input_channels"
    }
}

struct DeviceList: Codable {
    let devices: [Device]
}
