# !/usr/bin/env python3
# to start the program; open the terminal and type: sudo python3 [file name]
# to stop the program type at the terminal [ctrl] and [c] simultaneously
# the indentation blocks are 4, 8 or 12 spaces, do not use tabs

import RPi.GPIO as GPIO; import time; GPIO.setwarnings(False)
time.sleep(7) # time to put the MER on the ground
# constants used for driving logic
line_of_sight = 45; turn_delay = 1

# duty cycle values for the pulse width modulation of the servo. Default min.2 max.12 
# check these values to make sure the servo properly rotates 40 degrees each side
min_duty = 2; max_duty = 11

class Robot:
    # define all pins as used on the raspberry pi board
    servo_pin = 21; motor_left = 6; motor_right = 12; echo_pin = 19; trig_pin = 16

    # initial setup of the robot
    def __init__(self):
        # set up the pin layout
        GPIO.setmode(GPIO.BCM)

        # set up the pins for output and input
        GPIO.setup(self.motor_left, GPIO.OUT); GPIO.setup(self.motor_right, GPIO.OUT)
        GPIO.setup(self.trig_pin, GPIO.OUT); GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        
        # start pulse width modulation for servo and motors
        self.pwm_servo = GPIO.PWM(self.servo_pin, 50)
        self.pwm_left = GPIO.PWM(self.motor_left, 1000)
        self.pwm_right = GPIO.PWM(self.motor_right, 1000) 

        # default values: servo straight ahead, motors not moving, us sensor inactive
        self.pwm_servo.start(7); self.pwm_left.start(0); self.pwm_right.start(0)
        GPIO.output(self.trig_pin, GPIO.LOW)

    # cleanup of the robot
    def __del__(self):
        # stop the servo
        self.pwm_servo.stop()

        # stop the motors
        self.motor_speed(0,0); self.pwm_left.stop(); self.pwm_right.stop()

    # set the motor speed of the left and right wheels to a value between 0% and 100%
    def motor_speed(self, left, right):
        # set the left engine
        self.pwm_left.ChangeDutyCycle(left)

        # set the right engine
        self.pwm_right.ChangeDutyCycle(right)

    # turn the servo to an angle between -90 and +90 degrees
    def turn_servo(self, angle):
        # calculate the duty cycle by linearly distributing the angles
        duty_cycle = (angle + 90) / 180 * (max_duty - min_duty) + min_duty
   
        # set the duty cycle
        self.pwm_servo.ChangeDutyCycle(duty_cycle)

        # wait for the servo to turn        
        time.sleep(0.30)

    # use the ultrasonic sensor to look how far the nearest object is
    def look(self):
        # trigger the sensor by setting the pin to high, and then low again
        GPIO.output(self.trig_pin, GPIO.HIGH); time.sleep(10e-6)
        GPIO.output(self.trig_pin, GPIO.LOW)

        # define start and end time
        pulse_start = time.time(); pulse_end = time.time()

        # start counting when the echo pin is low
        while GPIO.input(self.echo_pin) == GPIO.LOW:
            pulse_start = time.time()

        # stop counting when the echo pin is high again (signal has come back)
        while GPIO.input(self.echo_pin) == GPIO.HIGH:
            pulse_end = time.time()
        
        # Calculate the distance (speed of sound 34300 cm/s)
        return (pulse_end - pulse_start)*34300/2

# driving code starts here
my_robot = Robot()

# initial speed of the robot
my_robot.motor_speed(70,70)

# the main loop
while True:
    # look in each direction and check the distance to the nearest object
    my_robot.turn_servo(45); distance_left = my_robot.look()
    my_robot.turn_servo(0); distance_straight = my_robot.look()
    my_robot.turn_servo(-45); distance_right = my_robot.look()
    
    # show the three distances and a blank line
    print("Distance left     %4.1f cm" % distance_left)
    print("Distance straight %4.1f cm" % distance_straight)
    print("Distance right    %4.1f cm" % distance_right)
    print("") 

    # driving logic
    if(distance_left<line_of_sight and distance_straight < line_of_sight and
    distance_right<line_of_sight): my_robot.motor_speed(0,0)

    elif distance_left < line_of_sight:
        my_robot.motor_speed(100,0)
        time.sleep(turn_delay)
        my_robot.motor_speed(70,70)

    elif distance_straight < line_of_sight:
        if  distance_right > distance_left:
            my_robot.motor_speed(100,0)
            time.sleep(turn_delay)
            my_robot.motor_speed(70,70) 
            
        else:
            my_robot.motor_speed(0,100)
            time.sleep(turn_delay)
            my_robot.motor_speed(70,70)

    elif distance_right < line_of_sight:
        my_robot.motor_speed(0,100)
        time.sleep(turn_delay) 
        my_robot.motor_speed(70,70)


#GPIO.cleanup()          

