// Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
// File Last Update Date : November 25, 2022

import UIKit
import CoreMotion

class ViewController: UIViewController, UITextFieldDelegate {
    @IBOutlet weak var IPTextField: UITextField!
    @IBOutlet weak var rateTextField: UITextField!
    @IBOutlet weak var connectButton: UIButton!
    @IBOutlet weak var stopButton: UIButton!
    @IBOutlet weak var responseLabel: UILabel!
    
    var timer: Timer!
    var labelText = ""
    var gyro_data: [Double] = []
    var accl_data: [Double] = []
    
    let motion = CMMotionManager()
    
    struct motionData: Codable {
        let gyroData: [Double]
        let acclData: [Double]
    }
    
    @IBAction func connectButtonAction(_ sender: Any) {
        let IP = "http://" + IPTextField.text! + "/"
        let rate = Double(rateTextField.text!) ?? 30.0
        
        // Verify that the gyroscopes and accelerometers are available to be used
        if motion.isGyroAvailable && motion.isAccelerometerAvailable {
            motion.gyroUpdateInterval = 1.0 / rate
            motion.accelerometerUpdateInterval = 1.0 / rate
            
            // Start the delivery of rotation and acceleration data
            motion.startGyroUpdates()
            motion.startAccelerometerUpdates()
            
            // Configure a timer to fetch the rotation and acceleration data
            timer = Timer(fire: Date(), interval: (1.0/rate), repeats: true, block: { [self] (timer) in
                // Get the gyroscope data
                if let gyro = motion.gyroData {
                    gyro_data = [gyro.timestamp, gyro.rotationRate.x, gyro.rotationRate.y, gyro.rotationRate.z]
                }
                
                // Get the accelerometer data
                if let accl = motion.accelerometerData {
                    accl_data = [accl.timestamp, accl.acceleration.x, accl.acceleration.y, accl.acceleration.z]
                }
                
                // Preparing JSON data for upload
                let motion_data = motionData(gyroData: gyro_data,
                                             acclData: accl_data)
                
                guard let uploadData = try? JSONEncoder().encode(motion_data) else {
                    return
                }
                
                // Configure an upload request
                let url = URL(string: IP)!
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                
                // Create and start an upload task
                let task = URLSession.shared.uploadTask(with: request, from: uploadData) { data, response, error in
                    if let error = error {
                        print ("error: \(error)")
                        self.labelText = "Could not connect to the server."
                        return
                    }
                    guard let response = response as? HTTPURLResponse,
                        (200...299).contains(response.statusCode) else {
                        print ("server error")
                        self.labelText = "Could not connect to the server."
                        return
                    }
                    if let mimeType = response.mimeType,
                        mimeType == "application/json",
                        let data = data,
                        let dataString = String(data: data, encoding: .utf8) {
                        print ("got data: \(dataString)")
                        self.labelText = "Connected to the server."
                    }
                }
                
                task.resume()
                responseLabel.text = self.labelText
            })
            
            // Add the timer to the current run loop.
            RunLoop.current.add(timer!, forMode: RunLoop.Mode.default)
        }
    }
    
    @IBAction func stopButtonAction(_ sender: Any) {
        if timer != nil {
            timer?.invalidate()
            timer = nil
            
            motion.stopGyroUpdates()
            motion.stopAccelerometerUpdates()
            
            if self.labelText == "Connected to the server." {
                responseLabel.text = "Disconnected from the server."
            }
        }
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        IPTextField.layer.cornerRadius = 15
        rateTextField.layer.cornerRadius = 15
        connectButton.layer.cornerRadius = 15
        stopButton.layer.cornerRadius = 15

        IPTextField.attributedPlaceholder = NSAttributedString(string:"Server IP Address", attributes: [NSAttributedString.Key.foregroundColor : UIColor.lightGray])
        rateTextField.attributedPlaceholder = NSAttributedString(string:"Frequency Rate", attributes: [NSAttributedString.Key.foregroundColor : UIColor.lightGray])
        
        self.IPTextField.delegate = self
        self.rateTextField.delegate = self
    }
    
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        self.view.endEditing(true)
        return false
    }
}
