package edu.harvard.zhuanglab.tma03;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.util.AttributeSet;
import android.util.Log;
import android.widget.ImageView;

public class TMACameraView extends ImageView {
	
	private static final boolean DEBUG = true;
    private static final String TAG = "TMACameraView";
	
	private float center_x = 128;
	private float center_y = 128;
	private boolean live = false;
	private float multiplier = 1;
	private boolean show_gain = true;
	
	private Bitmap mBitmap;
	private Rect mBitmapBounds;
	private Paint mBitmapPaint;
	private Rect mBounds;
	private Rect mImageBounds;
	private Paint mPaintBackground;
	private Paint mPaintLine;
	
	public int width;
	public int height;
	
	public TMACameraView(Context context, AttributeSet attrs) {
		super(context, attrs);
		
		mBitmapPaint = new Paint();
		
    	mPaintBackground = new Paint();
    	mPaintBackground.setColor(Color.parseColor("#000000"));

    	mPaintLine = new Paint();
        mPaintLine.setColor(Color.parseColor("#FFFFFF"));
        mPaintLine.setStyle(Paint.Style.STROKE);
        mPaintLine.setStrokeWidth(2);
	}

	/*
	 * Set the image back to black when the app closes.
	 */
    public void disconnected(){
    	live = false;
    	invalidate();
    }
    
    /*
     * Rescale and draw the image. The images that are sent are always
     * square so that we don't have to worry about the aspect ratio on
     * this end.
     */
    public void newImage(byte[] imgArray){
    	mBitmap = BitmapFactory.decodeByteArray(imgArray, 0, imgArray.length, null);
    	mBitmapBounds = new Rect(0, 0, mBitmap.getWidth(), mBitmap.getHeight());
    	if (DEBUG) Log.i(TAG, "newImage," + mBitmap.getWidth() + "," + mBitmap.getHeight());
    	live = true;
    	invalidate();
    }
    
    @Override
    protected void onDraw(Canvas canvas) {
    	super.onDraw(canvas);

    	canvas.drawRect(mBounds, mPaintBackground);

    	if (live){
        	canvas.drawBitmap(mBitmap, mBitmapBounds, mImageBounds, mBitmapPaint);
        	if (show_gain){
        		canvas.drawCircle(center_x, center_y, 20 * multiplier, mPaintLine);
        	}
    	}
    }
    
    @Override
    protected void onSizeChanged(int new_width, int new_height, int xOld, int yOld)
    {
    	super.onSizeChanged(new_width, new_height, xOld, yOld);

    	width = new_width;
    	height = new_height;
    	
    	mBounds = new Rect(0, 0, new_width, new_height);

    	if (new_width > new_height){
    		int dx = (new_width - new_height)/2;
    		mImageBounds = new Rect(dx, 0, dx + new_height, new_height);
    	}
    	else {
    		int dy = (new_height - new_width)/2;
    		mImageBounds = new Rect(0, dy, new_width, dy + new_width);
    	}

    	center_x = new_width/2;
    	center_y = new_height/2;

    	if (DEBUG) Log.i(TAG, "onSizeChanged," + width + "," + height);
    }

    public void setMultiplier(float new_multiplier){
    	multiplier = new_multiplier;
    }
    
    public void setShowGain(int new_show_gain){
    	if (new_show_gain != 0){
    		show_gain = true;
    	}
    	else{
    		show_gain = false;
    	}
    }
}
