// Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
// File Last Update Date : June 25, 2022
// TODO:
// SWIFT UI accepts interval and base address
// SWIFT UI accepts start and stop buttons

// Import dependencies
import UIKit
import CoreMotion
import CoreLocation

class ViewController: UIViewController, CLLocationManagerDelegate {
    
    // Set destination and measuring rate
    let interval = 1.0 / 30.0
    let dest = "http://192.168.1.23:5000/"
    
    // Initiate iSensors variable
    var rawGyro = String()
    var rawAccl = String()
    var rawMagn = String()

    var processedGyro = String()
    var processedAccl = String()
    var processedMagn = String()

    var attitude = String()
    var quaternion = String()
    var gravityField = String()

    var location = String()
    
    // Define motion/location manager
    let motionManager = CMMotionManager()
    let locationManager = CLLocationManager()
    
    // Define the data stream struct
    struct Order: Codable {
        let rawGyro: String
        let rawAccl: String
        let rawMagn: String
            
        let processedGyro: String
        let processedAccl: String
        let processedMagn: String
            
        let attitude: String
        let quaternion: String
        let gravityField: String
        
        let location: String
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        start_iSensors()
        
        // Define a custom function to collect and upload data
        func start_iSensors() {
            
            // Set the interval for iSensors
            self.motionManager.gyroUpdateInterval = interval
            self.motionManager.accelerometerUpdateInterval = interval
            self.motionManager.magnetometerUpdateInterval = interval
            self.motionManager.deviceMotionUpdateInterval = interval
           
            // Start collecting iSensors
            self.motionManager.startGyroUpdates()
            self.motionManager.startAccelerometerUpdates()
            self.motionManager.startMagnetometerUpdates()
            self.motionManager.startDeviceMotionUpdates(using: CMAttitudeReferenceFrame.xTrueNorthZVertical)
            
            // Ask a location authorization and start collecting iLocation
            self.locationManager.requestWhenInUseAuthorization()
            self.locationManager.startUpdatingLocation()

            // Configure a timer to fetch the data
            Timer.scheduledTimer(withTimeInterval: interval, repeats: true) {_ in
                
                // Get raw gyroscope data
                if let gyro = self.motionManager.gyroData {
                    self.rawGyro = arr2str(data: [gyro.timestamp, gyro.rotationRate.x, gyro.rotationRate.y, gyro.rotationRate.z])
                }
                
                // Get raw accelerometer data
                if let accl = self.motionManager.accelerometerData {
                    self.rawAccl = arr2str(data: [accl.timestamp, accl.acceleration.x, accl.acceleration.y, accl.acceleration.z])
                }

                // Get raw magnetometer data
                if let magn = self.motionManager.magnetometerData {
                    self.rawMagn = arr2str(data: [magn.timestamp, magn.magneticField.x, magn.magneticField.y, magn.magneticField.z])
                }

                // Get processed motion data
                if let motion_data = self.motionManager.deviceMotion {
                    
                    // Get processed gyroscope data
                    self.processedGyro = arr2str(data: [motion_data.timestamp, motion_data.rotationRate.x, motion_data.rotationRate.y, motion_data.rotationRate.z])

                    // Get processed accelerometer data
                    self.processedAccl = arr2str(data: [motion_data.timestamp, motion_data.userAcceleration.x, motion_data.userAcceleration.y, motion_data.userAcceleration.z])

                    // Get processed magnetometer data
                    self.processedMagn = arr2str(data: [motion_data.timestamp, motion_data.magneticField.field.x, motion_data.magneticField.field.y, motion_data.magneticField.field.z])

                    // Get processed attitude data
                    self.attitude = arr2str(data: [motion_data.timestamp, motion_data.attitude.roll, motion_data.attitude.pitch, motion_data.attitude.yaw])
                    
                    // Get processed quaternion data
                    self.quaternion = arr2str(data: [motion_data.timestamp, motion_data.attitude.quaternion.x, motion_data.attitude.quaternion.y, motion_data.attitude.quaternion.z, motion_data.attitude.quaternion.w])

                    // Get processed gravity data
                    self.gravityField = arr2str(data: [motion_data.timestamp, motion_data.gravity.x, motion_data.gravity.y, motion_data.gravity.z])
                }

                // Get processed location data (1 Hz)
                if let loc = self.locationManager.location {
                    self.location = arr2str(data: [loc.timestamp.timeIntervalSince1970, loc.coordinate.latitude, loc.coordinate.longitude, loc.altitude, loc.horizontalAccuracy, loc.verticalAccuracy])
                }
                
                let order = Order(
                    rawGyro: self.rawGyro,
                    rawAccl: self.rawAccl,
                    rawMagn: self.rawMagn,
                    processedGyro: self.processedGyro,
                    processedAccl: self.processedAccl,
                    processedMagn: self.processedMagn,
                    attitude: self.attitude,
                    quaternion: self.quaternion,
                    gravityField: self.gravityField,
                    location: self.location
                )
                                
                // Upload iSensors to destination
                POST_iSensors(dest: self.dest, order: order)
            }
            
            // Define a custom function to convert array to string
            func arr2str(data: [Double]) -> String {
                guard let encode_data = try? JSONEncoder().encode(data) else {
                    return ""
                }
                return String(data: encode_data, encoding: .utf8)!
            }
            
            // Define a custom function to make a POST request
            func POST_iSensors(dest: String, order: Order) {
                
                // Prepare JSON data for upload
                guard let uploadData = try? JSONEncoder().encode(order) else {
                    return
                }
                
                // Configure a URL request
                let url = URL(string: dest)!
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                
                // Start upload task
                let task = URLSession.shared.uploadTask(with: request, from: uploadData) { data, response, error in
                    if let error = error {
                        print ("error: \(error)")
                        return
                    }

                    guard let response = response as? HTTPURLResponse,
                          (200...299).contains(response.statusCode) else {
                        print ("server error")
                        return
                    }

                    if let mimeType = response.mimeType,
                       mimeType == "application/json",
                       let data = data,
                       let dataString = String(data: data, encoding: .utf8) {
                        print ("uploaded: \(dataString)")
                    }
                }
                task.resume()
            }
        }
    }
}
