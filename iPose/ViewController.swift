//
//  viewController.swift
//  iPose
//
//  Created by Ghasem Abdi on 2022-06-15.
//

import UIKit
import ARKit
import CoreMotion
import Accelerate.vImage

class ViewController: UIViewController, UITextFieldDelegate {
    var timer: Timer!
    var responseLabelText = ""
    let arReceiver = ARReceiver()
    let motion = CMMotionManager()
    var infoYpCbCrToARGB = vImage_YpCbCrToARGB()
    
    @IBOutlet weak var stopButton: UIButton!
    @IBOutlet weak var responseLabel: UILabel!
    @IBOutlet weak var connectButton: UIButton!
    @IBOutlet weak var IPTextField: UITextField!
    @IBOutlet weak var rateTextField: UITextField!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        stopButton.layer.cornerRadius = 15
        IPTextField.layer.cornerRadius = 15
        rateTextField.layer.cornerRadius = 15
        connectButton.layer.cornerRadius = 15
        
        self.IPTextField.delegate = self
        self.rateTextField.delegate = self
        
        IPTextField.attributedPlaceholder = NSAttributedString(string:"Server IP Address", attributes: [NSAttributedString.Key.foregroundColor : UIColor.lightGray])
        rateTextField.attributedPlaceholder = NSAttributedString(string:"Frequency Rate", attributes: [NSAttributedString.Key.foregroundColor : UIColor.lightGray])
        
