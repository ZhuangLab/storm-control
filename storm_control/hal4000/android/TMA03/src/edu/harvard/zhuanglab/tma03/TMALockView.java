package edu.harvard.zhuanglab.tma03;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.util.AttributeSet;
import android.util.Log;
import android.view.View;

public class TMALockView extends View {

	private static final boolean DEBUG = true;
    private static final String TAG = "TMALockView";

    private int height = 0;
	private boolean live = false;
	private float offset = 0;
	private float offset_bar_width = 4;
	private float sum = 0;
    private float sum_bar_margin = 4;
	private int width = 0;
	
	private Rect mBounds;
	private Paint mPaintBackground;
	private Paint mPaintOffset;
	private Paint mPaintSum;

	public TMALockView(Context context, AttributeSet attrs) {
		super(context, attrs);
		
    	mPaintBackground = new Paint();
    	mPaintBackground.setColor(Color.parseColor("#000000"));

    	mPaintOffset = new Paint();
    	mPaintOffset.setColor(Color.parseColor("#BBBBBB"));
        mPaintOffset.setStyle(Paint.Style.STROKE);
        mPaintOffset.setStrokeWidth(4);
    	
    	mPaintSum = new Paint();
    	mPaintSum.setColor(Color.parseColor("#00FF00"));
	}
	
	/*
	 * Set the view to black when disconnected.
	 */
    public void disconnected(){
    	live = false;
    	invalidate();
    }

    /*
     * Update with new lock data.
     */
    public void newLockData(float new_offset, float new_sum){
    	if (DEBUG) Log.i(TAG, "newLockData," + new_offset + "," + new_sum);
    	offset = new_offset;
    	sum = new_sum;
    	live = true;
    	invalidate();
    }
    
    @Override
    protected void onDraw(Canvas canvas) {
    	super.onDraw(canvas);

    	canvas.drawRect(mBounds, mPaintBackground);

    	if (live){
    		canvas.drawRect(1, sum_bar_margin, sum * width, height - sum_bar_margin, mPaintSum);
    		canvas.drawRect(offset * width - offset_bar_width, 2, offset * width + offset_bar_width, height - 2, mPaintOffset);
    	}
    }

    @Override
    protected void onSizeChanged(int new_width, int new_height, int xOld, int yOld)
    {
    	super.onSizeChanged(new_width, new_height, xOld, yOld);
    	
    	mBounds = new Rect(0, 0, new_width, new_height);
    	
    	width = new_width;
    	height = new_height;
    	
    	offset_bar_width = new_width/40;
    	sum_bar_margin = new_height/4;
    }    
}
