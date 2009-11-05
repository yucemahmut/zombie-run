// Copyright 2009 Peter Dolan, all rights reserved.

package net.peterd.zombierun.activity;

import com.google.android.apps.analytics.GoogleAnalyticsTracker;
import com.google.android.maps.MapActivity;

import android.os.Bundle;

public class BaseMapActivity extends MapActivity {

  protected GoogleAnalyticsTracker tracker;
  
  public void onCreate(Bundle bundle) {
    super.onCreate(bundle);
    tracker = GoogleAnalyticsTracker.getInstance();
    tracker.start("UA-214814-13", this);
    String pageView = this.getClass().getSimpleName();
    tracker.trackPageView("/action/" + pageView);
  }

  @Override
  protected boolean isRouteDisplayed() {
    return false;
  }

}