        guard configureYpCbCrToARGBInfo() == kvImageNoError else {
            return
        }
    }
    
    @IBAction func connectButtonAction(_ sender: Any) {
        let IP = "http://" + IPTextField.text! + "/"
        let rate = Double(rateTextField.text!) ?? 30.0
        
        // Verify that the gyroscopes, accelerometers, and LiDAR are available
        if motion.isGyroAvailable && motion.isAccelerometerAvailable && ARWorldTrackingConfiguration.supportsFrameSemantics([.sceneDepth, .smoothedSceneDepth]) {
            motion.gyroUpdateInterval = 1.0 / rate
            motion.accelerometerUpdateInterval = 1.0 / rate
            
            // Start the delivery of rotation, acceleration, LiDAR data
            arReceiver.start()
            motion.startGyroUpdates()
            motion.startAccelerometerUpdates()
            
            // Configure a timer to fetch the rotation and acceleration data
            timer = Timer(fire: Date(), interval: (1.0 / rate), repeats: true, block: { [self] (timer) in
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
                
                // Get the LiDAR data
                messageData.append("dpth".data(using: .ascii)!)
                if let depth = arReceiver.arData.depthImage {
                    messageData.append(createDataFromDepthCVPixelBuffer(pixelBuffer: depth))
                }
                
                // Get the visual data
                messageData.append("visl".data(using: .ascii)!)
                if let image = arReceiver.arData.colorImage {
                    messageData.append(createDataFromImageCVPixelBuffer(pixelBuffer: image))
                }
                
                // Get the camera interior orientation parameters and scale them based on "Convert YpCbCr to ARGB"
                messageData.append("camp".data(using: .ascii)!)
                let camp = arReceiver.arData.cameraIntrinsics
                messageData.append(withUnsafeBytes(of: camp[0][0] / 7.5) { Data($0) })
                messageData.append(withUnsafeBytes(of: camp[1][1] / 7.5) { Data($0) })
                messageData.append(withUnsafeBytes(of: camp[2][0] / 7.5) { Data($0) })
                messageData.append(withUnsafeBytes(of: camp[2][1] / 7.5) { Data($0) })
                
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
            arReceiver.pause()
            motion.stopGyroUpdates()
            motion.stopAccelerometerUpdates()
            
            if responseLabel.text == "RYANotics: Connected to the Server ..." {
                responseLabel.text = "RYANotics: Disconnected from the Server ..."
            }
            
            // Configure a shut down request for the server
            let IP = "http://" + IPTextField.text! + "/shutdown"
            let url = URL(string: IP)!
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            
            let task = URLSession.shared.dataTask(with: request)
            task.resume()
        }
    }
    
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        self.view.endEditing(true)
        return false
    }
    
    func configureYpCbCrToARGBInfo() -> vImage_Error {
        // A utility function that configures YpCbCr to ARGB info, adopted from https://developer.apple.com/documentation/accelerate/converting_luminance_and_chrominance_planes_to_an_argb_image
        
        var pixelRange = vImage_YpCbCrPixelRange(Yp_bias: 16, CbCr_bias: 128, YpRangeMax: 235, CbCrRangeMax: 240, YpMax: 235, YpMin: 16, CbCrMax: 240, CbCrMin: 16)
        
        let error = vImageConvert_YpCbCrToARGB_GenerateConversion(kvImage_YpCbCrToARGBMatrix_ITU_R_601_4!, &pixelRange, &infoYpCbCrToARGB, kvImage422CbYpCrYp8, kvImageARGB8888, vImage_Flags(kvImageNoFlags))
        
        return error
    }
    
    func createDataFromDepthCVPixelBuffer(pixelBuffer: CVPixelBuffer) -> Data {
        // A utility function that creates Data from Depth CVPixelBuffer, adopted from https://github.com/StuckiSimon/ar-streaming/blob/2d37f5afc6d6d626fb4caa460408f3eeadb77c68/ios-streaming-app/ios-streaming-app/Services/WebRTCClient.swift
        
        CVPixelBufferLockBaseAddress(pixelBuffer, [.readOnly])
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, [.readOnly]) }

        let source = CVPixelBufferGetBaseAddress(pixelBuffer)
        let totalSize = CVPixelBufferGetDataSize(pixelBuffer)
        guard let rawFrame = malloc(totalSize) else {fatalError("failed to alloc " + String(totalSize))}
        memcpy(rawFrame, source, totalSize)

        return Data(bytesNoCopy: rawFrame, count: totalSize, deallocator: .free)
    }

    func createDataFromImageCVPixelBuffer(pixelBuffer: CVPixelBuffer) -> Data {
        // A utility function that creates Data from Image CVPixelBuffer
        
        CVPixelBufferLockBaseAddress(pixelBuffer, [.readOnly])
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, [.readOnly]) }
        
        // Luma buffer
        let lumaWidth = CVPixelBufferGetWidthOfPlane(pixelBuffer, 0)
        let lumaHeight = CVPixelBufferGetHeightOfPlane(pixelBuffer, 0)
        let lumaRowBytes = CVPixelBufferGetBytesPerRowOfPlane(pixelBuffer, 0)
        let lumaBaseAddress = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 0)
        var sourceLumaBuffer = vImage_Buffer(data: lumaBaseAddress, height: vImagePixelCount(lumaHeight), width: vImagePixelCount(lumaWidth), rowBytes: lumaRowBytes)
        
        // Chroma buffer
        let chromaWidth = CVPixelBufferGetWidthOfPlane(pixelBuffer, 1)
        let chromaHeight = CVPixelBufferGetHeightOfPlane(pixelBuffer, 1)
        let chromaRowBytes = CVPixelBufferGetBytesPerRowOfPlane(pixelBuffer, 1)
        let chromaBaseAddress = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 1)
        var sourceChromaBuffer = vImage_Buffer(data: chromaBaseAddress, height: vImagePixelCount(chromaHeight), width: vImagePixelCount(chromaWidth), rowBytes: chromaRowBytes)
        
        // Convert YpCbCr to ARGB
        var argbBuffer = try! vImage_Buffer(width: Int(sourceLumaBuffer.width), height: Int(sourceLumaBuffer.height), bitsPerPixel: 8 * 4)
        vImageConvert_420Yp8_CbCr8ToARGB8888(&sourceLumaBuffer, &sourceChromaBuffer, &argbBuffer, &infoYpCbCrToARGB, nil, 255, vImage_Flags(kvImagePrintDiagnosticsToConsole))
        
        // Scale ARGB
        var argbBufferScaled = try! vImage_Buffer(width: Int(Double(sourceLumaBuffer.width) / 7.5), height: Int(Double(sourceLumaBuffer.height) / 7.5), bitsPerPixel: 8 * 4)
        vImageScale_ARGB8888(&argbBuffer, &argbBufferScaled, nil, vImage_Flags(kvImagePrintDiagnosticsToConsole))
        
        // Convert ARGB to RGB
        var rgbBuffer = try! vImage_Buffer(width: Int(argbBufferScaled.width), height: Int(argbBufferScaled.height), bitsPerPixel: 8 * 3)
        vImageConvert_ARGB8888toRGB888(&argbBufferScaled, &rgbBuffer, vImage_Flags(kvImagePrintDiagnosticsToConsole))
        
        // Convert vImage_Buffer to Data
        let totalSize = Int(rgbBuffer.height) * Int(rgbBuffer.rowBytes)
        guard let rawFrame = malloc(totalSize) else {fatalError("failed to alloc " + String(totalSize))}
        memcpy(rawFrame, rgbBuffer.data, totalSize)
        let visualData = Data(bytesNoCopy: rawFrame, count: totalSize, deallocator: .free)
        
        // Free vImage_buffer
        rgbBuffer.free()
        argbBuffer.free()
        argbBufferScaled.free()
        
        return visualData
    }
}
