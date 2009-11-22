package net.peterd.zombierun.overlay;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;

import com.google.android.maps.GeoPoint;
import com.google.android.maps.MapView;
import com.google.android.maps.MyLocationOverlay;
import com.google.android.maps.Overlay;

public class MotoCliqSafeMyLocationOverlay extends Overlay {

  private final MyLocationOverlay delegate;
  private final MapView map;
  private static final int dotHeight = 15;
  private static final int dotWidth = 15;

	public MotoCliqSafeMyLocationOverlay(Context context, MapView mapView) {
	  delegate = new MyLocationOverlay(context, mapView);
	  delegate.enableMyLocation();
		map = mapView;
	}

	public boolean enableMyLocation() {
	  return delegate.enableMyLocation();
	}

	public void disableMyLocation() {
	  delegate.disableMyLocation();
	}

	@Override
	public void draw(Canvas canvas, MapView mapView, boolean shadow) {
		try {
			super.draw(canvas, mapView, shadow);
		} catch (Exception e) {
      GeoPoint myLocation = delegate.getMyLocation();
      if (myLocation == null) {
        return;
      }

      GeoPoint mapCenter = map.getMapCenter();

			Rect mapRect = new Rect();
      map.getDrawingRect(mapRect);

      int mapHeight = mapRect.bottom - mapRect.top;
      int mapWidth = mapRect.right - mapRect.left;

      int lonSpanE6 = map.getLongitudeSpan();
      int mapLeftLon = mapCenter.getLongitudeE6() - (lonSpanE6 / 2);
      float screenLocationXPortion = ((float) (myLocation.getLongitudeE6() - mapLeftLon)) / lonSpanE6;

      int latSpanE6 = map.getLatitudeSpan();
      int mapBottomLat = mapCenter.getLatitudeE6() - (latSpanE6 / 2);
			float screenLocationYPortion = ((float) (myLocation.getLatitudeE6() - mapBottomLat)) / latSpanE6;

			RectF bounds = new RectF();
      bounds.bottom = mapRect.bottom - (mapHeight * screenLocationYPortion);
      bounds.top = bounds.bottom;
      bounds.bottom -= dotHeight / 2;
      bounds.top += dotHeight / 2;

      bounds.left = mapRect.left + (mapWidth * screenLocationXPortion);
      bounds.right = bounds.left;
      bounds.left -= dotWidth / 2;
      bounds.right += dotWidth / 2;

      Paint paint = new Paint();
      paint.setARGB(255, 0, 170, 240);
      canvas.drawOval(bounds, paint);
		}
	}
}
