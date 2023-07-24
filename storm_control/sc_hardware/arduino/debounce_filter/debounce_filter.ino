// Debounce filter
// v0.4
// Jeffrey Moffitt
// September 2022
// Children's Hospital Boston 2022

// Headers
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

// Display definitions
Adafruit_SH1107 display = Adafruit_SH1107(64, 128, &Wire);

float const _VERSION = 0.4; // Version ID
int val = 0;

int loop_time = 0; // Loop timer
int last_time = 0; // Time from last loop
int this_time = 0; // Time from this loop
int const buffer_length = 10; // Number of measurements in the buffer
int const pause_us_length = 5; // Number of us to pause between measurement
int buffer_counter = 0;
bool measurement_buffer[buffer_length]; 
float av_true = 0; // The fraction of the buffer that is true
float const threshold_true = 0.8;
float const threshold_false = 0.2;

// the setup function runs once when you press reset or power the board
void setup() {
  // Initialize the digital input and output lines
  pinMode(12, INPUT);
  pinMode(13, OUTPUT); //LED
  pinMode(11, OUTPUT);

  // Create the display
  display.begin(0x3C, true); // Address 0x3C default

  // Display the splash screen
  display.display();
  delay(1000);

  // Clear the display
  display.clearDisplay();
  display.display();
  display.setRotation(1);

  // Configure the display for error reports
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0,0);

  // Print properties
  display.println("DEBOUNCE " + String(_VERSION));
  display.println("");
  display.println("Debounce pin: " + String(12));
  display.println("Cycle time: " + String(pause_us_length) + "us");
  display.println("Buffer length: " + String(buffer_length));
  display.println("Fraction high: " + String(threshold_true));
  display.println("Fraction low: " + String(threshold_false));
  display.display();
}


// the loop function runs over and over again forever
void loop() {
  //Read the value
  val = digitalRead(12);
  
  //Record in buffer
  measurement_buffer[buffer_counter % buffer_length] = val;

  // Handle the buffer full situation
  if (buffer_counter == (buffer_length - 1)) {
    //Reset buffer counter
    buffer_counter = 0;

    // Compute the average
    av_true = 0.0; 
    for(int i=0; i<buffer_length; i++){
      if (measurement_buffer[i]) {
        av_true = av_true + 1;
      }
    }
    av_true = av_true/buffer_length;
    if (av_true >= threshold_true){
      digitalWrite(13, 1);
      digitalWrite(11, 1);
    }
    if (av_true <= threshold_false){
      digitalWrite(13, 0);
      digitalWrite(11, 0);
    }
  }

  delayMicroseconds(pause_us_length);
  buffer_counter = buffer_counter + 1;

}
