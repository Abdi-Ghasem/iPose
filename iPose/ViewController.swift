//
//  ViewController.swift
//  iPose
//
//  Created by Ghasem Abdi on 2022-06-15.
//

import UIKit
import CoreMotion
import CoreLocation

class ViewController: UIViewController, CLLocationManagerDelegate {
    
    let interval = 1.0 / 30.0 // 10 Hz
    let motion = CMMotionManager()
    let location = CLLocationManager()

    override func viewDidLoad() {
        super.viewDidLoad()
        start_iSensors()

        func start_iSensors() {
            self.motion.gyroUpdateInterval = interval
            self.motion.accelerometerUpdateInterval = interval
            self.motion.magnetometerUpdateInterval = interval
            self.motion.deviceMotionUpdateInterval = interval
           
            self.motion.startGyroUpdates()
            self.motion.startAccelerometerUpdates()
            self.motion.startMagnetometerUpdates()
            self.motion.startDeviceMotionUpdates()
            
            self.location.requestWhenInUseAuthorization()
            self.location.startUpdatingLocation()

            // Configure a timer to fetch the data.
            var i = 0
            Timer.scheduledTimer(withTimeInterval: interval, repeats: true) {_ in
                // Get raw gyroscope data.
                if let gyro = self.motion.gyroData {
                    let r_x = gyro.rotationRate.x
                    let r_y = gyro.rotationRate.y
                    let r_z = gyro.rotationRate.z
                    print("raw gyroscope data:   \(r_x)   \(r_y)  \(r_z)")
                }

                // Get raw accelerometer data.
                if let acc = self.motion.accelerometerData {
                    let a_x = acc.acceleration.x
                    let a_y = acc.acceleration.y
                    let a_z = acc.acceleration.z
                    print("raw accelerometer data:   \(a_x)   \(a_y)  \(a_z)")
                }
                
                // Get raw magnetometer data.
                if let mgt = self.motion.magnetometerData {
                    let m_x = mgt.magneticField.x
                    let m_y = mgt.magneticField.y
                    let m_z = mgt.magneticField.z
                    print("raw magnetometer data:    \(m_x)   \(m_y)  \(m_z)")
                }
                
                // Get processed motion data.
                if let motion_data = self.motion.deviceMotion {
                    // Get processed gyroscope data.
                    let p_r_x = motion_data.rotationRate.x
                    let p_r_y = motion_data.rotationRate.y
                    let p_r_z = motion_data.rotationRate.z
                    print("processed gyroscope data:   \(p_r_x)   \(p_r_y)  \(p_r_z)")
                    
                    // Get processed accelerometer data.
                    let p_a_x = motion_data.userAcceleration.x
                    let p_a_y = motion_data.userAcceleration.y
                    let p_a_z = motion_data.userAcceleration.z
                    print("processed accelerometer data:   \(p_a_x)   \(p_a_y)  \(p_a_z)")
                    
                    // Get processed magnetometer data.
                    let p_m_x = motion_data.magneticField.field.x
                    let p_m_y = motion_data.magneticField.field.y
                    let p_m_z = motion_data.magneticField.field.z
                    print("processed magnetometer data:    \(p_m_x)   \(p_m_y)  \(p_m_z)")
                    
                    // Get processed attitude data.
                    let roll = motion_data.attitude.roll
                    let pitch = motion_data.attitude.pitch
                    let yaw = motion_data.attitude.yaw
                    print("processed attitude data:   \(roll)  \(pitch)  \(yaw)")
                    
                    // Get processed gravity data.
                    let g_x = motion_data.gravity.x
                    let g_y = motion_data.gravity.y
                    let g_z = motion_data.gravity.z
                    print("processed gravity data:   \(g_x)  \(g_y)  \(g_z)")
                }
                
                // Get processed location data (1 Hz).
                if i % Int(1.0 / self.interval) == 0 {
                    if let xyz = self.location.location {
                        let ts = xyz.timestamp.timeIntervalSince1970
                        let lat = xyz.coordinate.latitude
                        let long = xyz.coordinate.longitude
                        let alt = xyz.altitude
                        let h_acc = xyz.horizontalAccuracy
                        let v_acc = xyz.verticalAccuracy
                        print("processed location data: \(ts)   \(lat)  \(long) \(alt)  \(h_acc)  \(v_acc)")
                    }
                }
                
                i += 1
            }
        }
    }
}
