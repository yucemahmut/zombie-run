// Copyright 2009 Peter Dolan, all rights reserved.

package net.peterd.zombierun.activity;

import com.google.android.apps.analytics.GoogleAnalyticsTracker;
import com.google.android.maps.MapActivity;

public class BaseMapActivity extends MapActivity {

  protected GoogleAnalyticsTracker tracker;
  
  @Override
  public void onStart() {
    super.onStart();
    BaseActivity.logToAnalytics(this);
  }
  
  @Override
  protected boolean isRouteDisplayed() {
    return false;
  }
  
}
