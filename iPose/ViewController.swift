//
//  viewController.swift
//  iPose
//
//  Created by Ghasem Abdi on 2022-06-15.
//

import UIKit
import CoreMotion

class ViewController: UIViewController, UITextFieldDelegate {
    @IBOutlet weak var stopButton: UIButton!
    @IBOutlet weak var responseLabel: UILabel!
    @IBOutlet weak var connectButton: UIButton!
    @IBOutlet weak var IPTextField: UITextField!
    @IBOutlet weak var rateTextField: UITextField!
    
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        self.view.endEditing(true)
        return false
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        stopButton.layer.cornerRadius = 15
        IPTextField.layer.cornerRadius = 15
        rateTextField.layer.cornerRadius = 15
        connectButton.layer.cornerRadius = 15
        
        IPTextField.attributedPlaceholder = NSAttributedString(string:"Server IP Address", attributes: [NSAttributedString.Key.foregroundColor : UIColor.lightGray])
        rateTextField.attributedPlaceholder = NSAttributedString(string:"Frequency Rate", attributes: [NSAttributedString.Key.foregroundColor : UIColor.lightGray])
        
        self.IPTextField.delegate = self
        self.rateTextField.delegate = self
    }
    
    var timer: Timer!
    var responseLabelText = ""
    let motion = CMMotionManager()
    
    @IBAction func connectButtonAction(_ sender: Any) {
        let IP = "http://" + IPTextField.text! + "/"
        let rate = Double(rateTextField.text!) ?? 30.0
        
        // Verify that the gyroscopes and accelerometers are available
        if motion.isGyroAvailable && motion.isAccelerometerAvailable {
            motion.gyroUpdateInterval = 1.0 / rate
            motion.accelerometerUpdateInterval = 1.0 / rate
            
            // Start the delivery of rotation and acceleration
            motion.startGyroUpdates()
            motion.startAccelerometerUpdates()
            
            // Configure a timer to fetch the rotation and acceleration data
            timer = Timer(fire: Date(), interval: (1.0/rate), repeats: true, block: { [self] (timer) in
                let messageData = NSMutableData()
                
                // Get the gyroscope data
                messageData.append("gyro".data(using: .ascii)!)
                if let gyro = motion.gyroData {
                    messageData.append(withUnsafeBytes(of: gyro.rotationRate.x) { Data($0) })
                    messageData.append(withUnsafeBytes(of: gyro.rotationRate.y) { Data($0) })
                    messageData.append(withUnsafeBytes(of: gyro.rotationRate.z) { Data($0) })
                }

                // Get the accelerometer data
                messageData.append("accl".data(using: .ascii)!)
                if let accl = motion.accelerometerData {
                    messageData.append(withUnsafeBytes(of: accl.acceleration.x) { Data($0) })
                    messageData.append(withUnsafeBytes(of: accl.acceleration.y) { Data($0) })
                    messageData.append(withUnsafeBytes(of: accl.acceleration.z) { Data($0) })
                }
                
                // Compress the message data
                let compressedMessageData = (try? messageData.compressed(using: .lzfse))!

                // Configure an upload request
                let url = URL(string: IP)!
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.httpBody = compressedMessageData as Data
                
                // Create and start a data task
                let task = URLSession.shared.dataTask(with: request) { [self] data, response, error in
                    if let error = error {
                        print ("Server Error: \(error)")
                        self.responseLabelText = "RYANotics: Server Error ..."
                        return
                    }
                    guard let httpResponse = response as? HTTPURLResponse, (200...299).contains(httpResponse.statusCode) else {
                        print ("Server Error: ...")
                        self.responseLabelText = "RYANotics: Server Error ..."
                        return
                    }
                    if let mimeType = httpResponse.mimeType, mimeType == "text/html" {
                        print("Sent Message ...")
                        self.responseLabelText = "RYANotics: Connected to the Server ..."
                    }
                }
                task.resume()
                responseLabel.text = self.responseLabelText
            })
            
            // Add the timer to the current run loop.
            RunLoop.current.add(timer!, forMode: RunLoop.Mode.default)
        }
        else {
            responseLabel.text = "RYANotics: Unsupported Device ..."
        }
    }
    
    @IBAction func stopButtonAction(_ sender: Any) {
        if timer != nil {
            timer?.invalidate()
            timer = nil
            
            // Stop the delivery of rotation and acceleration
            motion.stopGyroUpdates()
            motion.stopAccelerometerUpdates()
            
            if responseLabel.text == "RYANotics: Connected to the Server ..." {
                responseLabel.text = "RYANotics: Disconnected from the Server ..."
            }
        }
    }
}
