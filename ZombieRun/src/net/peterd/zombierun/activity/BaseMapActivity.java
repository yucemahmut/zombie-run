// Copyright 2009 Peter Dolan, all rights reserved.

package net.peterd.zombierun.activity;

import com.google.android.apps.analytics.GoogleAnalyticsTracker;
import com.google.android.maps.MapActivity;

import android.util.Log;

public class BaseMapActivity extends MapActivity {

  protected GoogleAnalyticsTracker tracker;
  
  @Override
  public void onStart() {
    super.onStart();
    tracker = GoogleAnalyticsTracker.getInstance();
    tracker.start("UA-214814-13", this);
    String pageView = "/action/" + this.getClass().getSimpleName();
    Log.d("ZombieRun.BaseMapActivity", pageView);
    tracker.trackPageView(pageView);
  }
  
  @Override
  protected boolean isRouteDisplayed() {
    return false;
  }

}
