// Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
// File Last Update Date : November 24, 2022

import UIKit
import CoreMotion

class ViewController: UIViewController {
    
    var timer: Timer!
    var gyro_data: [Double] = []
    var accl_data: [Double] = []
    
    let motion = CMMotionManager()
    
    struct motionData: Codable {
        let gyroData: [Double]
        let acclData: [Double]
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        startMotion()
        
        func startMotion() {
            
            // Verify that the gyroscopes and accelerometers are available to be used
            if self.motion.isGyroAvailable && self.motion.isAccelerometerAvailable {
                
                // Specify an update frequency
                self.motion.gyroUpdateInterval = 1.0 / 30.0
                self.motion.accelerometerUpdateInterval = 1.0 / 30.0
                
                // Start the delivery of rotation and acceleration data
                self.motion.startGyroUpdates()
                self.motion.startAccelerometerUpdates()
                
                // Configure a timer to fetch the rotation and acceleration data
                self.timer = Timer(fire: Date(), interval: (1.0/30.0), repeats: true, block: { [self] (timer) in
                    
                    // Get the gyroscope data
                    if let gyro = self.motion.gyroData {
                        self.gyro_data = [gyro.timestamp, gyro.rotationRate.x, gyro.rotationRate.y, gyro.rotationRate.z]
                    }
                    
                    // Get the accelerometer data
                    if let accl = self.motion.accelerometerData {
                        self.accl_data = [accl.timestamp, accl.acceleration.x, accl.acceleration.y, accl.acceleration.z]
                    }
                    
                    // Preparing JSON data for upload
                    let motion_data = motionData(gyroData: self.gyro_data,
                                                 acclData: self.accl_data)
                    
                    guard let uploadData = try? JSONEncoder().encode(motion_data) else {
                        return
                    }
                    
                    // Configure an upload request
                    let url = URL(string: "http://192.168.2.10:5000/")!
                    var request = URLRequest(url: url)
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    
                    // Create and start an upload task
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
                            print ("got data: \(dataString)")
                        }
                    }
                    task.resume()
                })
                
                // Add the timer to the current run loop.
                RunLoop.current.add(self.timer!, forMode: RunLoop.Mode.default)
            }
        }
        
        func stopMotion() {
            if self.timer != nil {
                self.timer?.invalidate()
                self.timer = nil
                
                self.motion.stopGyroUpdates()
                self.motion.stopAccelerometerUpdates()
            }
        }
    }
}
