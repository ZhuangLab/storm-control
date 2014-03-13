/*
 * An Android app to control HAL.
 * 
 * Much of the code comes from here:
 *   https://github.com/luugiathuy/Remote-Bluetooth-Android
 *   
 * Hazen 02/14
 */

package edu.harvard.zhuanglab.tma03;

import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.View.OnTouchListener;
import android.widget.Button;
import android.widget.RelativeLayout;
import android.widget.Toast;

public class MainActivity extends Activity {

	private static final boolean DEBUG = true;
	
    // Message types sent from the BluetoothIO Handler
	public static final int MESSAGE_CONNECT = 1;
	public static final int MESSAGE_DISCONNECT = 2;
	public static final int MESSAGE_IMAGE = 3;
    public static final int MESSAGE_READ = 4;
    public static final int MESSAGE_WRITE = 5;
    public static final int MESSAGE_TOAST = 6;
	
	// Intent request codes
    private static final int REQUEST_CONNECT_DEVICE = 1;
    private static final int REQUEST_ENABLE_BT = 2;

    private static final String TAG = "MainActivity";
    public static final String TOAST = "toast";
    
    // Local Bluetooth adapter
    private BluetoothAdapter mBluetoothAdapter = null;
    private BluetoothIO mBluetoothIO = null;
    
    private Button mDownButton = null;
    private Button mRecordButton = null;
    private Button mUpButton = null;
    private RelativeLayout mRelativeLayout = null;
    private TMACameraView mTMACameraView = null;
    private TMALockView mTMALockView = null;

    private void configureButtons(boolean connected){
    	if (connected){
        	mDownButton.setEnabled(true);
        	mDownButton.setTextColor(Color.parseColor("#FFFFFF"));
        	mRecordButton.setEnabled(true);
    		mRecordButton.setTextColor(Color.parseColor("#00FF00"));
        	mUpButton.setEnabled(true);
        	mUpButton.setTextColor(Color.parseColor("#FFFFFF"));    		
    	}
    	else{
        	mDownButton.setEnabled(false);
        	mDownButton.setTextColor(Color.parseColor("#404040"));
        	mRecordButton.setEnabled(false);
    		mRecordButton.setTextColor(Color.parseColor("#404040"));
        	mUpButton.setEnabled(false);
        	mUpButton.setTextColor(Color.parseColor("#404040"));    		
    	}
    }
    
    private final Handler mHandler = new Handler() {
        @Override
        public void handleMessage(Message msg) {
            switch (msg.what) {
            case MESSAGE_CONNECT:
            	mBluetoothIO.sendNewImage();
            	configureButtons(true);
            	break;
            case MESSAGE_DISCONNECT:
            	mTMACameraView.disconnected();
            	mTMALockView.disconnected();
            	configureButtons(false);
            	break;
            case MESSAGE_IMAGE:
            	byte[] imgArray = (byte [])msg.obj;
            	mTMACameraView.newImage(imgArray);
            	mBluetoothIO.sendNewImage();
            	break;
            case MESSAGE_READ:
            	String[] message = (String [])msg.obj;
            	if (message[0].equals("startfilm")){
            		mRecordButton.setTextColor(Color.parseColor("#FF0000"));
            	}
            	else if (message[0].equals("stopfilm")){
            		mRecordButton.setTextColor(Color.parseColor("#00FF00"));            		
            	}
            	else if (message[0].equals("gainchange")){
            		mTMACameraView.setMultiplier(Float.parseFloat(message[1]));
            	}
            	else if (message[0].equals("showgain")){
            		mTMACameraView.setShowGain(Integer.parseInt(message[1]));
            	}
            	else if (message[0].equals("lockupdate")){
            		mTMALockView.newLockData(Float.parseFloat(message[1]), Float.parseFloat(message[2]));
            	}
            	mBluetoothIO.sendAcknowledgement();
            	break;
            case MESSAGE_TOAST:
                Toast.makeText(getApplicationContext(), msg.getData().getString(TOAST), Toast.LENGTH_SHORT).show();
                break;
            }
        }
    };
    
	OnClickListener mTMALockViewOnClickListener = new OnClickListener() {
		@Override
		public void onClick(View v) {
			sendLockClick();
		}
	};
	
	public void onActivityResult(int requestCode, int resultCode, Intent data) {
        switch (requestCode) {
        case REQUEST_CONNECT_DEVICE:
            // When DeviceListActivity returns with a device to connect
            if (resultCode == Activity.RESULT_OK) {
                // Get the device MAC address
                String address = data.getExtras()
                                     .getString(DeviceListActivity.EXTRA_DEVICE_ADDRESS);
                // Get the BLuetoothDevice object
                BluetoothDevice device = mBluetoothAdapter.getRemoteDevice(address);
                // Attempt to connect to the device
                mBluetoothIO.connect(device);
            }
            break;
        case REQUEST_ENABLE_BT:
            // When the request to enable Bluetooth returns
            if (resultCode == Activity.RESULT_OK) {
                // Bluetooth is now enabled, so set up a chat session
                Toast.makeText(this, "Bluetooth Enabled", Toast.LENGTH_SHORT).show();
            } else {
                // User did not enable Bluetooth or an error occured
                Toast.makeText(this, "Bluetooth Not Enabled", Toast.LENGTH_SHORT).show();
            }
        }
    }
	
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
		mTMACameraView = (TMACameraView) findViewById(R.id.cameraView);

		mTMALockView = (TMALockView) findViewById(R.id.lockView);
		mTMALockView.setOnClickListener(mTMALockViewOnClickListener);
        
        mDownButton = (Button) findViewById(R.id.downButton);
        mRecordButton = (Button) findViewById(R.id.recordButton);
        mUpButton = (Button) findViewById(R.id.upButton);
        configureButtons(false);
        
        mRelativeLayout = (RelativeLayout) findViewById(R.id.relativeLayout1);
        mRelativeLayout.setOnTouchListener(relativeLayout1OnTouchListener);
        
        mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
                
        // If the adapter is null, then Bluetooth is not supported
        if (mBluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth is not available", Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.main, menu);
        return true;
    }
    
	@Override
	protected void onDestroy() {
		super.onDestroy();

		if (mBluetoothIO != null)
			mBluetoothIO.stop();
	}
	
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle presses on the action bar items
        switch (item.getItemId()) {
            case R.id.action_scan:
                // Launch the DeviceListActivity to see devices and do scan
            	Intent serverIntent = new Intent(this, DeviceListActivity.class);
            	startActivityForResult(serverIntent, REQUEST_CONNECT_DEVICE);
            	return true;
            case R.id.action_disconnect:
            	if (mBluetoothIO != null)
            		mBluetoothIO.stop();
            	return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }
    
	@Override
	protected void onStart() {
		super.onStart();        
		// If BT is not on, request that it be enabled.
        // setupCommand() will then be called during onActivityResult
		if (!mBluetoothAdapter.isEnabled()) {
			Intent enableIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
			startActivityForResult(enableIntent, REQUEST_ENABLE_BT);
		}
		else{
            mBluetoothIO = new BluetoothIO(this, mHandler);
		}
		
        // Remove icon from action bar
		getActionBar().setDisplayShowHomeEnabled(false);
	}
	
	@Override
	protected void onStop() {
	    super.onStop();
	    
    	if (mBluetoothIO != null)
    		mBluetoothIO.stop();
	}

	OnTouchListener relativeLayout1OnTouchListener = new OnTouchListener() {
		@Override
		public boolean onTouch(View v, MotionEvent event) {
			double eventX = ((double) event.getX()) / ((double)mTMACameraView.width) - 0.5;
			double eventY = ((double) event.getY()) / ((double)mTMACameraView.height) - 0.5;

			switch(event.getAction()){
			case MotionEvent.ACTION_DOWN:
				sendActionDown(eventX, eventY);
				break;

			case MotionEvent.ACTION_MOVE:
				sendActionMove(eventX, eventY);
				break;
				
			case MotionEvent.ACTION_UP:
				sendActionUp(eventX, eventY);
				break;
			}
			return true;

		}
	};

	public void sendActionDown(double x, double y){
        if (DEBUG) Log.i(TAG, "press," + x + "," + y);		
		mBluetoothIO.sendMessage("actiondown," + String.format("%.3f", x) + "," + String.format("%.3f", y));
	}

	public void sendActionMove(double x, double y){
        if (DEBUG) Log.i(TAG, "motion," + x + "," + y);
		mBluetoothIO.sendMessage("actionmove," + String.format("%.3f", x) + "," + String.format("%.3f", y));
		//mBluetoothIO.sendMessage(String.format("actionmove,%1,.3f,%2,.3f", x, y));
    }

	public void sendActionUp(double x, double y){
        if (DEBUG) Log.i(TAG, "release," + x + "," + y);
        mBluetoothIO.sendMessage("actionup," + String.format("%.3f", x) + "," + String.format("%.3f", y));
		//mBluetoothIO.sendMessage(String.format("actionup,%1,.3f,%2,.3f", x, y));
	}

	public void sendFocusDown(View view){
        if (DEBUG) Log.i(TAG, "focusdown");
		mBluetoothIO.sendMessage("focusdown");
    }
	
	public void sendFocusUp(View view){
        if (DEBUG) Log.i(TAG, "focusup");
		mBluetoothIO.sendMessage("focusup");
    }

	public void sendLockClick(){
		if (DEBUG) Log.i(TAG, "lockclick");
		mBluetoothIO.sendMessage("lockclick");
	}
	
	public void sendRecord(View view){
        if (DEBUG) Log.i(TAG, "sendRecord");
		mBluetoothIO.sendMessage("record");
    }
}
